import json

from odoo import http
from odoo.http import request, Response


class IMPCApiController(http.Controller):
    """External API controller for IMPC Microcredential Platform."""

    # ================================================================
    # Certificate Verification API (Public)
    # ================================================================

    @http.route('/api/v1/certificate/verify/<string:code>', type='http', auth='public',
                methods=['GET'], csrf=False, cors='*')
    def api_verify_certificate(self, code, **kw):
        """Public API endpoint for certificate verification.

        Returns JSON with certificate details if valid.
        """
        certificate = request.env['impc.certificate'].sudo().search([
            ('verification_code', '=', code),
            ('state', '!=', 'draft'),
        ], limit=1)

        if not certificate:
            return Response(
                json.dumps({
                    'status': 'error',
                    'message': 'Certificate not found.',
                    'code': code,
                }),
                content_type='application/json',
                status=404,
            )

        if certificate.state == 'revoked':
            return Response(
                json.dumps({
                    'status': 'revoked',
                    'message': 'This certificate has been revoked.',
                    'code': code,
                    'certificate_number': certificate.name,
                }),
                content_type='application/json',
                status=200,
            )

        data = {
            'status': 'valid',
            'message': 'Certificate is valid and verified.',
            'certificate': {
                'number': certificate.name,
                'verification_code': certificate.verification_code,
                'student_name': certificate.partner_id.name,
                'course_name': certificate.channel_id.name,
                'completion_date': certificate.completion_date.isoformat() if certificate.completion_date else None,
                'state': certificate.state,
                'issued_by': 'IMPC - Indonesia Microcredential Platform Center',
            },
        }
        return Response(
            json.dumps(data),
            content_type='application/json',
            status=200,
        )

    # ================================================================
    # Redeem Code Validation API (Authenticated)
    # ================================================================

    @http.route('/api/v1/redeem/validate', type='json', auth='user', methods=['POST'])
    def api_validate_redeem_code(self, **kw):
        """Validate a redeem code via API.

        Request body: {"code": "IMPC-XXXX-XXXX-XXXX"}
        """
        code = kw.get('code', '').strip().upper()
        if not code:
            return {'status': 'error', 'message': 'Code is required.'}

        redeem_code = request.env['impc.redeem.code'].sudo().search([
            ('code', '=', code),
        ], limit=1)

        if not redeem_code:
            return {'status': 'error', 'message': 'Invalid code.'}

        partner = request.env.user.partner_id
        validation = redeem_code.action_validate(partner)

        return {
            'status': 'valid' if validation['valid'] else 'error',
            'message': validation['message'],
            'course_name': redeem_code.course_id.name if validation['valid'] else None,
            'course_id': redeem_code.course_id.id if validation['valid'] else None,
            'expiry_date': str(redeem_code.expiry_date) if validation['valid'] else None,
        }

    # ================================================================
    # Redeem Code Bulk Generation API (Internal/Sales Group)
    # ================================================================

    @http.route('/api/v1/redeem/generate', type='json', auth='user', methods=['POST'])
    def api_generate_redeem_codes(self, **kw):
        """Bulk generate redeem codes (for Sales Group).

        Request body:
        {
            "course_id": 1,
            "quantity": 100,
            "expiry_date": "2025-12-31",
            "partner_id": 5,  // B2B company (optional)
            "batch_name": "Batch ABC Corp Q1"
        }

        Requires IMPC Manager group.
        """
        # Check permissions
        if not request.env.user.has_group('impc_website.group_impc_manager'):
            return {
                'status': 'error',
                'message': 'Insufficient permissions. IMPC Manager role required.',
            }

        course_id = kw.get('course_id')
        quantity = kw.get('quantity', 10)
        expiry_date = kw.get('expiry_date')
        partner_id = kw.get('partner_id')
        batch_name = kw.get('batch_name', 'API Generated Batch')

        # Validation
        if not course_id:
            return {'status': 'error', 'message': 'course_id is required.'}
        if not expiry_date:
            return {'status': 'error', 'message': 'expiry_date is required.'}
        if quantity < 1 or quantity > 10000:
            return {'status': 'error', 'message': 'quantity must be between 1 and 10000.'}

        # Verify course exists
        course = request.env['slide.channel'].sudo().browse(int(course_id))
        if not course.exists():
            return {'status': 'error', 'message': 'Course not found.'}

        # Create batch
        batch_vals = {
            'name': batch_name,
            'course_id': course.id,
            'quantity': quantity,
            'expiry_date': expiry_date,
            'state': 'draft',
        }
        if partner_id:
            batch_vals['partner_id'] = int(partner_id)

        batch = request.env['impc.redeem.code.batch'].sudo().create(batch_vals)
        batch.action_generate_codes()

        # Return generated codes
        codes = batch.code_ids.mapped('code')

        return {
            'status': 'success',
            'message': f'{len(codes)} codes generated successfully.',
            'batch_id': batch.id,
            'batch_name': batch.name,
            'course_name': course.name,
            'codes': codes,
            'expiry_date': expiry_date,
        }

    # ================================================================
    # Student Progress API (Authenticated)
    # ================================================================

    @http.route('/api/v1/student/progress', type='json', auth='user', methods=['GET'])
    def api_student_progress(self, **kw):
        """Get current student's learning progress summary."""
        partner = request.env.user.partner_id

        enrollments = request.env['slide.channel.partner'].sudo().search([
            ('partner_id', '=', partner.id),
            ('member_status', 'in', ['joined', 'ongoing', 'completed']),
        ])

        courses_data = []
        for enrollment in enrollments:
            courses_data.append({
                'course_id': enrollment.channel_id.id,
                'course_name': enrollment.channel_id.name,
                'completion': enrollment.completion,
                'member_status': enrollment.member_status,
                'enrollment_type': enrollment.enrollment_type,
                'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
                'has_certificate': bool(enrollment.certificate_id),
            })

        return {
            'status': 'success',
            'student_name': partner.name,
            'total_enrolled': len(enrollments),
            'total_completed': len(enrollments.filtered(lambda e: e.member_status == 'completed')),
            'total_in_progress': len(enrollments.filtered(lambda e: e.member_status in ('joined', 'ongoing'))),
            'courses': courses_data,
        }
