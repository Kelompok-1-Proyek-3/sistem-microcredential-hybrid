# Part of IMPC Microcredential Platform. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrEmployee(models.Model):
    """Extends hr.employee with learning progress and profile notes relations."""
    _inherit = 'hr.employee'

    learning_progress_ids = fields.One2many(
        'hr.learning.progress',
        'employee_id',
        string='Learning Progress',
    )
    learning_note_ids = fields.One2many(
        'hr.learning.profile.note',
        'employee_id',
        string='Learning Notes',
    )
    skill_mapping_log_ids = fields.One2many(
        'hr.skill.mapping.log',
        'employee_id',
        string='Skill Mapping Log',
    )

    # === Computed Fields ===
    active_course_count = fields.Integer(
        string='Active Courses',
        compute='_compute_learning_stats',
    )
    completed_course_count = fields.Integer(
        string='Completed Courses',
        compute='_compute_learning_stats',
    )
    at_risk_course_count = fields.Integer(
        string='At Risk Courses',
        compute='_compute_learning_stats',
    )

    @api.depends('learning_progress_ids', 'learning_progress_ids.status')
    def _compute_learning_stats(self):
        for employee in self:
            progress = employee.learning_progress_ids
            employee.active_course_count = len(
                progress.filtered(lambda r: r.status == 'IN_PROGRESS')
            )
            employee.completed_course_count = len(
                progress.filtered(lambda r: r.status == 'COMPLETED')
            )
            employee.at_risk_course_count = len(
                progress.filtered(lambda r: r.status == 'AT_RISK')
            )
