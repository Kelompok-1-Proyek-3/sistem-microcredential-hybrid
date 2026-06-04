from odoo import fields, models


class LmsLearnerCompetency(models.Model):
    _name = 'lms.learner.competency'
    _description = 'LMS Learner Competency'
    _order = 'acquired_date desc, id desc'

    learner_id = fields.Many2one('lms.learner', required=True, index=True, ondelete='cascade')
    channel_id = fields.Many2one('slide.channel', ondelete='set null')
    certificate_id = fields.Many2one('impc.certificate', ondelete='set null')
    competency_name = fields.Char(required=True)
    competency_level = fields.Char()
    acquired_date = fields.Date(default=fields.Date.today, required=True)
