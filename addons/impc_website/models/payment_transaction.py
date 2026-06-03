import logging

from odoo import models
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _create_payment(self, **extra_create_values):
        self.provider_id._ensure_payment_journal()
        if (
            self.provider_id.code == 'demo'
            and not self.partner_id.with_company(self.company_id).property_account_receivable_id
        ):
            _logger.info(
                "Skipping accounting payment creation for demo transaction %s "
                "because the company has no receivable account configured.",
                self.reference,
            )
            return self.env['account.payment']
        try:
            return super()._create_payment(**extra_create_values)
        except UserError as error:
            if self.provider_id.code != 'demo':
                raise
            _logger.info(
                "Skipping accounting payment creation for demo transaction %s: %s",
                self.reference,
                error,
            )
            return self.env['account.payment']
