from odoo import http
from odoo.http import request


class IMPCWebsiteController(http.Controller):
    """Public website controller for IMPC Microcredential Platform."""

    @http.route(['/', '/impc'], type='http', auth='public', website=True)
    def homepage(self, **kw):
        """Landing page with featured courses, stats, and CTA."""
        SlideChannel = request.env['slide.channel'].sudo()

        featured_courses = SlideChannel.search([
            ('is_published', '=', True),
            ('is_featured', '=', True),
        ], limit=6, order='create_date desc')

        # Fallback: if no featured, show latest published
        if not featured_courses:
            featured_courses = SlideChannel.search([
                ('is_published', '=', True),
            ], limit=6, order='create_date desc')

        # Stats
        total_courses = SlideChannel.search_count([('is_published', '=', True)])
        total_students = request.env['slide.channel.partner'].sudo().search_count([
            ('member_status', 'in', ['joined', 'ongoing', 'completed']),
        ])
        total_certificates = request.env['impc.certificate'].sudo().search_count([
            ('state', '=', 'issued'),
        ])

        # Categories (tags)
        categories = request.env['slide.channel.tag'].sudo().search([], limit=8)

        values = {
            'featured_courses': featured_courses,
            'total_courses': total_courses,
            'total_students': total_students,
            'total_certificates': total_certificates,
            'categories': categories,
        }
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

        values = {
            **result,
            'search': search,
            'category': category,
            'level': level,
            'mode': mode,
            'sort': sort,
            'all_categories': all_categories,
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

        # Check if current user is enrolled
        is_enrolled = False
        enrollment = None
        if not request.env.user._is_public():
            enrollment = request.env['slide.channel.partner'].sudo().search([
                ('channel_id', '=', course.id),
                ('partner_id', '=', request.env.user.partner_id.id),
            ], limit=1)
            is_enrolled = bool(enrollment)

        # Course content (slides grouped by category)
        categories = request.env['slide.slide'].sudo().search([
            ('channel_id', '=', course.id),
            ('is_category', '=', True),
        ], order='sequence')

        slides = request.env['slide.slide'].sudo().search([
            ('channel_id', '=', course.id),
            ('is_category', '=', False),
            ('is_published', '=', True),
        ], order='sequence')

        # Related courses
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
        }
        return request.render('impc_website.course_detail', values)

    @http.route(['/pricing', '/impc/pricing'], type='http', auth='public', website=True, sitemap=True)
    def pricing(self, **kw):
        """Pricing packages page."""
        return request.render('impc_website.pricing_page', {})

    @http.route(['/about', '/impc/about'], type='http', auth='public', website=True, sitemap=True)
    def about(self, **kw):
        """About IMPC page."""
        return request.render('impc_website.about_page', {})

    @http.route(['/faq', '/impc/faq'], type='http', auth='public', website=True, sitemap=True)
    def faq(self, **kw):
        """FAQ page."""
        return request.render('impc_website.faq_page', {})

    @http.route(['/corporate-training', '/impc/corporate-training'], type='http', auth='public', website=True, sitemap=True)
    def corporate_training(self, **kw):
        """Corporate/B2B training page."""
        return request.render('impc_website.corporate_page', {})

    @http.route([
        '/verify-certificate',
        '/impc/verify',
        '/impc/verify-certificate',
    ], type='http', auth='public', website=True, sitemap=True)
    def verify_certificate_form(self, code=None, **kw):
        """Certificate verification form page. Also handles ?code= query param."""
        if code:
            return request.redirect(f'/verify-certificate/{code}')
        return request.render('impc_website.verify_certificate_form', {})

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
        return request.render('impc_website.verify_certificate_result', values)
