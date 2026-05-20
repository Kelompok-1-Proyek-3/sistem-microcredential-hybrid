# addons/sale_microcredential/models/res_users.py
# DEV 1: Field definitions ONLY.
#
# KOREKSI ODOO 19: is_hr_partner_admin ada di res.users, BUKAN res.partner.
#   - Model 'account.user' TIDAK ADA di Odoo 19.
#   - Portal users = res.users dengan group base.group_portal.
#   - Field ini menandai user portal yang menjadi HR admin mitra B2B.
#
# Cara membuat portal user HR:
#   portal_group = self.env.ref('base.group_portal')
#   user = self.env['res.users'].create({
#       'name': 'HR Manager PT ABC',
#       'login': 'hr.manager@ptabc.co.id',
#       'email': 'hr.manager@ptabc.co.id',
#       'partner_id': partner_id,  # FK ke res.partner
#       'groups_id': [(4, portal_group.id)],
#       'is_hr_partner_admin': True,
#   })
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_hr_partner_admin = fields.Boolean(
        string='HR Portal Admin',
        default=False,
        help=(
            'Tandai user portal sebagai admin HR mitra B2B. '
            'Memberikan akses melihat semua kontrak & redeem code milik perusahaannya. '
            'User harus memiliki group base.group_portal untuk dapat login ke portal.'
        ),
    )
