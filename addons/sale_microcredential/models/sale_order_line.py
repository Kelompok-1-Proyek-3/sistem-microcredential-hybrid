# addons/sale_microcredential/models/sale_order_line.py
# DEV 1: Field definitions ONLY.
# TIDAK ADA method, TIDAK ADA @api.depends, TIDAK ADA action.
#
# KOREKSI ODOO 19:
#   - Field course FK menggunakan nama 'slide_channel_id' dan comodel 'slide.channel'
#   - Model 'elearning.course' TIDAK ADA di Odoo 19 — gunakan 'slide.channel'
from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # ── COURSE LINKAGE ─────────────────────────────────────────
    # Referensi ke slide.channel (native Odoo 19 eLearning model)
    # Field name: slide_channel_id (bukan course_id) — konsisten dengan PRD
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
        readonly=True,
        help='Diambil read-only dari course (dikelola Website Group via slide.channel).',
    )
    hybrid_session_summary = fields.Text(
        string='Jadwal Sesi Tatap Muka',
        readonly=True,
        help=(
            'READ-ONLY. Diisi dari event.event yang di-link ke slide.channel '
            'oleh Marketing Group.'
        ),
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
