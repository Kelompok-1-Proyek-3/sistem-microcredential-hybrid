# models/sale_order_integration.py
# Owner: Dev 2 — Integration & API Layer
# Scope: learning_mode sync, hybrid_session_summary, redeem code API client, auto-trigger on confirm
# TODO: Dev 2 mengisi file ini

# models/sale_order_integration.py
import requests
import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

REDEEM_CODE_API_URL_PARAM = 'microcredential_sales.redeem_code_api_url'
REDEEM_CODE_API_KEY_PARAM = 'microcredential_sales.redeem_code_api_key'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # ── Mode Pembelajaran (sync read-only dari course) ────────────────────────
    learning_mode = fields.Selection(
        selection=[
            ('ONLINE', 'Online'),
            ('OFFLINE', 'Offline'),
            ('HYBRID', 'Hybrid'),
        ],
        string='Mode Pembelajaran',
        compute='_compute_learning_mode',
        store=True,
        readonly=True,
        help='Otomatis diambil dari data kursus. Edit di modul eLearning.',
    )

    hybrid_session_summary = fields.Text(
        string='Ringkasan Jadwal Sesi Hybrid',
        help='Diisi otomatis dari data sesi offline Website Group jika mode = HYBRID',
        readonly=True,
        compute='_compute_hybrid_session_summary',
        store=True,
    )

    @api.depends('course_id')
    def _compute_learning_mode(self):
        """
        Sync learning_mode dari slide.channel.
        CATATAN: Field `x_learning_mode` di slide.channel dibuat oleh Website Group (W-01).
        Jika belum ada, default ke 'ONLINE'.
        """
        for line in self:
            if line.course_id and hasattr(line.course_id, 'x_learning_mode'):
                line.learning_mode = line.course_id.x_learning_mode
            else:
                line.learning_mode = 'ONLINE'   # Default sampai Website Group selesai W-01

    @api.depends('course_id', 'learning_mode')
    def _compute_hybrid_session_summary(self):
        """
        Ambil ringkasan jadwal hybrid dari Website Group (W-12).
        CATATAN: Implementasi penuh menunggu Website Group selesai endpoint sync sesi.
        Untuk sementara, kosong jika belum ada.
        """
        for line in self:
            if line.learning_mode != 'HYBRID' or not line.course_id:
                line.hybrid_session_summary = False
                continue
            # TODO: Ganti dengan API call ke Website Group ketika W-12 selesai
            # Untuk sementara, nilai dikosongkan (akan diisi manual oleh Sales)
            if not line.hybrid_session_summary:
                line.hybrid_session_summary = False


