from odoo import api, fields, models


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    def _sync_impc_attendance(self):
        """Sync registration state to IMPC attendance records."""
        Attendance = self.env['impc.session.attendance']
        SlidePartner = self.env['slide.channel.partner']
        for registration in self:
            partner = registration.partner_id
            event = registration.event_id
            course = SlidePartner.search([
                ('partner_id', '=', partner.id),
                ('channel_id.event_id', '=', event.id),
                ('member_status', 'in', ['joined', 'ongoing']),
            ], limit=1)
            if not course:
                continue
            enrollment = course
            attendance = Attendance.search([
                ('channel_partner_id', '=', enrollment.id),
                ('event_id', '=', event.id),
            ], limit=1)
            if not attendance:
                attendance = Attendance.create({
                    'channel_partner_id': enrollment.id,
                    'event_id': event.id,
                    'registration_id': registration.id,
                    'attendance_status': 'pending',
                })
            vals = {
                'registration_id': registration.id,
                'sync_date': fields.Datetime.now(),
            }
            if registration.state == 'done':
                vals['attendance_status'] = 'hadir'
            elif registration.state in ('cancel', 'declined'):
                vals['attendance_status'] = 'tidak_hadir'
            attendance.write(vals)
            if not enrollment.session_attendance_id:
                enrollment.session_attendance_id = attendance.id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_impc_attendance()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            self._sync_impc_attendance()
        return res
