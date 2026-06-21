# addons/sale_microcredential/models/sale_order_line.py
from odoo import api, models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # ── COURSE LINKAGE ─────────────────────────────────────────
    slide_channel_id = fields.Many2one(
        comodel_name='slide.channel',
        string='Course',
        ondelete='set null',
    )
    learning_mode = fields.Selection(
        selection=[
            ('online', 'Online'),
            ('offline', 'Offline'),
            ('hybrid', 'Hybrid'),
        ],
        string='Learning Mode',
<<<<<<< HEAD
        readonly=True,
        help='Auto-filled from the selected course.',
=======
        help='Mode pembelajaran untuk line ini.',
>>>>>>> 42dfb97135ddfe2f75cdcc4a016e4fcafe923a67
    )
    hybrid_session_summary = fields.Text(
        string='Jadwal Sesi Tatap Muka',
        readonly=True,
        help='Auto-filled from the course event for hybrid/offline mode.',
    )

    # ── REDEEM CODE CONFIG PER LINE ────────────────────────────
    redeem_code_count = fields.Integer(
        string='Jumlah Redeem Code',
        default=0,
    )
    redeem_code_expiry_days = fields.Integer(
        string='Masa Berlaku Kode (Hari)',
        default=90,
    )
    student_count = fields.Integer(
        string='Jumlah Peserta',
        default=1,
    )
    course_access_duration_days = fields.Integer(
        string='Durasi Akses Kursus (Hari)',
        default=90,
    )

    # ── ONCHANGE ───────────────────────────────────────────────
    @api.onchange('slide_channel_id')
    def _onchange_slide_channel_id(self):
        """Auto-fill learning_mode and hybrid_session_summary from course."""
        if self.slide_channel_id:
            self.learning_mode = self.slide_channel_id.learning_mode
            if self.slide_channel_id.learning_mode in ('hybrid', 'offline') and self.slide_channel_id.event_id:
                event = self.slide_channel_id.event_id
                self.hybrid_session_summary = (
                    f"{event.name}\n"
                    f"Tanggal: {event.date_begin} - {event.date_end}\n"
                    f"Lokasi: {event.address_inline or 'TBD'}"
                )
            else:
                self.hybrid_session_summary = False
        else:
            self.learning_mode = False
            self.hybrid_session_summary = False
