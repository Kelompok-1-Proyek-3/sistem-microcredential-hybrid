from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError


class IMPCRedeemController(http.Controller):
    """Redeem voucher controller for IMPC Microcredential Platform."""

    @http.route(['/my-learning/redeem', '/impc/my-learning/redeem'], type='http', auth='user', website=True)
    def redeem_form(self, **kw):
        """Redeem voucher form page."""
        values = {
            'success': kw.get('success'),
            'error': kw.get('error'),
            'course_name': kw.get('course_name'),
        }
        return request.render('impc_website.portal_redeem_voucher', values)

    @http.route([
        '/my-learning/redeem/submit',
        '/impc/my-learning/redeem/submit',
    ], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def redeem_submit(self, code='', **kw):
        """Process voucher redemption."""
        if not code or not code.strip():
            return request.redirect('/my-learning/redeem?error=Please+enter+a+redeem+code.')

        code = code.strip().upper()
        partner = request.env.user.partner_id

        redeem_code = request.env['impc.redeem.code'].sudo().search([
            ('code', '=', code),
        ], limit=1)

        if not redeem_code:
            return request.redirect('/my-learning/redeem?error=Invalid+code.+Please+check+and+try+again.')

        # Validate
        validation = redeem_code.action_validate(partner)
        if not validation['valid']:
            error_msg = validation['message'].replace(' ', '+')
            return request.redirect(f'/my-learning/redeem?error={error_msg}')

        # Claim
        try:
            redeem_code.action_claim(partner)
            course_name = redeem_code.course_id.name or 'Course'
            return request.redirect(
                f'/my-learning/redeem?success=1&course_name={course_name.replace(" ", "+")}'
            )
        except ValidationError as e:
            error_msg = str(e).replace(' ', '+')
            return request.redirect(f'/my-learning/redeem?error={error_msg}')

    @http.route([
        '/my-learning/redeem/validate',
        '/impc/my-learning/redeem/validate',
    ], type='json', auth='user', website=True)
    def redeem_validate_ajax(self, code='', **kw):
        """AJAX endpoint for real-time code validation."""
        if not code or not code.strip():
            return {'valid': False, 'message': 'Please enter a redeem code.'}

        code = code.strip().upper()
        partner = request.env.user.partner_id

        redeem_code = request.env['impc.redeem.code'].sudo().search([
            ('code', '=', code),
        ], limit=1)

        if not redeem_code:
            return {'valid': False, 'message': 'Invalid code. Please check and try again.'}

        validation = redeem_code.action_validate(partner)
        if validation['valid']:
            return {
                'valid': True,
                'message': 'Code is valid!',
                'course_name': redeem_code.course_id.name,
                'course_id': redeem_code.course_id.id,
            }
        return validation
