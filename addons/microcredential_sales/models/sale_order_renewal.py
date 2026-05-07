# models/sale_order_renewal.py
# Owner: Dev 3 — CRM, Portal & Dashboard
# Scope: Renewal workflow, expiry_date, days_until_expiry, cron job renewal check
# TODO: Dev 3 mengisi file ini

# models/sale_order_renewal.py
from datetime import timedelta
from odoo import models, fields, api, _


class SaleOrderRenewal(models.Model):
    _inherit = 'sale.order'

    expiry_date = fields.Date(
        string='Tanggal Kadaluarsa Kontrak',
        help='Untuk B2B: gunakan contract_end_date. Field ini untuk kalkulasi renewal.',
        compute='_compute_expiry_date',
        store=True,
    )
    renewal_opportunity = fields.Boolean(
        string='Peluang Renewal',
        compute='_compute_renewal_opportunity',
        store=True,
    )
    renewed_to_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Diperpanjang ke Kontrak',
        copy=False,
        readonly=True,
    )
    days_until_expiry = fields.Integer(
        string='Hari Menuju Kadaluarsa',
        compute='_compute_days_until_expiry',
    )

    @api.depends('contract_end_date')
    def _compute_expiry_date(self):
        for rec in self:
            rec.expiry_date = rec.contract_end_date

    @api.depends('expiry_date')
    def _compute_renewal_opportunity(self):
        today = fields.Date.today()
        threshold = today + timedelta(days=30)
        for rec in self:
            if rec.expiry_date and rec.contract_type == 'B2B_CONTRACT':
                rec.renewal_opportunity = rec.expiry_date <= threshold and rec.contract_status == 'ongoing'
            else:
                rec.renewal_opportunity = False

    @api.depends('expiry_date')
    def _compute_days_until_expiry(self):
        today = fields.Date.today()
        for rec in self:
            if rec.expiry_date:
                delta = rec.expiry_date - today
                rec.days_until_expiry = delta.days
            else:
                rec.days_until_expiry = 0

    def action_create_renewal_quotation(self):
        """Buat quotation baru sebagai renewal dari kontrak ini."""
        self.ensure_one()
        new_order = self.copy({
            'name': self.env['ir.sequence'].next_by_code('sale.order'),
            'contract_status': 'draft',
            'approval_state': 'draft',
            'redeem_codes_generated': False,
            'redeem_code_batch_id': False,
            'redeem_code_batch_status': 'PENDING',
        })
        self.renewed_to_order_id = new_order
        self.message_post(
            body=_('Renewal quotation dibuat: %s') % new_order.name,
        )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Renewal Quotation',
            'res_model': 'sale.order',
            'res_id': new_order.id,
            'view_mode': 'form',
        }

    @api.model
    def _cron_flag_renewal_opportunities(self):
        """
        Cron job harian:
        Tandai kontrak B2B yang kadaluarsa dalam 30 hari.
        Kirim email notifikasi ke salesperson.
        """
        contracts_due = self.search([
            ('contract_type', '=', 'B2B_CONTRACT'),
            ('contract_status', '=', 'ongoing'),
            ('renewal_opportunity', '=', True),
        ])
        for contract in contracts_due:
            contract.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Renewal: Kontrak %s kadaluarsa %d hari lagi') % (
                    contract.name, contract.days_until_expiry,
                ),
                note=_('Hubungi %s untuk perpanjangan kontrak. Usage: periksa dashboard performa.') % (
                    contract.partner_id.name,
                ),
                user_id=contract.user_id.id or self.env.user.id,
            )
