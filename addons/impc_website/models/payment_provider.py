from odoo import models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    def _get_or_create_demo_account(self, code, name, account_type):
        self.ensure_one()
        Account = self.env['account.account'].sudo().with_company(self.company_id)
        account = Account.search([
            ('code', '=', code),
            ('company_ids', 'in', self.company_id.id),
        ], limit=1)
        if account:
            return account
        return Account.create({
            'code': code,
            'name': name,
            'account_type': account_type,
            'company_ids': [(6, 0, [self.company_id.id])],
            'reconcile': account_type in ('asset_current', 'liability_current'),
        })

    def _ensure_payment_journal(self):
        self.ensure_one()
        if self.code != 'demo':
            return self
        Journal = self.env['account.journal'].sudo()
        PaymentMethod = self.env['account.payment.method']
        bank_account = self._get_or_create_demo_account(
            '101999',
            'Demo Bank',
            'asset_cash',
        )
        outstanding_account = self._get_or_create_demo_account(
            '101998',
            'Demo Outstanding Receipts',
            'asset_current',
        )
        bank_journal = self.journal_id or Journal.search([
            ('type', '=', 'bank'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        if not bank_journal:
            bank_journal = Journal.create({
                'name': 'Demo Bank',
                'type': 'bank',
                'code': 'DMBNK',
                'company_id': self.company_id.id,
                'default_account_id': bank_account.id,
            })
        elif not bank_journal.default_account_id:
            bank_journal.default_account_id = bank_account.id

        self.sudo().journal_id = bank_journal.id
        existing = self.env['account.payment.method.line'].sudo().search([
            ('payment_provider_id', '=', self.id),
            ('journal_id', '=', bank_journal.id),
        ], limit=1)
        if not existing:
            inbound_method = PaymentMethod.search([
                ('code', '=', 'manual'),
                ('payment_type', '=', 'inbound'),
            ], limit=1) or PaymentMethod.search([], limit=1)
            if inbound_method:
                bank_journal.write({
                    'inbound_payment_method_line_ids': [
                        (0, 0, {
                            'name': 'Demo',
                            'payment_method_id': inbound_method.id,
                            'payment_provider_id': self.id,
                            'payment_account_id': outstanding_account.id,
                        }),
                    ],
                })
        elif not existing.payment_account_id:
            existing.payment_account_id = outstanding_account.id
        return self
