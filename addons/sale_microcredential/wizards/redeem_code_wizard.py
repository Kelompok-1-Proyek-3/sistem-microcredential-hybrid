# addons/sale_microcredential/wizards/redeem_code_wizard.py
import logging
from datetime import date, timedelta

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class RedeemCodeWizard(models.TransientModel):
    _name = 'sale.redeem.code.wizard'
    _description = 'Wizard: Generate Redeem Codes'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Kontrak',
        required=True,
        readonly=True,
    )
    partner_name = fields.Char(
        string='Customer',
        related='sale_order_id.partner_id.name',
        readonly=True,
    )
    total_codes = fields.Integer(
        string='Total Kode yang Akan Di-generate',
        compute='_compute_total_codes',
        readonly=True,
    )
    confirmation_note = fields.Text(
        string='Catatan Tambahan',
        help='Opsional: catatan untuk dikirim bersama email distribusi.',
    )

    @api.depends('sale_order_id')
    def _compute_total_codes(self):
        for wiz in self:
            wiz.total_codes = sum(
                wiz.sale_order_id.order_line.mapped('redeem_code_count')
            )

    def action_generate(self):
        """Generate redeem codes directly via ORM for each order line."""
        self.ensure_one()
        order = self.sale_order_id

        if self.total_codes <= 0:
            raise UserError(
                'Tidak ada jumlah kode yang valid pada line order. '
                'Pastikan kolom "Jumlah Redeem Code" sudah diisi.'
            )

        order.write({
            'redeem_codes_requested_at': fields.Datetime.now(),
            'redeem_code_batch_status': 'PENDING',
        })

        batch_model = self.env['impc.redeem.code.batch'].sudo()
        last_batch = None

        try:
            lines = order.order_line.filtered(
                lambda l: l.slide_channel_id and l.redeem_code_count > 0
            )
            for line in lines:
                expiry_date = date.today() + timedelta(days=line.redeem_code_expiry_days)

                batch = batch_model.create({
                    'name': f'{order.name} - {line.slide_channel_id.name}',
                    'course_id': line.slide_channel_id.id,
                    'partner_id': order.partner_id.id,
                    'quantity': line.redeem_code_count,
                    'expiry_date': expiry_date,
                    'state': 'draft',
                })
                batch.action_generate_codes()
                self._send_batch_email(batch, order)
                last_batch = batch

                _logger.info(
                    'Batch %s created for order %s, course %s, qty %d',
                    batch.name, order.name, line.slide_channel_id.name,
                    line.redeem_code_count,
                )

            # Update order with last batch reference and status
            order_vals = {
                'redeem_codes_generated': True,
                'redeem_codes_generated_at': fields.Datetime.now(),
                'redeem_code_batch_status': 'GENERATED',
            }
            if last_batch:
                order_vals['redeem_code_batch_id'] = last_batch.id
            order.write(order_vals)

            # Post summary message
            batch_count = len(lines)
            order.message_post(
                body=(
                    f"Redeem code berhasil di-generate. "
                    f"Total: <b>{self.total_codes}</b> kode "
                    f"dalam <b>{batch_count}</b> batch."
                )
            )

        except Exception:
            order.write({'redeem_code_batch_status': 'FAILED'})
            raise

        return {'type': 'ir.actions.act_window_close'}

    def _send_batch_email(self, batch, order):
        """Send redeem code batch email to the purchasing company."""
        template = self.env.ref(
            'sale_microcredential.email_template_redeem_code_ready',
            raise_if_not_found=False,
        )
        recipient = batch.partner_id.email or order.partner_id.email
        if not template or not recipient:
            _logger.warning(
                'Skip redeem code email for batch %s: template or recipient missing',
                batch.name,
            )
            order.message_post(
                body=(
                    f"Redeem code batch <b>{batch.name}</b> sudah dibuat, "
                    f"tetapi email notifikasi belum terkirim karena template atau email perusahaan belum tersedia."
                )
            )
            return False

        try:
            template.send_mail(
                batch.id,
                force_send=True,
                email_values={'email_to': recipient},
            )
        except Exception:
            _logger.exception(
                'Failed to send redeem code email for batch %s',
                batch.name,
            )
            order.message_post(
                body=(
                    f"Redeem code batch <b>{batch.name}</b> berhasil dibuat, "
                    f"tetapi email ke <b>{recipient}</b> gagal dikirim."
                )
            )
            return False

        order.message_post(
            body=(
                f"Email redeem code untuk batch <b>{batch.name}</b> sudah dikirim ke "
                f"<b>{recipient}</b>."
            )
        )
        return True
