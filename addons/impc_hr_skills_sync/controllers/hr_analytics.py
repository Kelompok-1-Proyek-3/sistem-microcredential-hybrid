# -*- coding: utf-8 -*-
"""HR Learning Analytics Controller - Charts and reports for learning analytics."""

import json
from datetime import datetime, timedelta

from odoo import fields, http
from odoo.http import request


class HRAnalyticsController(http.Controller):
    """HR Learning Analytics - Visual charts and reports."""

    def _require_hr_manager(self):
        """Check if user has HR access."""
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
        return None

    @http.route(['/hr/analytics', '/impc/hr/analytics'], type='http', auth='user', website=True)
    def hr_analytics_dashboard(self, period='month', **kw):
        """HR Analytics dashboard with charts."""
        guard = self._require_hr_manager()
        if guard:
            return guard

        env = request.env

        # Determine date range
        today = fields.Date.today()
        if period == 'week':
            start_date = today - timedelta(days=7)
        elif period == 'month':
            start_date = today - timedelta(days=30)
        elif period == 'quarter':
            start_date = today - timedelta(days=90)
        else:
            start_date = today - timedelta(days=30)

        # Get analytics snapshots
        snapshots = env['hr.learning.analytics.snapshot'].sudo().search([
            ('snapshot_date', '>=', start_date)
        ], order='snapshot_date')

        # Aggregate data for charts
        dept_chart_data = self._get_department_chart_data(snapshots)
        trend_chart_data = self._get_trend_chart_data(snapshots)
        status_chart_data = self._get_status_chart_data()

        # Course enrollment by department
        dept_enrollment = self._get_dept_enrollment_data()

        # Top performing courses
        top_courses = self._get_top_courses()

        # Skill acquisition trends
        skill_trends = self._get_skill_trends(start_date)

        values = {
            'period': period,
            'dept_chart_data': json.dumps(dept_chart_data),
            'trend_chart_data': json.dumps(trend_chart_data),
            'status_chart_data': json.dumps(status_chart_data),
            'dept_enrollment': dept_enrollment,
            'top_courses': top_courses,
            'skill_trends': skill_trends,
        }
        return request.render('impc_hr_skills_sync.hr_analytics_dashboard', values)

    def _get_department_chart_data(self, snapshots):
        """Get department-wise chart data."""
        dept_data = {}
        for snapshot in snapshots:
            dept_name = snapshot.department_id.name or 'Unknown'
            if dept_name not in dept_data:
                dept_data[dept_name] = {
                    'total': 0,
                    'completed': 0,
                    'at_risk': 0,
                }
            dept_data[dept_name]['total'] += snapshot.total_employees_in_learning
            dept_data[dept_name]['completed'] += snapshot.total_certificates_this_period
            dept_data[dept_name]['at_risk'] += snapshot.at_risk_count

        return {
            'labels': list(dept_data.keys())[:10],
            'datasets': {
                'total': [d['total'] for d in dept_data.values()][:10],
                'completed': [d['completed'] for d in dept_data.values()][:10],
                'at_risk': [d['at_risk'] for d in dept_data.values()][:10],
            }
        }

    def _get_trend_chart_data(self, snapshots):
        """Get learning trend over time."""
        date_data = {}
        for snapshot in snapshots:
            date_str = snapshot.snapshot_date.strftime('%Y-%m-%d')
            if date_str not in date_data:
                date_data[date_str] = {
                    'completion_rate': 0,
                    'count': 0,
                }
            date_data[date_str]['completion_rate'] += snapshot.completion_rate
            date_data[date_str]['count'] += 1

        # Calculate averages
        labels = sorted(date_data.keys())
        completion_rates = [
            date_data[d]['completion_rate'] / date_data[d]['count'] if date_data[d]['count'] > 0 else 0
            for d in labels
        ]

        return {
            'labels': labels,
            'completion_rates': completion_rates,
        }

    def _get_status_chart_data(self):
        """Get overall status distribution."""
        env = request.env
        total_progress = env['hr.learning.progress'].sudo().search([])

        in_progress = len(total_progress.filtered(lambda r: r.status == 'in_progress'))
        completed = len(total_progress.filtered(lambda r: r.status == 'completed'))
        at_risk = len(total_progress.filtered(lambda r: r.status == 'at_risk'))

        return {
            'labels': ['In Progress', 'Completed', 'At Risk'],
            'data': [in_progress, completed, at_risk],
        }

    def _get_dept_enrollment_data(self):
        """Get department enrollment statistics."""
        env = request.env
        departments = env['hr.department'].sudo().search([])

        data = []
        for dept in departments:
            progress = env['hr.learning.progress'].sudo().search([
                ('department_id', '=', dept.id)
            ])
            if progress:
                data.append({
                    'department': dept.name,
                    'total': len(progress),
                    'avg_completion': sum(progress.mapped('completion_percentage')) / len(progress),
                    'at_risk': len(progress.filtered(lambda r: r.status == 'at_risk')),
                })

        return sorted(data, key=lambda x: x['total'], reverse=True)[:10]

    def _get_top_courses(self):
        """Get most enrolled courses."""
        env = request.env
        progress_records = env['hr.learning.progress'].sudo().search([])

        course_data = {}
        for rec in progress_records:
            course_id = rec.channel_id.id
            if course_id not in course_data:
                course_data[course_id] = {
                    'name': rec.course_name,
                    'total': 0,
                    'completed': 0,
                }
            course_data[course_id]['total'] += 1
            if rec.status == 'completed':
                course_data[course_id]['completed'] += 1

        # Sort by total enrollment
        sorted_courses = sorted(course_data.values(), key=lambda x: x['total'], reverse=True)[:10]
        return sorted_courses

    def _get_skill_trends(self, start_date):
        """Get skill acquisition trends."""
        env = request.env
        logs = env['hr.employee.skill_mapping_log'].sudo().search([
            ('change_date', '>=', start_date)
        ], order='change_date')

        skill_data = {}
        for log in logs:
            skill_name = log.skill_id.name
            if skill_name not in skill_data:
                skill_data[skill_name] = 0
            skill_data[skill_name] += 1

        sorted_skills = sorted(skill_data.items(), key=lambda x: x[1], reverse=True)[:10]
        return [{'skill': s[0], 'count': s[1]} for s in sorted_skills]

    @http.route(['/hr/analytics/department/<int:dept_id>'], 
                type='http', auth='user', website=True)
    def department_analytics(self, dept_id, **kw):
        """Detailed analytics for a specific department."""
        guard = self._require_hr_manager()
        if guard:
            return guard

        env = request.env
        department = env['hr.department'].sudo().browse(dept_id)
        if not department.exists():
            return request.redirect('/hr/analytics')

        # Get snapshots for this department
        snapshots = env['hr.learning.analytics.snapshot'].sudo().search([
            ('department_id', '=', dept_id)
        ], order='snapshot_date desc', limit=30)

        # Get progress records
        progress_records = env['hr.learning.progress'].sudo().search([
            ('department_id', '=', dept_id)
        ])

        # Build charts
        progress_chart_data = self._build_progress_chart(progress_records)
        timeline_chart_data = self._build_timeline_chart(snapshots)

        # Employee breakdown
        employee_data = []
        for rec in progress_records:
            employee_data.append({
                'employee': rec.employee_id,
                'course': rec.channel_id,
                'completion': rec.completion_percentage,
                'status': rec.status,
                'last_accessed': rec.last_accessed_date,
            })

        values = {
            'department': department,
            'snapshots': snapshots,
            'progress_records': progress_records,
            'progress_chart_data': json.dumps(progress_chart_data),
            'timeline_chart_data': json.dumps(timeline_chart_data),
            'employee_data': employee_data,
            'total_employees': len(progress_records.mapped('employee_id')),
            'total_courses': len(progress_records.mapped('channel_id')),
        }
        return request.render('impc_hr_skills_sync.hr_department_analytics', values)

    def _build_progress_chart(self, progress_records):
        """Build progress distribution chart."""
        bins = {
            '0-25%': 0,
            '26-50%': 0,
            '51-75%': 0,
            '76-99%': 0,
            '100%': 0,
        }
        for rec in progress_records:
            pct = rec.completion_percentage
            if pct <= 25:
                bins['0-25%'] += 1
            elif pct <= 50:
                bins['26-50%'] += 1
            elif pct <= 75:
                bins['51-75%'] += 1
            elif pct < 100:
                bins['76-99%'] += 1
            else:
                bins['100%'] += 1

        return {
            'labels': list(bins.keys()),
            'data': list(bins.values()),
        }

    def _build_timeline_chart(self, snapshots):
        """Build timeline chart from snapshots."""
        return {
            'labels': [s.snapshot_date.strftime('%Y-%m-%d') for s in reversed(snapshots)],
            'completion_rate': [s.completion_rate for s in reversed(snapshots)],
            'avg_completion': [s.avg_completion_percentage for s in reversed(snapshots)],
            'at_risk': [s.at_risk_count for s in reversed(snapshots)],
        }
