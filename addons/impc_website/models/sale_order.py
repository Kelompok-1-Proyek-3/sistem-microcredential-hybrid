from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        for order in self.filtered(lambda o: o.state == 'sale'):
            # Skip auto-enrollment for B2B contracts — handled by sale_microcredential
            contract_type = getattr(order, 'contract_type', 'B2C')
            if contract_type != 'B2B_CONTRACT':
                order._impc_create_enrollments()
        return res

    def _impc_create_enrollments(self):
        self.ensure_one()
        SlideChannel = self.env['slide.channel'].sudo()
        SlidePartner = self.env['slide.channel.partner'].sudo()
        for line in self.order_line:
            if not line.product_id:
                continue
            course = SlideChannel.search([
                ('product_id', '=', line.product_id.id),
            ], limit=1)
            if not course:
                continue
            existing = SlidePartner.search([
                ('channel_id', '=', course.id),
                ('partner_id', '=', self.partner_id.id),
            ], limit=1)
            if existing:
                if existing.enrollment_type != 'b2c_payment':
                    existing.write({'enrollment_type': 'b2c_payment'})
                continue
            SlidePartner.create({
                'channel_id': course.id,
                'partner_id': self.partner_id.id,
                'enrollment_type': 'b2c_payment',
                'member_status': 'joined',
            })
