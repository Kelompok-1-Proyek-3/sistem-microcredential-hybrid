from odoo import api, fields, models

class SlideChannelPartner(models.Model):
    _inherit = 'slide.channel.partner'

    def write(self, vals):
        res = super(SlideChannelPartner, self).write(vals)
        if 'completion' in vals:
            self._check_and_generate_certificates()
        return res

    def _check_and_generate_certificates(self):
        for record in self:
            if record.completion == 100:
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
                
                if not enrollment:
                    enrollment = self.env['lms.enrollment'].create({
                        'learner_id': learner.id,
                        'channel_id': record.channel_id.id,
                        'status': 'completed',
                        'progress_pct': 100.0
                    })
                else:
                    enrollment.write({'status': 'completed', 'progress_pct': 100.0})
                
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
