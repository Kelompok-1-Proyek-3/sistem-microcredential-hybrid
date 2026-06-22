# addons/sale_microcredential/models/sale_order_workflow.py
import logging
from datetime import date, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrderWorkflow(models.Model):
	"""
	Extension untuk sale.order — khusus business logic dan workflow.
	Fields didefinisikan di sale_order.py (Dev 1).
	"""
	_inherit = 'sale.order'

	@api.onchange('contract_type')
	def _onchange_contract_type(self):
		"""Auto-fill contract_start_date when B2B is selected."""
		if self.contract_type == 'B2B_CONTRACT':
			if not self.contract_start_date:
				self.contract_start_date = fields.Date.today()
		else:
			self.contract_start_date = False

	@api.depends('expiry_date')
	def _compute_renewal_opportunity(self):
		from datetime import date, timedelta
		today = date.today()
		threshold = today + timedelta(days=30)
		for order in self:
			if order.expiry_date and order.expiry_date <= threshold:
				order.renewal_opportunity = True
			else:
				order.renewal_opportunity = False

	def action_request_redeem_codes(self):
		"""
		Buka wizard untuk konfirmasi request redeem code ke Website API.
		Dipanggil dari tombol di form view (Dev 3 yang buat tombolnya di XML).
		"""
		self.ensure_one()
		if self.contract_type != 'B2B_CONTRACT':
			raise UserError('Redeem code hanya untuk kontrak tipe B2B.')
		if self.redeem_codes_generated:
			raise UserError('Redeem code untuk kontrak ini sudah pernah di-generate.')

		return {
			'type': 'ir.actions.act_window',
			'name': 'Request Redeem Codes',
			'res_model': 'sale.redeem.code.wizard',
			'view_mode': 'form',
			'target': 'new',
			'context': {'default_sale_order_id': self.id},
		}

	def action_send_contract_confirmation(self):
		"""
		Kirim email konfirmasi kontrak ke customer.
		Dipanggil otomatis via server action saat state = sale.
		"""
		self.ensure_one()
		template = self.env.ref(
			'sale_microcredential.email_template_b2b_contract_confirmed',
			raise_if_not_found=False,
		)
		if template:
			template.send_mail(self.id, force_send=True)
			_logger.info('Contract confirmation email sent for order %s', self.name)

	def action_confirm(self):
		"""Override Odoo native confirm untuk trigger workflow B2B."""
		res = super().action_confirm()
		b2b_orders = self.filtered(lambda o: o.contract_type == 'B2B_CONTRACT')
		if b2b_orders:
			b2b_orders.write({'contract_start_date': fields.Date.today()})
			for order in b2b_orders:
				order.action_send_contract_confirmation()
				_logger.info('B2B Contract %s confirmed, start date set.', order.name)
		return res

	def action_retry_redeem_codes(self):
		"""
		Manual retry jika generate redeem code gagal.
		Maksimum 3 percobaan (dicatat di chatter).
		"""
		self.ensure_one()
		retry_count = self.message_ids.filtered(
			lambda m: 'RETRY_REDEEM' in (m.subject or '')
		)
		if len(retry_count) >= 3:
			raise UserError(
				'Maksimum 3 kali retry sudah tercapai. '
				'Hubungi tim Website untuk penanganan manual.'
			)
		self.message_post(
			subject='RETRY_REDEEM',
			body=f'Retry request redeem code ke-{len(retry_count) + 1}.',
		)
		return self.action_request_redeem_codes()

	@api.model
	def _cron_flag_renewal_contracts(self):
		"""
		Dipanggil oleh ir.cron setiap hari.
		Flag kontrak B2B yang expiry_date-nya <= 30 hari dari sekarang.
		"""
		today = date.today()
		threshold = today + timedelta(days=30)
		expiring = self.search([
			('state', '=', 'sale'),
			('contract_type', '=', 'B2B_CONTRACT'),
			('expiry_date', '!=', False),
			('expiry_date', '<=', threshold),
			('renewal_opportunity', '=', False),
		])
		expiring.write({'renewal_opportunity': True})
		_logger.info('Flagged %d B2B contracts for renewal.', len(expiring))
