from datetime import timedelta
from odoo import api, fields, models

class HrLearningProgress(models.Model):
    _name = 'hr.learning.progress'
    _description = 'HR Learning Progress'
    _order = 'last_accessed_date desc, id desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True, ondelete='cascade')
    channel_id = fields.Many2one('slide.channel', string='Course', required=True, index=True, ondelete='cascade')
    course_name = fields.Char(related='channel_id.name', string='Course Name', store=True)
    learning_mode = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('hybrid', 'Hybrid')
    ], string='Learning Mode', store=True, compute='_compute_learning_mode')
    channel_partner_id = fields.Many2one('slide.channel.partner', string='Enrollment', required=True, index=True, ondelete='cascade')
    enrollment_date = fields.Datetime(related='channel_partner_id.create_date', string='Enrollment Date', store=True)
    completion_percentage = fields.Integer(string='Completion (%)', default=0)
    attendance_status = fields.Selection([
        ('not_required', 'Not Required'),
        ('pending', 'Pending'),
        ('hadir', 'Hadir'),
        ('tidak_hadir', 'Tidak Hadir')
    ], string='Attendance Status', default='not_required')
    checkin_time = fields.Datetime(string='Check-in Time')
    status = fields.Selection([
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('at_risk', 'At Risk')
    ], string='Status', default='in_progress', index=True)
    last_accessed_date = fields.Datetime(string='Last Accessed Date')

    @api.depends('channel_id')
    def _compute_learning_mode(self):
        for record in self:
            # Assuming channel_id might have a custom field learning_mode, if not default to online
            if hasattr(record.channel_id, 'learning_mode'):
                record.learning_mode = record.channel_id.learning_mode
            else:
                record.learning_mode = 'online'

    @api.model
    def _sync_learning_progress_from_elearning(self):
        employees = self.env['hr.employee'].search([('user_id', '!=', False)])
        partner_employee_map = {e.user_id.partner_id.id: e.id for e in employees if e.user_id.partner_id}
        
        if not partner_employee_map:
            return

        enrollments = self.env['slide.channel.partner'].search([
            ('partner_id', 'in', list(partner_employee_map.keys()))
        ])

        progress_recs = self.search([('channel_partner_id', 'in', enrollments.ids)])
        progress_map = {rec.channel_partner_id.id: rec for rec in progress_recs}

        for enrollment in enrollments:
            emp_id = partner_employee_map.get(enrollment.partner_id.id)
            if not emp_id:
                continue
                
            attendance = False
            if hasattr(enrollment, 'session_attendance_id') and enrollment.session_attendance_id:
                attendance = enrollment.session_attendance_id

            # Determine Status
            status = 'in_progress'
            if enrollment.completion == 100:
                status = 'completed'
            else:
                # Check if at risk
                enrollment_age = (fields.Datetime.now() - enrollment.create_date).days
                if enrollment_age > 30 and enrollment.completion < 25:
                    status = 'at_risk'

            vals = {
                'completion_percentage': enrollment.completion,
                'attendance_status': attendance.attendance_status if attendance and hasattr(attendance, 'attendance_status') else 'not_required',
                'checkin_time': attendance.checkin_time if attendance and hasattr(attendance, 'checkin_time') else False,
                'status': status,
                'last_accessed_date': enrollment.write_date,
            }

            if enrollment.id in progress_map:
                progress_map[enrollment.id].write(vals)
            else:
                self.create({
                    **vals,
                    'employee_id': emp_id,
                    'channel_id': enrollment.channel_id.id,
                    'channel_partner_id': enrollment.id,
                })

    @api.model
    def _send_at_risk_alerts(self):
        at_risk_records = self.search([('status', '=', 'at_risk')])
        template = self.env.ref('impc_hr_skills_sync.mail_template_at_risk_alert', raise_if_not_found=False)
        if not template:
            return

        for record in at_risk_records:
            ctx = {
                'course_name': record.course_name,
                'progress_pct': record.completion_percentage,
            }
            template.with_context(ctx).send_mail(record.employee_id.id, force_send=True)
