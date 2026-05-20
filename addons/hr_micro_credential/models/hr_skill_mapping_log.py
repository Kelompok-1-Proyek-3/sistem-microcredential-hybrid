# Part of IMPC Microcredential Platform. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrSkillMappingLog(models.Model):
    """Audit log for skill changes triggered by certificate issuance.
    
    Tracks when and why an employee's skill was added or updated,
    including the old and new skill level for versioning support.
    """
    _name = 'hr.skill.mapping.log'
    _description = 'Employee Skill Mapping Audit Log'
    _order = 'change_date desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
    )
    skill_id = fields.Many2one(
        'hr.skill',
        string='Skill',
        required=True,
        ondelete='cascade',
    )
    certificate_id = fields.Integer(
        string='Certificate ID (eLearning)',
        help='Foreign key reference to elearning.certificate in Website module',
    )
    course_name = fields.Char(
        string='Course Name',
    )
    skill_level_before = fields.Selection(
        [
            ('NONE', 'None'),
            ('BEGINNER', 'Beginner'),
            ('INTERMEDIATE', 'Intermediate'),
            ('ADVANCED', 'Advanced'),
            ('EXPERT', 'Expert'),
        ],
        string='Level Before',
    )
    skill_level_after = fields.Selection(
        [
            ('BEGINNER', 'Beginner'),
            ('INTERMEDIATE', 'Intermediate'),
            ('ADVANCED', 'Advanced'),
            ('EXPERT', 'Expert'),
        ],
        string='Level After',
        required=True,
    )
    change_date = fields.Date(
        string='Change Date',
        required=True,
        default=fields.Date.today,
    )