class SaleOrderRedeemIntegration(models.Model):
    _inherit = 'sale.order'

    # ── Status Redeem Code ────────────────────────────────────────────────────
    redeem_codes_generated = fields.Boolean(
        string='Redeem Code Sudah Digenerate',
        default=False,
        copy=False,
        tracking=True,
    )
    redeem_code_batch_id = fields.Char(
        string='Batch ID Redeem Code',
        copy=False,
        readonly=True,
    )
    redeem_codes_requested_at = fields.Datetime(
        string='Waktu Request Generate',
        copy=False,
        readonly=True,
    )
    redeem_codes_generated_at = fields.Datetime(
        string='Waktu Generate Berhasil',
        copy=False,
        readonly=True,
    )
    redeem_code_batch_status = fields.Selection(
        selection=[
            ('PENDING', 'Pending'),
            ('GENERATED', 'Berhasil'),
            ('FAILED', 'Gagal'),
        ],
        string='Status Batch',
        default='PENDING',
        copy=False,
        readonly=True,
        tracking=True,
    )
    redeem_code_csv_url = fields.Char(
        string='URL Download CSV Redeem Code',
        copy=False,
        readonly=True,
    )

    # ── Tombol Trigger Manual ────────────────────────────────────────────────
    def action_open_redeem_code_wizard(self):
        """Buka wizard untuk trigger/retry generate redeem code."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generate Redeem Code',
            'res_model': 'redeem.code.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id},
        }

    def _call_redeem_code_api(self, course_id, quantity, expiry_days):
        """
        Panggil API Website Group untuk generate redeem code.
        
        Returns:
            dict: Response dari API {'batch_id', 'codes_generated', 'csv_url', 'status'}
        Raises:
            UserError: Jika API tidak dapat dihubungi atau response error
        """
        api_url = self.env['ir.config_parameter'].sudo().get_param(
            REDEEM_CODE_API_URL_PARAM, 
            default='http://localhost:8069/api/v1/elearning/redeem-codes/generate'
        )
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            REDEEM_CODE_API_KEY_PARAM,
            default=''
        )

        if not api_key:
            raise UserError(_(
                'API key untuk redeem code belum dikonfigurasi. '
                'Set parameter: %s'
            ) % REDEEM_CODE_API_KEY_PARAM)

        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
        }
        payload = {
            'course_id': course_id,
            'quantity': quantity,
            'contract_id': self.id,
            'contract_reference': self.name,
            'expiry_days': expiry_days,
            'requested_by': self.env.user.login,
        }

        try:
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise UserError(_('Timeout saat menghubungi API redeem code. Silakan coba lagi.'))
        except requests.exceptions.ConnectionError:
            raise UserError(_('Tidak dapat terhubung ke API redeem code. Periksa koneksi jaringan.'))
        except requests.exceptions.HTTPError as e:
            raise UserError(_('API error: %s') % str(e))

    def action_generate_redeem_codes_auto(self):
        """
        Auto-trigger dari contract confirmation.
        Dipanggil setelah action_confirm() berhasil untuk B2B.
        """
        self.ensure_one()
        if self.contract_type != 'B2B_CONTRACT':
            return

        b2b_lines = self.order_line.filtered(
            lambda l: l.course_id and l.redeem_code_count > 0
        )
        if not b2b_lines:
            _logger.warning(
                'Sale Order %s dikonfirmasi sebagai B2B tapi tidak ada line dengan redeem code.',
                self.name,
            )
            return

        self.redeem_codes_requested_at = fields.Datetime.now()
        self.redeem_code_batch_status = 'PENDING'

        # Ambil line pertama sebagai referensi (1 course per contract untuk saat ini)
        # TODO: Extend untuk multi-course jika diperlukan
        line = b2b_lines[0]

        # Buat log audit
        log = self.env['redeem.code.request.log'].create({
            'sale_order_id': self.id,
            'course_id': line.course_id.id,
            'quantity_requested': line.redeem_code_count,
            'expiry_days': line.redeem_code_expiry_days,
            'status': 'PENDING',
            'requested_at': fields.Datetime.now(),
        })

        retry_count = 0
        max_retries = 3
        last_error = None

        while retry_count < max_retries:
            try:
                result = self._call_redeem_code_api(
                    course_id=line.course_id.id,
                    quantity=line.redeem_code_count,
                    expiry_days=line.redeem_code_expiry_days,
                )
                # Berhasil
                self.redeem_codes_generated = True
                self.redeem_code_batch_id = result.get('batch_id')
                self.redeem_codes_generated_at = fields.Datetime.now()
                self.redeem_code_batch_status = 'GENERATED'
                self.redeem_code_csv_url = result.get('csv_url')

                log.write({
                    'status': 'SUCCESS',
                    'batch_id': result.get('batch_id'),
                    'response_payload': str(result),
                    'completed_at': fields.Datetime.now(),
                })
                self.message_post(
                    body=_('Redeem code berhasil digenerate. Batch ID: %s') % result.get('batch_id'),
                )
                return
            except UserError as e:
                last_error = str(e)
                retry_count += 1
                _logger.warning(
                    'Percobaan %d/3 generate redeem code gagal untuk %s: %s',
                    retry_count, self.name, last_error,
                )

        # Semua retry gagal
        self.redeem_code_batch_status = 'FAILED'
        log.write({
            'status': 'FAILED',
            'error_message': last_error,
            'completed_at': fields.Datetime.now(),
        })
        self.message_post(
            body=_('GAGAL generate redeem code setelah 3 percobaan. Error: %s. Gunakan tombol Retry manual.') % last_error,
            subtype_xmlid='mail.mt_comment',
        )
        
    def action_confirm(self):
        """Override untuk auto-trigger redeem code generate setelah confirm B2B."""
        result = super().action_confirm()
        for order in self.filtered(lambda o: o.contract_type == 'B2B_CONTRACT'):
            # Auto trigger generate redeem code
            try:
                order.action_generate_redeem_codes_auto()
            except Exception as e:
                # Jangan batalkan konfirmasi, log saja
                _logger.error(
                    'Auto-generate redeem code gagal untuk %s: %s',
                    order.name, str(e),
                )
                order.message_post(
                    body=_('Perhatian: Auto-generate redeem code gagal. Silakan trigger manual.'),
                )
        return result    