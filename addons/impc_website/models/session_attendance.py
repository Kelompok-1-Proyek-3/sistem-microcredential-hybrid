from odoo import api, fields, models


class ImpcSessionAttendance(models.Model):
    _name = 'impc.session.attendance'
    _description = 'IMPC Session Attendance (Hybrid Learning)'
    _order = 'sync_date desc'

    # === Links ===
    channel_partner_id = fields.Many2one(
        'slide.channel.partner',
        string='Enrollment',
        required=True,
        ondelete='cascade',
    )
    partner_id = fields.Many2one(
        related='channel_partner_id.partner_id',
        string='Student',
        store=True,
    )
    channel_id = fields.Many2one(
        related='channel_partner_id.channel_id',
        string='Course',
        store=True,
    )
    event_id = fields.Many2one(
        'event.event',
        string='Event Session',
        required=True,
    )
    registration_id = fields.Many2one(
        'event.registration',
        string='Event Registration',
    )

    # === Attendance Status ===
    attendance_status = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('hadir', 'Hadir (Attended)'),
            ('tidak_hadir', 'Tidak Hadir (Absent)'),
        ],
        string='Attendance Status',
        default='pending',
        required=True,
    )

    # === Sync Metadata ===
    sync_date = fields.Datetime(
        string='Last Sync',
        readonly=True,
    )

    # === Constraints (Odoo 19 syntax) ===
    _enrollment_event_unique = models.Constraint(
        'UNIQUE(channel_partner_id, event_id)',
        'Only one attendance record per enrollment per event.',
    )

    def _compute_display_name(self):
        for record in self:
            partner_name = record.partner_id.name or 'Unknown'
            event_name = record.event_id.name or 'Unknown'
            record.display_name = f'{partner_name} - {event_name}'

    @api.model
    def cron_sync_attendance(self):
        """Scheduled action: sync attendance from event.registration.

        Reads event.registration records and updates attendance status:
        - state='done' (Attended in Odoo 19) → hadir
        - Event ended + not attended → tidak_hadir
        """
        # Find all hybrid/offline courses with linked events
        hybrid_courses = self.env['slide.channel'].sudo().search([
            ('learning_mode', 'in', ['hybrid', 'offline']),
            ('event_id', '!=', False),
        ])

        for course in hybrid_courses:
            event = course.event_id
            enrollments = self.env['slide.channel.partner'].sudo().search([
                ('channel_id', '=', course.id),
                ('member_status', 'in', ['joined', 'ongoing']),
            ])

            for enrollment in enrollments:
                # Find or create attendance record
                attendance = self.sudo().search([
                    ('channel_partner_id', '=', enrollment.id),
                    ('event_id', '=', event.id),
                ], limit=1)

                if not attendance:
                    attendance = self.sudo().create({
                        'channel_partner_id': enrollment.id,
                        'event_id': event.id,
                        'attendance_status': 'pending',
                    })

                # Look up event registration
                registration = self.env['event.registration'].sudo().search([
                    ('event_id', '=', event.id),
                    ('partner_id', '=', enrollment.partner_id.id),
                ], limit=1)

                if registration:
                    attendance.registration_id = registration.id
                    if registration.state == 'done':
                        attendance.write({
                            'attendance_status': 'hadir',
                            'sync_date': fields.Datetime.now(),
                        })
                    elif (
                        event.date_end
                        and event.date_end < fields.Datetime.now()
                        and registration.state != 'done'
                    ):
                        attendance.write({
                            'attendance_status': 'tidak_hadir',
                            'sync_date': fields.Datetime.now(),
                        })
                elif event.date_end and event.date_end < fields.Datetime.now():
                    # No registration and event ended
                    attendance.write({
                        'attendance_status': 'tidak_hadir',
                        'sync_date': fields.Datetime.now(),
                    })

                # Link attendance to enrollment
                if not enrollment.session_attendance_id:
                    enrollment.session_attendance_id = attendance.id

        return True
