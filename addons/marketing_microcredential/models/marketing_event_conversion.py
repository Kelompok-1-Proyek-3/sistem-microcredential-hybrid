import base64
import csv
import io
from datetime import datetime, timedelta

from odoo import api, fields, models


class MarketingEventConversionReport(models.Model):
    _name = 'marketing.event.conversion.report'
    _description = 'Marketing Event Conversion Report'
    _order = 'week_start desc, event_id'

    event_id = fields.Many2one(
        'event.event',
        string='Event',
        required=True,
        ondelete='cascade',
        index=True,
    )
    course_id = fields.Many2one(
        'slide.channel',
        string='Course',
        ondelete='set null',
        index=True,
    )
    week_start = fields.Date(
        string='Week Start',
        required=True,
        index=True,
    )
    week_end = fields.Date(
        string='Week End',
        required=True,
    )
    registered_count = fields.Integer(
        string='Registered',
        default=0,
    )
    attended_count = fields.Integer(
        string='Attended',
        default=0,
    )
    enrolled_count = fields.Integer(
        string='Enrolled',
        default=0,
    )
    conversion_rate = fields.Float(
        string='Conversion (%)',
        compute='_compute_conversion_rate',
        store=True,
    )
    last_synced = fields.Datetime(
        string='Last Synced',
        readonly=True,
    )

    _sql_constraints = [
        (
            'unique_event_week',
            'unique(event_id, week_start)',
            'Only one weekly report per event is allowed.',
        ),
    ]

    @api.depends('attended_count', 'enrolled_count')
    def _compute_conversion_rate(self):
        for record in self:
            if record.attended_count:
                record.conversion_rate = (record.enrolled_count / record.attended_count) * 100
            else:
                record.conversion_rate = 0.0

    @staticmethod
    def _get_week_range(target_date):
        week_start = target_date - timedelta(days=target_date.weekday() + 7)
        week_end = week_start + timedelta(days=6)
        return week_start, week_end

    @api.model
    def _sync_weekly_conversion_report(self):
        today = fields.Date.today()
        week_start, week_end = self._get_week_range(today)
        start_dt = datetime.combine(week_start, datetime.min.time())
        end_dt = datetime.combine(week_end + timedelta(days=1), datetime.min.time())

        events = self.env['event.event'].search([
            ('date_begin', '>=', fields.Datetime.to_string(start_dt)),
            ('date_begin', '<', fields.Datetime.to_string(end_dt)),
        ])

        for event in events:
            registrations = self.env['event.registration'].search([
                ('event_id', '=', event.id),
                ('state', 'in', ['open', 'done']),
            ])
            attended_regs = registrations.filtered(lambda reg: reg.state == 'done')

            course = self.env['slide.channel'].search([('event_id', '=', event.id)], limit=1)
            enrolled_count = 0
            if course and attended_regs:
                partner_ids = attended_regs.mapped('partner_id').ids
                enrolled_count = self.env['slide.channel.partner'].search_count([
                    ('channel_id', '=', course.id),
                    ('partner_id', 'in', partner_ids),
                ])

            vals = {
                'course_id': course.id or False,
                'week_start': week_start,
                'week_end': week_end,
                'registered_count': len(registrations),
                'attended_count': len(attended_regs),
                'enrolled_count': enrolled_count,
                'last_synced': fields.Datetime.now(),
            }

            existing = self.search([
                ('event_id', '=', event.id),
                ('week_start', '=', week_start),
            ], limit=1)
            if existing:
                existing.write(vals)
            else:
                self.create({**vals, 'event_id': event.id})

    @api.model
    def _export_weekly_conversion_csv(self):
        today = fields.Date.today()
        week_start, week_end = self._get_week_range(today)
        records = self.search([
            ('week_start', '=', week_start),
        ])

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            'Event', 'Course', 'Week Start', 'Week End',
            'Registered', 'Attended', 'Enrolled', 'Conversion (%)'
        ])
        for record in records:
            writer.writerow([
                record.event_id.name,
                record.course_id.name or '',
                record.week_start,
                record.week_end,
                record.registered_count,
                record.attended_count,
                record.enrolled_count,
                round(record.conversion_rate, 2),
            ])

        content = buffer.getvalue().encode('utf-8')
        buffer.close()

        filename = f"weekly_event_conversion_{week_start}.csv"
        self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(content),
            'res_model': 'res.company',
            'res_id': self.env.company.id,
            'mimetype': 'text/csv',
        })
