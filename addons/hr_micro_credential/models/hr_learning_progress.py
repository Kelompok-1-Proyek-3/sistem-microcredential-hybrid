# Part of IMPC Microcredential Platform. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrLearningProgress(models.Model):
    """Stores synced learning progress data from eLearning (Website Group).
    
    This is a read-model (cache) that gets populated via scheduled sync
    from the Website Group's eLearning API. HR Group does NOT write to
    eLearning models directly.
    """
    _name = 'hr.learning.progress'
    _description = 'Employee Learning Progress'
    _order = 'employee_id, course_name'
    _rec_name = 'display_name'

    # === Employee Reference ===
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
    )
    department_id = fields.Many2one(
        related='employee_id.department_id',
        string='Department',
        store=True,
        readonly=True,
    )

    # === Course Information (synced from eLearning) ===
    course_id = fields.Integer(
        string='Course ID (eLearning)',
        required=True,
        help='Foreign key reference to elearning.course in Website module',
    )
    course_name = fields.Char(
        string='Course Name',
        required=True,
    )
    learning_mode = fields.Selection(
        [
            ('ONLINE', 'Online'),
            ('OFFLINE', 'Offline'),
            ('HYBRID', 'Hybrid'),
        ],
        string='Learning Mode',
        required=True,
        default='ONLINE',
    )
    enrollment_id = fields.Integer(
        string='Enrollment ID (eLearning)',
        help='Foreign key reference to elearning.course_enrollment in Website module',
    )
    enrollment_date = fields.Date(
        string='Enrollment Date',
    )

    # === Progress Metrics ===
    completion_percentage = fields.Float(
        string='Completion (%)',
        default=0.0,
    )
    attendance_status = fields.Selection(
        [
            ('NOT_REQUIRED', 'Not Required'),
            ('PENDING', 'Pending'),
            ('HADIR', 'Hadir'),
            ('TIDAK_HADIR', 'Tidak Hadir'),
        ],
        string='Attendance Status',
        default='NOT_REQUIRED',
    )
    checkin_time = fields.Datetime(
        string='Check-in Time',
    )
    quiz_score = fields.Float(
        string='Quiz Score',
    )
    status = fields.Selection(
        [
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('AT_RISK', 'At Risk'),
        ],
        string='Status',
        default='IN_PROGRESS',
        compute='_compute_status',
        store=True,
    )
    last_accessed_date = fields.Datetime(
        string='Last Accessed',
    )
    estimated_completion_date = fields.Date(
        string='Estimated Completion',
    )

    # === Sync Metadata ===
    synced_at = fields.Datetime(
        string='Last Synced',
        readonly=True,
    )

    # === Display ===
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    @api.depends('employee_id.name', 'course_name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.employee_id.name} - {record.course_name}"

    @api.depends('completion_percentage', 'enrollment_date', 'attendance_status', 'quiz_score')
    def _compute_status(self):
        """Compute at-risk status based on configurable thresholds.
        
        Rules (from PRD):
        - completion 100% + quiz passed → COMPLETED
        - < 25% progress after 30 days → AT_RISK
        - Attendance blocked (hybrid, not checked-in past session) → AT_RISK
        - Otherwise → IN_PROGRESS
        """
        today = fields.Date.today()
        for record in self:
            if record.completion_percentage >= 100 and (record.quiz_score or 0) >= 70:
                record.status = 'COMPLETED'
            elif (
                record.enrollment_date
                and (today - record.enrollment_date).days > 30
                and record.completion_percentage < 25
            ):
                record.status = 'AT_RISK'
            elif (
                record.learning_mode == 'HYBRID'
                and record.attendance_status == 'TIDAK_HADIR'
            ):
                record.status = 'AT_RISK'
            else:
                record.status = 'IN_PROGRESS'

    # === Sync Method (called by cron) ===
    @api.model
    def _sync_learning_progress_from_elearning(self):
        """Scheduled action: Sync progress data from Website eLearning API.
        
        Called every 5 minutes via ir.cron.
        In production, this calls GET /api/v1/elearning/progress/all
        For now, this is a stub that will be connected once the
        Website Group provides the API endpoint (dependency W-08).
        """
        # TODO: Implement actual API call when Website endpoint W-08 is available
        # website_api = self.env['res.company']._get_website_api_client()
        # progress_data = website_api.get('/api/v1/elearning/progress/all', params={'since': last_sync})
        # for record in progress_data['data']:
        #     ... upsert logic ...
        pass
