# controllers/portal_hr_controller.py
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError

class HRPartnerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        if 'b2b_contract_count' in counters:
            contract_count = request.env['sale.order'].sudo().search_count([
                ('partner_id', 'child_of', partner.commercial_partner_id.id),
                ('contract_type', '=', 'B2B_CONTRACT'),
                ('contract_status', 'in', ['confirmed', 'ongoing']),
            ])
            values['b2b_contract_count'] = contract_count

        return values

    @http.route('/portal/contracts', type='http', auth='user', website=True)
    def portal_contracts_list(self, **kwargs):
        """Daftar semua kontrak B2B milik perusahaan HR manager."""
        partner = request.env.user.partner_id
        contracts = request.env['sale.order'].sudo().search([
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('contract_type', '=', 'B2B_CONTRACT'),
        ], order='contract_start_date desc')

        return request.render('microcredential_sales.portal_contracts_list', {
            'contracts': contracts,
            'page_name': 'contracts',
        })

    @http.route('/portal/contracts/<int:order_id>', type='http', auth='user', website=True)
    def portal_contract_detail(self, order_id, **kwargs):
        """Detail satu kontrak: redeem codes, jadwal hybrid (read-only), progress."""
        try:
            contract = self._document_check_access('sale.order', order_id)
        except AccessError:
            return request.redirect('/portal/contracts')

        # Ambil data jadwal hybrid (placeholder sampai Website Group selesai W-12)
        hybrid_lines = contract.order_line.filtered(
            lambda l: l.learning_mode == 'HYBRID'
        )

        return request.render('microcredential_sales.portal_contract_detail', {
            'contract': contract,
            'hybrid_lines': hybrid_lines,
            'page_name': 'contract_detail',
        })