# Part of IMPC Microcredential Platform. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrCourseSkillMapping(models.Model):
    """Defines which skills are earned by completing a specific course.
    
    This mapping is used to automatically update employee skills
    when a certificate is issued by the Website Group.
    
    Example: Course "Python Advanced" → Skills: "Python (Advanced)", "OOP (Intermediate)"
    """
    _name = 'hr.course.skill.mapping'
    _description = 'Course to Skill Mapping'
    _order = 'course_name, skill_id'

    course_id = fields.Integer(
        string='Course ID (eLearning)',
        required=True,
        help='Foreign key reference to elearning.course in Website module',
        index=True,
    )
    course_name = fields.Char(
        string='Course Name',
        required=True,
    )
    skill_id = fields.Many2one(
        'hr.skill',
        string='Skill',
        required=True,
        ondelete='cascade',
    )
    skill_level = fields.Selection(
        [
            ('BEGINNER', 'Beginner'),
            ('INTERMEDIATE', 'Intermediate'),
            ('ADVANCED', 'Advanced'),
            ('EXPERT', 'Expert'),
        ],
        string='Skill Level',
        required=True,
        default='BEGINNER',
    )
