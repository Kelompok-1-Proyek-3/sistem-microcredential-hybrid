# addons/sale_microcredential/controllers/portal_contract.py
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class HRPartnerPortal(CustomerPortal):
    """
    Portal controller untuk HR partner B2B.
    Extends CustomerPortal agar dapat menggunakan /my/ routes.
    """

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'contract_count' in counters:
            domain = self._get_contracts_domain()
            values['contract_count'] = request.env['sale.order'].search_count(domain)
        return values

    def _get_contracts_domain(self):
        """Domain filter: hanya tampilkan kontrak milik partner yang login."""
        partner = request.env.user.partner_id
        return [
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('contract_type', '=', 'B2B_CONTRACT'),
            ('state', 'in', ['sale', 'done']),
        ]

    @http.route(['/my/contracts', '/my/contracts/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_contracts(self, page=1, **kw):
        domain = self._get_contracts_domain()
        Contract = request.env['sale.order']
        contract_count = Contract.search_count(domain)

        pager = portal_pager(
            url='/my/contracts',
            total=contract_count,
            page=page,
            step=10,
        )
        contracts = Contract.search(domain, limit=10, offset=pager['offset'],
                                    order='date_order desc')
        return request.render(
            'sale_microcredential.portal_my_contracts',
            {'contracts': contracts, 'pager': pager, 'page_name': 'contract'},
        )

    @http.route('/my/contracts/<int:order_id>', type='http', auth='user', website=True)
    def portal_contract_detail(self, order_id, **kw):
        order = request.env['sale.order'].browse(order_id)
        # Security check: pastikan partner yang login boleh lihat kontrak ini
        if order.partner_id.commercial_partner_id != request.env.user.partner_id.commercial_partner_id:
            return request.redirect('/my/contracts')
        return request.render(
            'sale_microcredential.portal_contract_detail',
            {'order': order, 'page_name': 'contract'},
        )

    @http.route('/my/contracts/<int:order_id>/redeem-codes',
                type='http', auth='user', website=True)
    def portal_contract_redeem_codes(self, order_id, **kw):
        order = request.env['sale.order'].browse(order_id)
        # Security check
        if order.partner_id.commercial_partner_id != request.env.user.partner_id.commercial_partner_id:
            return request.redirect('/my/contracts')
        return request.render(
            'sale_microcredential.portal_redeem_codes',
            {'order': order, 'page_name': 'contract'},
        )