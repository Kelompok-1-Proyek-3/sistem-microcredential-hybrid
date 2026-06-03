from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        if 'demo' not in res:
            res['demo'] = {'mode': 'multi', 'type': ('bank', 'cash')}
        return res
