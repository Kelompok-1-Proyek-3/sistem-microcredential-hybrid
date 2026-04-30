# models/sale_order_line_contract.py
# Owner: Dev 1 — Contract Core
# Scope: Extend sale.order.line dengan field khusus B2B (kursus, student count, redeem spec)

from odoo import models, fields


class SaleOrderLineContract(models.Model):
    _inherit = 'sale.order.line'

    # ── Referensi Kursus ──────────────────────────────────────────────────────
    course_id = fields.Many2one(
        comodel_name='slide.channel',
        string='Kursus',
        ondelete='set null',
        help='Kursus Microcredential yang terkait dengan line item ini.',
    )

    # ── Kuantitas Khusus B2B ──────────────────────────────────────────────────
    student_count = fields.Integer(
        string='Jumlah Student',
        default=1,
        help='Jumlah slot student dalam paket B2B.',
    )
    redeem_code_count = fields.Integer(
        string='Jumlah Redeem Code',
        help='Jumlah redeem code yang akan digenerate untuk line ini. Default = student_count.',
    )
    redeem_code_expiry_days = fields.Integer(
        string='Masa Berlaku Redeem Code (hari)',
        default=90,
        help='Redeem code kadaluarsa setelah N hari dari tanggal generate.',
    )

    # ── Catatan Distribusi ────────────────────────────────────────────────────
    redeem_code_notes = fields.Text(
        string='Catatan Redeem Code',
        help='Instruksi distribusi kode untuk HR manager.',
    )
