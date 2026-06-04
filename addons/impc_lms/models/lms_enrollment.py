from odoo import fields, models


class LmsEnrollment(models.Model):
    _name = 'lms.enrollment'
    _description = 'LMS Enrollment'
    _order = 'enrollment_date desc, id desc'

    learner_id = fields.Many2one('lms.learner', required=True, index=True, ondelete='cascade')
    channel_id = fields.Many2one('slide.channel', required=True, index=True, ondelete='restrict')
    enrollment_type = fields.Selection(
        selection=[
            ('b2c_payment', 'B2C Payment'),
            ('b2b_redeem', 'B2B Redeem'),
            ('internal_free', 'Internal Free'),
        ],
        required=True,
        default='b2c_payment',
    )
    enrollment_date = fields.Date(default=fields.Date.today, required=True)
    status = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('expired', 'Expired'),
        ],
        default='pending',
        required=True,
    )
    progress_pct = fields.Float(default=0.0)
    last_activity_date = fields.Datetime()
    requires_offline = fields.Boolean(default=False)
    attendance_status = fields.Selection(
        selection=[
            ('not_required', 'Not Required'),
            ('pending', 'Pending'),
            ('present', 'Present'),
            ('absent', 'Absent'),
        ],
        default='not_required',
        required=True,
    )
    eticket_ids = fields.One2many('lms.eticket', 'enrollment_id')
    exam_unlocked = fields.Boolean(default=False)
