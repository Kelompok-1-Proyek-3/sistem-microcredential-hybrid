from odoo import api, fields, models


class SlideChannelPartner(models.Model):
    _inherit = 'slide.channel.partner'

    # === Enrollment Type ===
    enrollment_type = fields.Selection(
        selection=[
            ('b2c_payment', 'B2C Payment'),
            ('b2b_voucher', 'B2B Voucher'),
            ('manual', 'Manual Enrollment'),
        ],
        string='Enrollment Type',
        default='manual',
        help='How the student was enrolled in this course.',
    )

    # === Voucher Reference ===
    redeem_code_id = fields.Many2one(
        'impc.redeem.code',
        string='Redeem Code Used',
        readonly=True,
        help='The voucher code used for B2B enrollment.',
    )

    # === Enrollment Metadata ===
    enrollment_date = fields.Datetime(
        string='Enrollment Date',
        default=fields.Datetime.now,
        readonly=True,
    )

    # === Certificate Link ===
    certificate_id = fields.Many2one(
        'impc.certificate',
        string='Certificate',
        readonly=True,
        help='The certificate issued upon course completion.',
    )

    # === Certificate Pending Flag ===
    certificate_pending = fields.Boolean(
        string='Certificate Pending',
        default=False,
        help='Set to True when completion criteria are met, awaiting cron to generate.',
    )

    # === Exam Gating (Hybrid) ===
    exam_unlocked = fields.Boolean(
        string='Exam Unlocked',
        compute='_compute_exam_unlocked',
        store=True,
        help='Whether the final exam is accessible (based on attendance for hybrid courses).',
    )

    # === Attendance Reference ===
    session_attendance_id = fields.Many2one(
        'impc.session.attendance',
        string='Session Attendance',
        readonly=True,
    )

    @api.depends(
        'channel_id.learning_mode',
        'session_attendance_id.attendance_status',
    )
    def _compute_exam_unlocked(self):
        for record in self:
            if record.channel_id.learning_mode == 'online':
                record.exam_unlocked = True
            elif record.channel_id.learning_mode in ('hybrid', 'offline'):
                attendance = record.session_attendance_id
                record.exam_unlocked = (
                    attendance and attendance.attendance_status == 'hadir'
                )
            else:
                record.exam_unlocked = True

    def _check_completion_and_set_pending(self):
        """Check if enrollment is fully completed and set pending flag."""
        for record in self:
            if (
                record.member_status == 'completed'
                and record.completion >= 100
                and not record.certificate_id
                and not record.certificate_pending
            ):
                record.certificate_pending = True

    def write(self, vals):
        res = super().write(vals)
        if 'member_status' in vals or 'completion' in vals:
            self._check_completion_and_set_pending()
        return res
