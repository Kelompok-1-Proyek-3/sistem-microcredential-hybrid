# -*- coding: utf-8 -*-
"""HR Manager Dashboard Controller - Web routes for HR managers to monitor employee learning."""

from odoo import fields, http
from odoo.http import request


class HRDashboardController(http.Controller):
    """HR Manager Dashboard - Overview of learning progress across all employees."""

    def _require_hr_manager(self):
        """Check if user has HR access. Returns redirect if not authorized."""
        user = request.env.user
        if user._is_public():
            return request.redirect('/web/login')
        
        # Check for HR access (HR manager or system admin)
        has_hr_access = (
            user.has_group('hr.group_hr_manager') or
            user.has_group('base.group_system') or
            user.has_group('hr.group_hr_user')
        )
        if not has_hr_access:
            return request.redirect('/')
        return None

    @http.route(['/hr/dashboard', '/impc/hr/dashboard'], type='http', auth='user', website=True)
    def hr_dashboard(self, **kw):
        """HR Dashboard with learning progress overview."""
        guard = self._require_hr_manager()
        if guard:
            return guard

        env = request.env

        # Get all departments with employees in learning
        departments = env['hr.department'].sudo().search([])

        # Learning progress statistics
        total_progress = env['hr.learning.progress'].sudo().search([])
        total_in_learning = len(total_progress)
        in_progress = total_progress.filtered(lambda r: r.status == 'in_progress')
        completed = total_progress.filtered(lambda r: r.status == 'completed')
        at_risk = total_progress.filtered(lambda r: r.status == 'at_risk')

        # Department-wise statistics
        dept_stats = []
        for dept in departments:
            dept_progress = total_progress.filtered(lambda r: r.department_id.id == dept.id)
            if dept_progress:
                dept_completed = len(dept_progress.filtered(lambda r: r.status == 'completed'))
                dept_at_risk = len(dept_progress.filtered(lambda r: r.status == 'at_risk'))
                avg_completion = sum(dept_progress.mapped('completion_percentage')) / len(dept_progress) if dept_progress else 0
                dept_stats.append({
                    'department': dept,
                    'total': len(dept_progress),
                    'completed': dept_completed,
                    'at_risk': dept_at_risk,
                    'avg_completion': avg_completion,
                })

        # Sort by total enrolled (descending)
        dept_stats = sorted(dept_stats, key=lambda x: x['total'], reverse=True)

        # Top 5 at-risk employees
        at_risk_employees = at_risk[:10]

        # Recent skill updates (last 10)
        recent_skill_logs = env['hr.employee.skill_mapping_log'].sudo().search(
            [],
            order='change_date desc',
            limit=10
        )

        # Recent learning notes
        recent_notes = env['hr.learning.profile.note'].sudo().search(
            [],
            order='note_date desc',
            limit=5
        )

        # Course enrollment trends (last 30 days)
        thirty_days_ago = fields.Datetime.now().replace(day=1)  # Start of month
        recent_enrollments = env['hr.learning.progress'].sudo().search([
            ('enrollment_date', '>=', thirty_days_ago)
        ])

        values = {
            'total_in_learning': total_in_learning,
            'total_in_progress': len(in_progress),
            'total_completed': len(completed),
            'total_at_risk': len(at_risk),
            'dept_stats': dept_stats[:8],  # Top 8 departments
            'at_risk_employees': at_risk_employees,
            'recent_skill_logs': recent_skill_logs,
            'recent_notes': recent_notes,
            'recent_enrollments_count': len(recent_enrollments),
        }
        return request.render('impc_hr_skills_sync.hr_dashboard', values)

    @http.route(['/hr/at-risk', '/impc/hr/at-risk'], type='http', auth='user', website=True)
    def hr_at_risk_list(self, department_id=None, **kw):
        """Detailed list of at-risk employees."""
        guard = self._require_hr_manager()
        if guard:
            return guard

        env = request.env

        domain = [('status', '=', 'at_risk')]
        if department_id:
            domain.append(('department_id', '=', int(department_id)))

        at_risk_records = env['hr.learning.progress'].sudo().search(
            domain,
            order='last_accessed_date asc'
        )

        # Group by department
        dept_groups = {}
        for rec in at_risk_records:
            dept_name = rec.department_id.name or 'No Department'
            if dept_name not in dept_groups:
                dept_groups[dept_name] = []
            dept_groups[dept_name].append(rec)

        departments = env['hr.department'].sudo().search([])

        values = {
            'at_risk_records': at_risk_records,
            'dept_groups': dept_groups,
            'departments': departments,
            'selected_department': int(department_id) if department_id else None,
            'total_at_risk': len(at_risk_records),
        }
        return request.render('impc_hr_skills_sync.hr_at_risk_list', values)

    @http.route(['/hr/department/<int:dept_id>', '/impc/hr/department/<int:dept_id>'], 
                type='http', auth='user', website=True)
    def hr_department_detail(self, dept_id, **kw):
        """Department learning detail page."""
        guard = self._require_hr_manager()
        if guard:
            return guard

        env = request.env
        department = env['hr.department'].sudo().browse(dept_id)
        if not department.exists():
            return request.redirect('/hr/dashboard')

        # Get learning progress for this department
        progress_records = env['hr.learning.progress'].sudo().search([
            ('department_id', '=', dept_id)
        ], order='last_accessed_date desc')

        # Get analytics snapshots for the department
        snapshots = env['hr.learning.analytics.snapshot'].sudo().search([
            ('department_id', '=', dept_id)
        ], order='snapshot_date desc', limit=30)

        # Department stats
        in_progress = progress_records.filtered(lambda r: r.status == 'in_progress')
        completed = progress_records.filtered(lambda r: r.status == 'completed')
        at_risk = progress_records.filtered(lambda r: r.status == 'at_risk')

        values = {
            'department': department,
            'progress_records': progress_records,
            'snapshots': snapshots,
            'total_employees': len(progress_records),
            'in_progress_count': len(in_progress),
            'completed_count': len(completed),
            'at_risk_count': len(at_risk),
            'avg_completion': sum(progress_records.mapped('completion_percentage')) / len(progress_records) if progress_records else 0,
        }
        return request.render('impc_hr_skills_sync.hr_department_detail', values)
