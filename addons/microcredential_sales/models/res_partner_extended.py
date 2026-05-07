# models/res_partner_extended.py
# Owner: Dev 3 — CRM, Portal & Dashboard
# Scope: Extended fields pada res.partner untuk HR partner (industri, karyawan, anggaran training)
# TODO: Dev 3 mengisi file ini

from odoo import models, fields


class ResPartnerExtended(models.Model):
    _inherit = 'res.partner'

    # ── Tipe Perusahaan ───────────────────────────────────────────────────────
    company_type_microcredential = fields.Selection(
        selection=[
            ('INDIVIDUAL', 'Individual'),
            ('CORPORATE_HR', 'Perusahaan – Departemen HR'),
            ('CORPORATE_OTHER', 'Perusahaan – Lainnya'),
        ],
        string='Tipe Partner (Microcredential)',
        default='INDIVIDUAL',
    )
    industry_type = fields.Selection(
        selection=[
            ('TECH', 'Teknologi'),
            ('FINANCE', 'Keuangan'),
            ('MANUFACTURING', 'Manufaktur'),
            ('EDUCATION', 'Pendidikan'),
            ('OTHER', 'Lainnya'),
        ],
        string='Industri',
    )
    employee_count = fields.Integer(
        string='Jumlah Karyawan',
    )
    training_budget_annual = fields.Float(
        string='Anggaran Training Tahunan (IDR)',
    )
    is_hr_partner_admin = fields.Boolean(
        string='Admin HR Portal',
        default=False,
        help='Jika True, user portal ini bisa lihat semua kontrak perusahaannya',
    )
    hr_contract_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='partner_id',
        string='Kontrak B2B',
        domain=[('contract_type', '=', 'B2B_CONTRACT')],
    )
