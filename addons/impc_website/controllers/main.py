from odoo import http
from odoo.http import request


class IMPCWebsiteController(http.Controller):
    """Public website controller for IMPC Microcredential Platform."""

    def _get_auth_data(self):
        """Return auth-related context for all public templates."""
        is_authenticated = not request.env.user._is_public()
        return {
            'is_authenticated': is_authenticated,
        }

    def _get_portal_data(self):
        """Return personalized data for authenticated users on public pages."""
        partner = request.env.user.partner_id
        enrollments = request.env['slide.channel.partner'].sudo().search([
            ('partner_id', '=', partner.id),
            ('member_status', 'in', ['joined', 'ongoing', 'completed']),
        ], order='create_date desc')
        in_progress = enrollments.filtered(lambda e: e.member_status in ('joined', 'ongoing'))
        completed = enrollments.filtered(lambda e: e.member_status == 'completed')
        certificates = request.env['impc.certificate'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', '=', 'issued'),
        ])
        continue_course = in_progress[:1] if in_progress else None
        return {
            'enrollments': enrollments,
            'in_progress': in_progress,
            'completed': completed,
            'certificates': certificates,
            'continue_course': continue_course,
            'total_in_progress': len(in_progress),
            'total_completed': len(completed),
        }

    @http.route(['/', '/impc'], type='http', auth='public', website=True)
    def homepage(self, **kw):
        """Landing page with featured courses, stats, and CTA.
        Auth-aware: shows marketing content for guests, dashboard for logged-in users.
        """
        SlideChannel = request.env['slide.channel'].sudo()
        is_authenticated = not request.env.user._is_public()

        featured_courses = SlideChannel.search([
            ('is_published', '=', True),
            ('is_featured', '=', True),
        ], limit=6, order='create_date desc')

        if not featured_courses:
            featured_courses = SlideChannel.search([
                ('is_published', '=', True),
            ], limit=6, order='create_date desc')

        total_courses = SlideChannel.search_count([('is_published', '=', True)])
        total_students = request.env['slide.channel.partner'].sudo().search_count([
            ('member_status', 'in', ['joined', 'ongoing', 'completed']),
        ])
        total_certificates = request.env['impc.certificate'].sudo().search_count([
            ('state', '=', 'issued'),
        ])
        categories = request.env['slide.channel.tag'].sudo().search([], limit=8)

        values = {
            'featured_courses': featured_courses,
            'total_courses': total_courses,
            'total_students': total_students,
            'total_certificates': total_certificates,
            'categories': categories,
            'is_authenticated': is_authenticated,
            'enrolled_ids': [],
        }

        if is_authenticated:
            values.update(self._get_portal_data())
            values['enrolled_ids'] = [e.channel_id.id for e in values['enrollments']]

        return request.render('impc_website.homepage', values)

    @http.route(['/courses', '/impc/courses'], type='http', auth='public', website=True, sitemap=True)
    def courses(self, search='', category=None, level=None, mode=None, sort='newest', page=1, **kw):
        """Course catalog with search, filter, and pagination."""
        SlideChannel = request.env['slide.channel'].sudo()
        result = SlideChannel.search_published_courses(
            search=search, category=category, level=level,
            mode=mode, sort=sort, page=page,
        )

        all_categories = request.env['slide.channel.tag'].sudo().search([])

        is_authenticated = not request.env.user._is_public()
        enrolled_ids = []
        if is_authenticated:
            enrollments = request.env['slide.channel.partner'].sudo().search([
                ('partner_id', '=', request.env.user.partner_id.id),
                ('member_status', 'in', ['joined', 'ongoing', 'completed']),
            ])
            enrolled_ids = [e.channel_id.id for e in enrollments]

        values = {
            **result,
            'search': search,
            'category': category,
            'level': level,
            'mode': mode,
            'sort': sort,
            'all_categories': all_categories,
            'is_authenticated': is_authenticated,
            'enrolled_ids': enrolled_ids,
        }
        return request.render('impc_website.courses_catalog', values)

    @http.route([
        '/courses/<model("slide.channel"):course>',
        '/impc/courses/<model("slide.channel"):course>',
    ], type='http', auth='public', website=True, sitemap=True)
    def course_detail(self, course, **kw):
        """Single course detail page with syllabus, pricing, and enrollment."""
        if not course.is_published and not request.env.user.has_group('website.group_website_designer'):
            return request.redirect('/courses')

        is_authenticated = not request.env.user._is_public()
        is_enrolled = False
        enrollment = None
        if is_authenticated:
            enrollment = request.env['slide.channel.partner'].sudo().search([
                ('channel_id', '=', course.id),
                ('partner_id', '=', request.env.user.partner_id.id),
            ], limit=1)
            is_enrolled = bool(enrollment)

        categories = request.env['slide.slide'].sudo().search([
            ('channel_id', '=', course.id),
            ('is_category', '=', True),
        ], order='sequence')

        slides = request.env['slide.slide'].sudo().search([
            ('channel_id', '=', course.id),
            ('is_category', '=', False),
            ('is_published', '=', True),
        ], order='sequence')

        related_courses = request.env['slide.channel'].sudo().search([
            ('is_published', '=', True),
            ('id', '!=', course.id),
            ('tag_ids', 'in', course.tag_ids.ids),
        ], limit=3)

        values = {
            'course': course,
            'is_enrolled': is_enrolled,
            'enrollment': enrollment,
            'categories': categories,
            'slides': slides,
            'related_courses': related_courses,
            'is_authenticated': is_authenticated,
        }
        return request.render('impc_website.course_detail', values)

    @http.route(['/pricing', '/impc/pricing'], type='http', auth='public', website=True, sitemap=True)
    def pricing(self, **kw):
        """Pricing packages page."""
        values = self._get_auth_data()
        return request.render('impc_website.pricing_page', values)

    @http.route(['/about', '/impc/about'], type='http', auth='public', website=True, sitemap=True)
    def about(self, **kw):
        """About IMPC page."""
        values = self._get_auth_data()
        return request.render('impc_website.about_page', values)

    @http.route(['/faq', '/impc/faq'], type='http', auth='public', website=True, sitemap=True)
    def faq(self, **kw):
        """FAQ page."""
        values = self._get_auth_data()
        return request.render('impc_website.faq_page', values)

    @http.route(['/corporate-training', '/impc/corporate-training'], type='http', auth='public', website=True, sitemap=True)
    def corporate_training(self, **kw):
        """Corporate/B2B training page."""
        values = self._get_auth_data()
        return request.render('impc_website.corporate_page', values)

    @http.route(['/contact', '/impc/contact'], type='http', auth='public', website=True, sitemap=True)
    def contact(self, inquiry=None, **kw):
        """Contact page with CRM lead form."""
        values = {
            **self._get_auth_data(),
            'inquiry': inquiry or kw.get('inquiry') or request.params.get('inquiry'),
        }
        return request.render('impc_website.contact_page', values)

    @http.route([
        '/verify-certificate',
        '/impc/verify',
        '/impc/verify-certificate',
    ], type='http', auth='public', website=True, sitemap=True)
    def verify_certificate_form(self, code=None, **kw):
        """Certificate verification form page. Also handles ?code= query param."""
        if code:
            return request.redirect(f'/verify-certificate/{code}')
        values = self._get_auth_data()
        return request.render('impc_website.verify_certificate_form', values)

    @http.route([
        '/verify-certificate/<string:code>',
        '/impc/verify/<string:code>',
        '/impc/verify-certificate/<string:code>',
    ], type='http', auth='public', website=True)
    def verify_certificate(self, code, **kw):
        """Certificate verification result page."""
        certificate = request.env['impc.certificate'].sudo().search([
            ('verification_code', '=', code),
            ('state', '!=', 'draft'),
        ], limit=1)

        values = {
            'certificate': certificate,
            'code': code,
            'found': bool(certificate),
            'is_valid': certificate.state == 'issued' if certificate else False,
        }
        values.update(self._get_auth_data())
        return request.render('impc_website.verify_certificate_result', values)
