import logging
import requests
from odoo import models, api, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

REDEEM_API_PATH = '/api/v1/elearning/redeem-codes/generate'
TIMEOUT_SECONDS = 15


class RedeemCodeService(models.AbstractModel):
    """
    Service layer untuk integrasi API dengan Website Group.
    Dipanggil dari wizard atau workflow action.
    """
    _name = 'sale.redeem.code.service'
    _description = 'Redeem Code API Service'

    @api.model
    def generate_codes(self, sale_order, course_id, quantity, expiry_days):
        """
        Kirim POST request ke Website API untuk generate redeem codes.

        :param sale_order: record sale.order
        :param course_id: int, ID dari slide.channel
        :param quantity: int, jumlah kode
        :param expiry_days: int, masa berlaku kode
        :return: dict response dari API atau raise UserError
        """
        # Mock support untuk development/testing lokal
        if self.env['ir.config_parameter'].sudo().get_param('sale_microcredential.mock_api') == 'True':
            _logger.info('Using mock redeem code response for order %s', sale_order.name)
            data = {
                'status': 'SUCCESS',
                'batch_id': f'MOCK-{sale_order.id}',
                'codes_generated': quantity,
                'csv_url': '#',
            }
            # update order as if success
            sale_order.write({
                'redeem_codes_generated': True,
                'redeem_code_batch_id': data.get('batch_id'),
                'redeem_codes_generated_at': fields.Datetime.now(),
                'redeem_code_batch_status': 'GENERATED',
            })
            sale_order.message_post(
                body=(
                    f"✅ (MOCK) Redeem code berhasil di-generate. Batch ID: <b>{data.get('batch_id')}</b>, Jumlah: <b>{data.get('codes_generated')}</b>"
                )
            )
            return data

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'sale_microcredential.website_api_key'
        )
        if not api_key:
            raise UserError(
                'API Key untuk Website tidak ditemukan. Hubungi administrator untuk setup di Settings → Technical → Parameters.'
            )

        url = f"{base_url.rstrip('/')}{REDEEM_API_PATH}"
        payload = {
            'course_id': course_id,
            'quantity': quantity,
            'contract_id': sale_order.id,
            'contract_reference': sale_order.name,
            'expiry_days': expiry_days,
            'requested_by': self.env.user.login,
        }
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout:
            _logger.error('Timeout saat request redeem code untuk order %s', sale_order.name)
            raise UserError(
                'Request timeout. Coba lagi dalam beberapa menit. Jika terus gagal, gunakan tombol Retry (maks 3x).'
            )
        except requests.exceptions.RequestException as exc:
            _logger.error('Error request redeem code: %s', exc)
            raise UserError(f'Gagal terhubung ke Website API: {exc}')

        if data.get('status') != 'SUCCESS':
            raise UserError(f"Website API merespons error: {data.get('message', 'Unknown error')}")

        # Update sale.order setelah berhasil
        sale_order.write({
            'redeem_codes_generated': True,
            'redeem_code_batch_id': data.get('batch_id'),
            'redeem_codes_generated_at': fields.Datetime.now(),
            'redeem_code_batch_status': 'GENERATED',
        })
        sale_order.message_post(
            body=(
                f"✅ Redeem code berhasil di-generate. Batch ID: <b>{data.get('batch_id')}</b>, Jumlah: <b>{data.get('codes_generated')}</b>"
            )
        )
        _logger.info(
            'Redeem codes generated for order %s, batch_id=%s',
            sale_order.name,
            data.get('batch_id'),
        )
        return data
