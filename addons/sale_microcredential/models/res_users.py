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
            'User harus memiliki group base.group_portal untuk dapat login ke portal. '
            'Otomatis di-set True saat user ditambahkan ke group Sales Microcredential / HR Partner.'
        ),
    )

    def write(self, vals):
        """Auto-set is_hr_partner_admin when group_hr_partner is assigned."""
        res = super().write(vals)
        if 'groups_id' in vals:
            try:
                hr_group = self.env.ref(
                    'sale_microcredential.group_hr_partner',
                    raise_if_not_found=False,
                )
            except Exception:
                hr_group = None
            if hr_group:
                cmd_ids = set()
                for cmd in vals['groups_id']:
                    if cmd[0] in (4, 6) and len(cmd) > 1:
                        if cmd[0] == 4:
                            cmd_ids.add(cmd[1])
                        elif cmd[0] == 6:
                            cmd_ids.update(cmd[2])
                if hr_group.id in cmd_ids:
                    users_to_flag = self.filtered(
                        lambda u: not u.is_hr_partner_admin
                    )
                    if users_to_flag:
                        super(ResUsers, users_to_flag).write(
                            {'is_hr_partner_admin': True}
                        )
        return res
