# -*- coding: utf-8 -*-
"""Employee Learning Profile Controller - Individual employee learning view."""

from odoo import http
from odoo.http import request


class HREmployeeProfileController(http.Controller):
    """Employee Learning Profile - Individual employee learning dashboard."""

    def _require_employee_access(self, employee_id):
        """Check if user can access employee profile.
        - HR managers can see all employees
        - Regular users can only see their own profile
        """
        user = request.env.user
        if user._is_public():
            return None, request.redirect('/web/login')

        employee = request.env['hr.employee'].sudo().browse(employee_id)
        if not employee.exists():
            return None, request.redirect('/hr/dashboard')

        # HR managers and admins can see all profiles
        has_hr_access = (
            user.has_group('hr.group_hr_manager') or
            user.has_group('base.group_system') or
            user.has_group('hr.group_hr_user')
        )

        # Check if viewing own profile
        is_own_profile = (
            employee.user_id.id == user.id or
            employee.work_contact_id.id == user.partner_id.id
        )

        if not has_hr_access and not is_own_profile:
            return None, request.redirect('/')

        return employee, None

    @http.route(['/hr/employee/<int:employee_id>', '/impc/hr/employee/<int:employee_id>'], 
                type='http', auth='user', website=True)
    def employee_profile(self, employee_id, **kw):
        """Employee learning profile page."""
        employee, guard = self._require_employee_access(employee_id)
        if guard:
            return guard

        env = request.env

        # Get learning progress for this employee
        progress_records = env['hr.learning.progress'].sudo().search([
            ('employee_id', '=', employee_id)
        ], order='last_accessed_date desc')

        # Get skill mapping logs
        skill_logs = env['hr.employee.skill_mapping_log'].sudo().search([
            ('employee_id', '=', employee_id)
        ], order='change_date desc', limit=10)

        # Get current skills
        skills = env['hr.employee.skill'].sudo().search([
            ('employee_id', '=', employee_id)
        ])

        # Get learning notes
        notes = env['hr.learning.profile.note'].sudo().search([
            ('employee_id', '=', employee_id)
        ], order='note_date desc')

        # Get certificates
        partner_id = employee.user_id.partner_id.id if employee.user_id else employee.work_contact_id.id
        certificates = env['impc.certificate'].sudo().search([
            ('partner_id', '=', partner_id),
            ('state', '=', 'issued')
        ], order='issued_date desc') if partner_id else env['impc.certificate']

        # Statistics
        in_progress = progress_records.filtered(lambda r: r.status == 'in_progress')
        completed = progress_records.filtered(lambda r: r.status == 'completed')
        at_risk = progress_records.filtered(lambda r: r.status == 'at_risk')

        values = {
            'employee': employee,
            'progress_records': progress_records,
            'skill_logs': skill_logs,
            'skills': skills,
            'notes': notes,
            'certificates': certificates,
            'total_courses': len(progress_records),
            'in_progress_count': len(in_progress),
            'completed_count': len(completed),
            'at_risk_count': len(at_risk),
            'total_skills': len(skills),
            'total_certificates': len(certificates),
            'is_own_profile': employee.user_id.id == request.env.user.id,
        }
        return request.render('impc_hr_skills_sync.hr_employee_profile', values)

    @http.route(['/hr/employee/<int:employee_id>/note/add'], 
                type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def add_employee_note(self, employee_id, note_text=None, **kw):
        """Add a learning note to employee profile."""
        employee, guard = self._require_employee_access(employee_id)
        if guard:
            return guard

        if note_text and note_text.strip():
            request.env['hr.learning.profile.note'].sudo().create({
                'employee_id': employee_id,
                'note_text': note_text.strip(),
                'created_by': request.env.user.id,
            })

        return request.redirect(f'/hr/employee/{employee_id}')

    @http.route(['/my-learning/profile', '/impc/my-learning/profile'], 
                type='http', auth='user', website=True)
    def my_learning_profile(self, **kw):
        """Redirect current user to their employee profile."""
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', user.id)
        ], limit=1)

        if employee:
            return request.redirect(f'/hr/employee/{employee.id}')
        else:
            # No employee record - redirect to student dashboard
            return request.redirect('/my-learning')

    @http.route(['/hr/employees', '/impc/hr/employees'], type='http', auth='user', website=True)
    def employee_list(self, search='', department_id=None, status='all', **kw):
        """List all employees with learning data."""
        user = request.env.user
        if user._is_public():
            return request.redirect('/web/login')

        has_hr_access = (
            user.has_group('hr.group_hr_manager') or
            user.has_group('base.group_system') or
            user.has_group('hr.group_hr_user')
        )
        if not has_hr_access:
            return request.redirect('/')

        env = request.env

        # Build domain for employees
        domain = [('user_id', '!=', False)]  # Only employees with user accounts
        if department_id:
            domain.append(('department_id', '=', int(department_id)))

        if search:
            domain.append('|')
            domain.append(('name', 'ilike', search))
            domain.append(('work_email', 'ilike', search))

        employees = env['hr.employee'].sudo().search(domain, order='name')

        # Get learning progress summary per employee
        employee_data = []
        for emp in employees:
            progress = env['hr.learning.progress'].sudo().search([
                ('employee_id', '=', emp.id)
            ])
            
            if status != 'all':
                progress = progress.filtered(lambda r: r.status == status)
            
            if progress or status == 'all':
                employee_data.append({
                    'employee': emp,
                    'progress': progress,
                    'total_courses': len(progress),
                    'in_progress': len(progress.filtered(lambda r: r.status == 'in_progress')),
                    'completed': len(progress.filtered(lambda r: r.status == 'completed')),
                    'at_risk': len(progress.filtered(lambda r: r.status == 'at_risk')),
                    'avg_completion': sum(progress.mapped('completion_percentage')) / len(progress) if progress else 0,
                })

        departments = env['hr.department'].sudo().search([])

        values = {
            'employee_data': employee_data,
            'departments': departments,
            'search': search,
            'selected_department': int(department_id) if department_id else None,
            'selected_status': status,
            'total_employees': len(employee_data),
        }
        return request.render('impc_hr_skills_sync.hr_employee_list', values)
