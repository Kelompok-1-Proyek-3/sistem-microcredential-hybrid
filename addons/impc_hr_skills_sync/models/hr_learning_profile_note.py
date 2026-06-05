from odoo import api, fields, models

class HrLearningProfileNote(models.Model):
    _name = 'hr.learning.profile.note'
    _description = 'Employee Learning Profile Note'
    _order = 'note_date desc, id desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade', index=True)
    note_date = fields.Date(string='Date', required=True, default=fields.Date.today)
    note_text = fields.Text(string='Note', required=True)
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.uid, readonly=True)
