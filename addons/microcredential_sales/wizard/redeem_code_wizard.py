# wizard/redeem_code_wizard.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RedeemCodeWizard(models.TransientModel):
    _name = 'redeem.code.wizard'
    _description = 'Wizard Generate / Retry Redeem Code'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        readonly=True,
    )
    course_id = fields.Many2one(
        comodel_name='slide.channel',
        string='Kursus',
        required=True,
    )
    quantity = fields.Integer(
        string='Jumlah Redeem Code',
        required=True,
        default=1,
    )
    expiry_days = fields.Integer(
        string='Masa Berlaku (hari)',
        required=True,
        default=90,
    )
    note = fields.Text(string='Catatan')

    @api.onchange('sale_order_id')
    def _onchange_sale_order(self):
        order = self.sale_order_id
        if order and order.order_line:
            b2b_line = order.order_line.filtered(lambda l: l.course_id)[0:1]
            if b2b_line:
                self.course_id = b2b_line.course_id
                self.quantity = b2b_line.redeem_code_count or b2b_line.student_count
                self.expiry_days = b2b_line.redeem_code_expiry_days

    def action_execute(self):
        """Jalankan generate redeem code secara manual."""
        self.ensure_one()
        order = self.sale_order_id
        if not order:
            raise UserError(_('Sale order tidak ditemukan.'))

        result = order._call_redeem_code_api(
            course_id=self.course_id.id,
            quantity=self.quantity,
            expiry_days=self.expiry_days,
        )

        order.redeem_codes_generated = True
        order.redeem_code_batch_id = result.get('batch_id')
        order.redeem_code_batch_status = 'GENERATED'
        order.redeem_code_csv_url = result.get('csv_url')

        # Log audit
        self.env['redeem.code.request.log'].create({
            'sale_order_id': order.id,
            'course_id': self.course_id.id,
            'quantity_requested': self.quantity,
            'expiry_days': self.expiry_days,
            'status': 'SUCCESS',
            'batch_id': result.get('batch_id'),
            'response_payload': str(result),
            'requested_at': fields.Datetime.now(),
            'completed_at': fields.Datetime.now(),
        })

        order.message_post(
            body=_('Redeem code digenerate manual. Batch ID: %s. Oleh: %s. Catatan: %s') % (
                result.get('batch_id'), self.env.user.name, self.note or '-'
            ),
        )

        return {'type': 'ir.actions.act_window_close'}