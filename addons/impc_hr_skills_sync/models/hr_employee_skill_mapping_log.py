from odoo import fields, models


class HrEmployeeSkillMappingLog(models.Model):
    _name = 'hr.employee.skill_mapping_log'
    _description = 'Employee Skill Mapping Log'
    _order = 'change_date desc, id desc'

    employee_id = fields.Many2one('hr.employee', required=True, index=True, ondelete='cascade')
    skill_id = fields.Many2one('hr.skill', required=True, index=True, ondelete='restrict')
    certificate_id = fields.Many2one('impc.certificate', required=True, index=True, ondelete='restrict')
    skill_level_before_id = fields.Many2one('hr.skill.level', ondelete='set null')
    skill_level_after_id = fields.Many2one('hr.skill.level', required=True, ondelete='restrict')
    change_date = fields.Date(required=True)
