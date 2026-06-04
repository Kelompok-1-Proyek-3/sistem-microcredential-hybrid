from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ImpcCourseSkillMapping(models.Model):
    _name = 'impc.course_skill_mapping'
    _description = 'IMPC Course Skill Mapping'
    _order = 'channel_id, skill_type_id, skill_id'

    channel_id = fields.Many2one('slide.channel', required=True, index=True, ondelete='cascade')
    skill_id = fields.Many2one('hr.skill', required=True, index=True, ondelete='restrict')
    skill_level_id = fields.Many2one('hr.skill.level', required=True, ondelete='restrict')
    skill_type_id = fields.Many2one('hr.skill.type', required=True, ondelete='restrict')

    @api.constrains('skill_id', 'skill_type_id')
    def _check_skill_type(self):
        for record in self:
            if record.skill_id and record.skill_id.skill_type_id != record.skill_type_id:
                raise ValidationError(_(
                    'The skill %s is not part of skill type %s.',
                    record.skill_id.name,
                    record.skill_type_id.name,
                ))

    @api.constrains('skill_level_id', 'skill_type_id')
    def _check_skill_level(self):
        for record in self:
            if record.skill_level_id and record.skill_level_id.skill_type_id != record.skill_type_id:
                raise ValidationError(_(
                    'The skill level %s is not valid for skill type %s.',
                    record.skill_level_id.name,
                    record.skill_type_id.name,
                ))
