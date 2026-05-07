# models/redeem_code_log.py
# Owner: Dev 2 — Integration & API Layer
# Scope: Model audit log untuk setiap request generate redeem code
# TODO: Dev 2 mengisi file ini

# models/redeem_code_log.py
from odoo import models, fields


class RedeemCodeRequestLog(models.Model):
    _name = 'redeem.code.request.log'
    _description = 'Log Request Generate Redeem Code'
    _order = 'requested_at desc'
    _rec_name = 'sale_order_id'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
    )
    course_id = fields.Many2one(
        comodel_name='slide.channel',
        string='Kursus',
    )
    quantity_requested = fields.Integer(string='Jumlah Diminta')
    expiry_days = fields.Integer(string='Masa Berlaku (hari)')
    status = fields.Selection(
        selection=[
            ('PENDING', 'Pending'),
            ('SUCCESS', 'Berhasil'),
            ('FAILED', 'Gagal'),
        ],
        string='Status',
        default='PENDING',
    )
    batch_id = fields.Char(string='Batch ID')
    response_payload = fields.Text(string='Response API (raw)')
    error_message = fields.Text(string='Pesan Error')
    requested_at = fields.Datetime(string='Waktu Request')
    completed_at = fields.Datetime(string='Waktu Selesai')