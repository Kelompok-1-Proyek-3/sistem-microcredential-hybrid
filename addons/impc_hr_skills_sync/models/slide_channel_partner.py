from odoo import api, fields, models

class SlideChannelPartner(models.Model):
    _inherit = 'slide.channel.partner'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(SlideChannelPartner, self).create(vals_list)
        records._sync_lms_enrollment()
        return records

    def write(self, vals):
        res = super(SlideChannelPartner, self).write(vals)
        if 'completion' in vals or 'member_status' in vals:
            self._sync_lms_enrollment()
        return res

    def _sync_lms_enrollment(self):
        for record in self:
            learner = self.env['lms.learner'].search([('partner_id', '=', record.partner_id.id)], limit=1)
            if not learner:
                learner = self.env['lms.learner'].create({
                    'partner_id': record.partner_id.id,
                    'learner_type': 'internal' if self.env['hr.employee'].search([('user_id.partner_id', '=', record.partner_id.id)]) else 'b2c'
                })
            
            enrollment = self.env['lms.enrollment'].search([
                ('learner_id', '=', learner.id),
                ('channel_id', '=', record.channel_id.id)
            ], limit=1)
            
            status_map = {
                'joined': 'active',
                'ongoing': 'active',
                'completed': 'completed'
            }
            status = status_map.get(record.member_status, 'pending')
            if record.completion == 100:
                status = 'completed'
                
            if not enrollment:
                enrollment = self.env['lms.enrollment'].create({
                    'learner_id': learner.id,
                    'channel_id': record.channel_id.id,
                    'status': status,
                    'progress_pct': record.completion or 0.0
                })
            else:
                enrollment.write({'status': status, 'progress_pct': record.completion or 0.0})
            
            if record.completion == 100:
                existing_cert = self.env['impc.certificate'].search([
                    ('learner_id', '=', learner.id),
                    ('channel_id', '=', record.channel_id.id)
                ], limit=1)
                
                if not existing_cert:
                    self.env['impc.certificate'].create({
                        'learner_id': learner.id,
                        'channel_id': record.channel_id.id,
                        'enrollment_id': enrollment.id,
                        'issued_date': fields.Date.today()
                    })
