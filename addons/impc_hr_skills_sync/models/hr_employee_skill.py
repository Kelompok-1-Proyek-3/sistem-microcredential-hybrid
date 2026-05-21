import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrEmployeeSkill(models.Model):
    _inherit = 'hr.employee.skill'

    @api.model
    def _sync_skills_from_certificates(self):
        certificates = self.env['impc.certificate'].search([
            ('is_revoked', '=', False),
            ('skill_synced', '=', False),
        ])
        if not certificates:
            return

        employee_model = self.env['hr.employee']
        mapping_model = self.env['impc.course_skill_mapping']
        log_model = self.env['hr.employee.skill_mapping_log']

        for cert in certificates:
            if not cert.partner_id or not cert.channel_id:
                _logger.warning(
                    'Certificate %s missing partner or channel. Marking as synced.',
                    cert.id,
                )
                cert.skill_synced = True
                continue

            employee = employee_model.search([
                ('user_id.partner_id', '=', cert.partner_id.id),
            ], limit=1)
            if not employee:
                employee_missing_user = employee_model.search([
                    ('user_id', '=', False),
                    ('work_contact_id', '=', cert.partner_id.id),
                ], limit=1)
                if employee_missing_user:
                    _logger.warning(
                        'Employee %s missing user_id for certificate %s. Skipping skill sync.',
                        employee_missing_user.id,
                        cert.id,
                    )
                    continue

                cert.skill_synced = True
                continue

            mappings = mapping_model.search([
                ('channel_id', '=', cert.channel_id.id),
            ])
            if not mappings:
                _logger.warning(
                    'No course skill mapping for channel %s on certificate %s. Marking as synced.',
                    cert.channel_id.id,
                    cert.id,
                )
                cert.skill_synced = True
                continue

            for mapping in mappings:
                if not mapping.skill_id or not mapping.skill_level_id or not mapping.skill_type_id:
                    _logger.warning(
                        'Skipping course skill mapping %s due to missing fields.',
                        mapping.id,
                    )
                    continue

                existing_skill = self.search([
                    ('employee_id', '=', employee.id),
                    ('skill_id', '=', mapping.skill_id.id),
                    ('skill_type_id', '=', mapping.skill_type_id.id),
                ], limit=1)
                level_before = existing_skill.skill_level_id if existing_skill else False

                if existing_skill:
                    if not self._is_level_upgrade(level_before, mapping.skill_level_id):
                        continue
                    existing_skill.write({'skill_level_id': mapping.skill_level_id.id})
                else:
                    self.create({
                        'employee_id': employee.id,
                        'skill_id': mapping.skill_id.id,
                        'skill_level_id': mapping.skill_level_id.id,
                        'skill_type_id': mapping.skill_type_id.id,
                    })

                log_model.create({
                    'employee_id': employee.id,
                    'skill_id': mapping.skill_id.id,
                    'certificate_id': cert.id,
                    'skill_level_before_id': level_before.id if level_before else False,
                    'skill_level_after_id': mapping.skill_level_id.id,
                    'change_date': cert.issued_date.date() if cert.issued_date else fields.Date.today(),
                })

            cert.skill_synced = True

    @api.model
    def _is_level_upgrade(self, current_level, new_level):
        if not current_level or not new_level:
            return False
        return new_level.level_progress > current_level.level_progress
