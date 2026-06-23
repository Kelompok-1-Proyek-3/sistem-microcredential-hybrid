# addons/sale_microcredential/models/sale_order.py
# DEV 1: Field definitions ONLY.
# TIDAK ADA method, TIDAK ADA @api.depends, TIDAK ADA action.
# Semua business logic ada di sale_order_workflow.py (Dev 2).
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ── CONTRACT TYPE ──────────────────────────────────────────
    contract_type = fields.Selection(
        selection=[
            ('B2C', 'B2C - Individual'),
            ('B2B_CONTRACT', 'B2B - Corporate Contract'),
        ],
        string='Contract Type',
        default='B2C',
        required=True,
        tracking=True,
    )
    partner_type = fields.Selection(
        selection=[
            ('INDIVIDUAL', 'Individual'),
            ('CORPORATE_HR', 'Corporate HR'),
            ('CORPORATE_OTHER', 'Corporate - Other'),
        ],
        string='Partner Type',
        default='INDIVIDUAL',
        tracking=True,
    )

    # ── CONTRACT PERIOD ────────────────────────────────────────
    contract_start_date = fields.Date(
        string='Contract Start Date',
        tracking=True,
    )
    expiry_date = fields.Date(
        string='Contract Expiry Date',
        tracking=True,
    )
    renewal_opportunity = fields.Boolean(
        string='Flag Renewal',
        default=False,
        help='Otomatis True jika expiry_date < 30 hari dari hari ini.',
    )
    renewed_to_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Renewed To',
        ondelete='set null',
        copy=False,
    )

    # ── REDEEM CODE TRACKING ───────────────────────────────────
    redeem_codes_generated = fields.Boolean(
        string='Redeem Codes Generated',
        default=False,
        copy=False,
    )
    redeem_code_batch_id = fields.Many2one(
        'impc.redeem.code.batch',
        string='Redeem Code Batch',
        copy=False,
    )
    redeem_codes_requested_at = fields.Datetime(
        string='Redeem Requested At',
        copy=False,
    )
    redeem_codes_generated_at = fields.Datetime(
        string='Redeem Generated At',
        copy=False,
    )
    redeem_code_batch_status = fields.Selection(
        selection=[
            ('PENDING', 'Pending'),
            ('GENERATED', 'Generated'),
            ('FAILED', 'Failed'),
        ],
        string='Batch Status',
        default='PENDING',
        copy=False,
    )
