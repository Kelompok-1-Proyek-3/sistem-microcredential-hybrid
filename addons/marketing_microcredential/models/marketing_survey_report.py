import base64
import csv
import io
from datetime import datetime, timedelta

from odoo import api, fields, models


class MarketingSurveyReport(models.Model):
    _name = 'marketing.survey.report'
    _description = 'Marketing Survey Monthly Report'
    _order = 'month_start desc, survey_id'

    survey_id = fields.Many2one(
        'survey.survey',
        string='Survey',
        required=True,
        ondelete='cascade',
        index=True,
    )
    month_start = fields.Date(
        string='Month Start',
        required=True,
        index=True,
    )
    month_end = fields.Date(
        string='Month End',
        required=True,
    )
    response_count = fields.Integer(
        string='Responses',
        default=0,
    )
    avg_score = fields.Float(
        string='Average Score',
        default=0.0,
    )
    nps_score = fields.Float(
        string='NPS Score',
        default=0.0,
    )
    last_synced = fields.Datetime(
        string='Last Synced',
        readonly=True,
    )

    _sql_constraints = [
        (
            'unique_survey_month',
            'unique(survey_id, month_start)',
            'Only one monthly report per survey is allowed.',
        ),
    ]

    @staticmethod
    def _get_month_range(target_date):
        first_day_this_month = target_date.replace(day=1)
        last_day_prev_month = first_day_this_month - timedelta(days=1)
        month_start = last_day_prev_month.replace(day=1)
        month_end = last_day_prev_month
        return month_start, month_end

    @api.model
    def _sync_monthly_survey_report(self):
        today = fields.Date.today()
        month_start, month_end = self._get_month_range(today)
        start_dt = datetime.combine(month_start, datetime.min.time())
        end_dt = datetime.combine(month_end + timedelta(days=1), datetime.min.time())

        surveys = self.env['survey.survey'].search([])
        for survey in surveys:
            responses = self.env['survey.user_input'].search([
                ('survey_id', '=', survey.id),
                ('state', '=', 'done'),
                ('create_date', '>=', fields.Datetime.to_string(start_dt)),
                ('create_date', '<', fields.Datetime.to_string(end_dt)),
            ])
            response_count = len(responses)

            avg_score = 0.0
            nps_score = 0.0

            if responses:
                lines = self.env['survey.user_input.line'].search([
                    ('user_input_id', 'in', responses.ids),
                    ('value_number', '!=', False),
                ])
                if lines:
                    total = sum(lines.mapped('value_number'))
                    avg_score = total / len(lines)

                if survey.nps_question_id:
                    nps_lines = self.env['survey.user_input.line'].search([
                        ('user_input_id', 'in', responses.ids),
                        ('question_id', '=', survey.nps_question_id.id),
                        ('value_number', '!=', False),
                    ])
                    if nps_lines:
                        promoters = len([ln for ln in nps_lines if ln.value_number >= 9])
                        detractors = len([ln for ln in nps_lines if ln.value_number <= 6])
                        total_nps = len(nps_lines)
                        nps_score = ((promoters / total_nps) - (detractors / total_nps)) * 100

            vals = {
                'month_start': month_start,
                'month_end': month_end,
                'response_count': response_count,
                'avg_score': round(avg_score, 2),
                'nps_score': round(nps_score, 2),
                'last_synced': fields.Datetime.now(),
            }

            existing = self.search([
                ('survey_id', '=', survey.id),
                ('month_start', '=', month_start),
            ], limit=1)
            if existing:
                existing.write(vals)
            else:
                self.create({**vals, 'survey_id': survey.id})

    @api.model
    def _export_monthly_survey_csv(self):
        today = fields.Date.today()
        month_start, _month_end = self._get_month_range(today)
        records = self.search([
            ('month_start', '=', month_start),
        ])

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            'Survey', 'Month Start', 'Month End',
            'Responses', 'Average Score', 'NPS Score'
        ])
        for record in records:
            writer.writerow([
                record.survey_id.title,
                record.month_start,
                record.month_end,
                record.response_count,
                record.avg_score,
                record.nps_score,
            ])

        content = buffer.getvalue().encode('utf-8')
        buffer.close()

        filename = f"monthly_survey_report_{month_start}.csv"
        self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(content),
            'res_model': 'res.company',
            'res_id': self.env.company.id,
            'mimetype': 'text/csv',
        })
