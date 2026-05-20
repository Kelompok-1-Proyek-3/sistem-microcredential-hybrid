# addons/sale_microcredential/models/res_partner.py
# DEV 1: Field definitions ONLY.
#
# CATATAN: is_hr_partner_admin TIDAK ada di sini.
# Field tersebut ada di res_users.py karena berkaitan dengan login/portal user,
# bukan dengan contact record (res.partner).
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_type_microcredential = fields.Selection(
        selection=[
            ('INDIVIDUAL', 'Individual'),
            ('CORPORATE_HR', 'Perusahaan - HR'),
            ('CORPORATE_OTHER', 'Perusahaan - Lainnya'),
        ],
        string='Tipe Partner',
        default='INDIVIDUAL',
    )
    industry_type = fields.Selection(
        selection=[
            ('TECH', 'Teknologi'),
            ('FINANCE', 'Keuangan'),
            ('MANUFACTURING', 'Manufaktur'),
            ('OTHER', 'Lainnya'),
        ],
        string='Industri',
    )
    employee_count = fields.Integer(
        string='Jumlah Karyawan',
    )
    training_budget_annual = fields.Float(
        string='Budget Pelatihan Tahunan (IDR)',
        digits=(16, 2),
    )
