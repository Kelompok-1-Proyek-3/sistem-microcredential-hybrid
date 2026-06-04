from odoo import fields, models


class LmsLearner(models.Model):
    _name = 'lms.learner'
    _description = 'LMS Learner'
    _order = 'create_date desc, id desc'

    partner_id = fields.Many2one('res.partner', required=True, index=True, ondelete='cascade')
    learner_type = fields.Selection(
        selection=[
            ('b2c', 'B2C'),
            ('b2b', 'B2B'),
            ('internal', 'Internal'),
        ],
        required=True,
        default='b2c',
    )
    company_id = fields.Many2one('res.partner')
    enrollment_ids = fields.One2many('lms.enrollment', 'learner_id')
    certificate_ids = fields.One2many('impc.certificate', 'learner_id')
    competency_ids = fields.One2many('lms.learner.competency', 'learner_id')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('partner_unique', 'unique(partner_id)', 'Learner already exists for this partner.'),
    ]
