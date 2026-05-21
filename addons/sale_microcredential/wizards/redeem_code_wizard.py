from odoo import models, fields, api
from odoo.exceptions import UserError


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
        self.ensure_one()
        order = self.sale_order_id
        service = self.env['sale.redeem.code.service']

        if self.total_codes <= 0:
            raise UserError(
                'Tidak ada jumlah kode yang valid pada line order. Pastikan kolom "Jumlah Redeem Code" sudah diisi.'
            )

        order.write({
            'redeem_codes_requested_at': fields.Datetime.now(),
            'redeem_code_batch_status': 'PENDING',
        })

        try:
            for line in order.order_line.filtered(lambda l: l.slide_channel_id and l.redeem_code_count > 0):
                service.generate_codes(
                    sale_order=order,
                    course_id=line.slide_channel_id.id,
                    quantity=line.redeem_code_count,
                    expiry_days=line.redeem_code_expiry_days,
                )
        except Exception:
            order.write({'redeem_code_batch_status': 'FAILED'})
            raise

        return {'type': 'ir.actions.act_window_close'}
