# Part of IMPC Microcredential Platform. See LICENSE file for full copyright and licensing details.

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class HrMicroCredentialAPI(http.Controller):
    """API endpoints consumed by Website Group for skill updates.
    
    The Website Group calls these endpoints when a certificate is issued,
    triggering automatic skill mapping for the employee.
    """

    @http.route(
        '/api/v1/hr/employees/<int:employee_id>/skills/update',
        type='json',
        auth='user',
        methods=['POST'],
    )
    def update_employee_skills(self, employee_id, **kwargs):
        """Receive certificate issuance event from Website Group.
        
        Called by Website Group (eLearning) when a certificate is generated.
        Looks up course → skill mappings and updates employee skills accordingly.
        
        Expected JSON payload:
            {
                "certificate_id": 123,
                "course_id": 5,
                "course_name": "Python Advanced",
                "certificate_date": "2026-04-20"
            }
        """
        certificate_id = kwargs.get('certificate_id')
        course_id = kwargs.get('course_id')
        course_name = kwargs.get('course_name', '')
        certificate_date = kwargs.get('certificate_date')

        employee = request.env['hr.employee'].browse(employee_id)
        if not employee.exists():
            return {'status': 'error', 'message': f'Employee {employee_id} not found'}

        # Find skill mappings for this course
        mappings = request.env['hr.course.skill.mapping'].search([
            ('course_id', '=', course_id),
        ])

        if not mappings:
            _logger.info(
                'No skill mappings found for course_id=%s (%s)',
                course_id, course_name,
            )
            return {'status': 'ok', 'message': 'No skill mappings configured for this course'}

        updated_skills = []
        for mapping in mappings:
            # Check if employee already has this skill
            existing_skill = request.env['hr.employee.skill'].search([
                ('employee_id', '=', employee_id),
                ('skill_id', '=', mapping.skill_id.id),
            ], limit=1)

            level_before = 'NONE'
            if existing_skill:
                level_before = existing_skill.skill_level_id.name if existing_skill.skill_level_id else 'NONE'
                # TODO: Update skill level if new level is higher
            else:
                # TODO: Create new hr.employee.skill record
                pass

            # Log the change
            request.env['hr.skill.mapping.log'].create({
                'employee_id': employee_id,
                'skill_id': mapping.skill_id.id,
                'certificate_id': certificate_id,
                'course_name': course_name,
                'skill_level_before': level_before,
                'skill_level_after': mapping.skill_level,
                'change_date': certificate_date or fields.Date.today(),
            })

            updated_skills.append({
                'skill': mapping.skill_id.name,
                'level': mapping.skill_level,
            })

        _logger.info(
            'Updated %d skills for employee %s from course %s',
            len(updated_skills), employee.name, course_name,
        )

        return {
            'status': 'ok',
            'updated_skills': updated_skills,
        }
