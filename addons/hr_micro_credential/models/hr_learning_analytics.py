# Part of IMPC Microcredential Platform. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrLearningAnalyticsSnapshot(models.Model):
    """Daily snapshot of department-level learning analytics.
    
    Aggregated metrics per department, refreshed daily via cron.
    Used for the Analytics tab in the HR Learning dashboard.
    """
    _name = 'hr.learning.analytics.snapshot'
    _description = 'Department Learning Analytics Snapshot'
    _order = 'snapshot_date desc, department_id'

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        required=True,
        ondelete='cascade',
        index=True,
    )
    snapshot_date = fields.Date(
        string='Snapshot Date',
        required=True,
        index=True,
    )
    total_employees_in_learning = fields.Integer(
        string='Employees in Learning',
        default=0,
    )
    avg_completion_percentage = fields.Float(
        string='Avg Completion (%)',
        default=0.0,
    )
    total_certificates_this_period = fields.Integer(
        string='Certificates Issued',
        default=0,
    )
    completion_rate = fields.Float(
        string='Completion Rate (%)',
        default=0.0,
        help='Percentage of enrollments that have been completed',
    )
    at_risk_count = fields.Integer(
        string='At Risk Employees',
        default=0,
    )

    @api.model
    def _generate_daily_snapshot(self):
        """Scheduled action: Generate daily analytics snapshot per department.
        
        Called once per day via ir.cron.
        Aggregates data from hr.learning.progress records.
        """
        today = fields.Date.today()
        departments = self.env['hr.department'].search([])

        for dept in departments:
            progress_records = self.env['hr.learning.progress'].search([
                ('department_id', '=', dept.id),
            ])

            if not progress_records:
                continue

            total_enrolled = len(progress_records)
            completed = len(progress_records.filtered(lambda r: r.status == 'COMPLETED'))
            at_risk = len(progress_records.filtered(lambda r: r.status == 'AT_RISK'))
            avg_completion = (
                sum(progress_records.mapped('completion_percentage')) / total_enrolled
                if total_enrolled else 0.0
            )
            completion_rate = (completed / total_enrolled * 100) if total_enrolled else 0.0

            # Upsert: update if exists for today, else create
            existing = self.search([
                ('department_id', '=', dept.id),
                ('snapshot_date', '=', today),
            ], limit=1)

            vals = {
                'department_id': dept.id,
                'snapshot_date': today,
                'total_employees_in_learning': total_enrolled,
                'avg_completion_percentage': avg_completion,
                'total_certificates_this_period': completed,
                'completion_rate': completion_rate,
                'at_risk_count': at_risk,
            }

            if existing:
                existing.write(vals)
            else:
                self.create(vals)
