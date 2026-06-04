from odoo import api, fields, models


class LmsOfflineSession(models.Model):
    _name = 'lms.offline_session'
    _description = 'LMS Offline Session'
    _order = 'session_date desc, id desc'

    channel_id = fields.Many2one('slide.channel', required=True, index=True, ondelete='restrict')
    session_date = fields.Date(required=True)
    start_time = fields.Float()
    end_time = fields.Float()
    location = fields.Char()
    capacity = fields.Integer()
    is_active = fields.Boolean(default=True)
    eticket_ids = fields.One2many('lms.eticket', 'session_id')
    enrolled_count = fields.Integer(compute='_compute_enrolled_count')

    @api.depends('eticket_ids')
    def _compute_enrolled_count(self):
        for session in self:
            session.enrolled_count = len(session.eticket_ids)
