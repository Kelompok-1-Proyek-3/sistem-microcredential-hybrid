"""
IMPC Website Controllers
"""

from odoo import http
from odoo.http import request


class ImpcPublicController(http.Controller):
    """Public website routes for IMPC"""

    @http.route('/impc', type='http', auth='public', website=True)
    def homepage(self, **kwargs):
        """GET /impc - Public homepage with featured courses"""
        context = {}
        
        try:
            # Get featured courses (limit to 6)
            courses = request.env['elearning.course'].sudo().search(
                [],
                order='create_date desc',
                limit=6
            )
            context['courses'] = courses
        except KeyError:
            context['courses'] = []
        
        try:
            # Get course categories
            categories = request.env['elearning.category'].sudo().search([])
            context['categories'] = categories
        except KeyError:
            context['categories'] = []
        
        try:
            # Get stats
            total_courses = request.env['elearning.course'].sudo().search_count([])
            context['total_courses'] = total_courses
        except KeyError:
            context['total_courses'] = 0
        
        try:
            # Get total students (count partners with student category or check enrollments)
            total_students = request.env['elearning.enrollment'].sudo().search_count([])
            context['total_students'] = total_students
        except KeyError:
            context['total_students'] = 0
        
        # Try to render - with fallback to plain response for debugging
        try:
            return request.render('impc_website.impc_homepage', context)
        except Exception as e:
            # If template not found, return debug info
            return f"<h1>DEBUG: Template Error</h1><p>Error: {str(e)}</p><p>Context: {context}</p>"

    @http.route('/impc/courses', type='http', auth='public', website=True)
    def courses(self, **kwargs):
        """GET /impc/courses - Course catalog with search/filter/sort"""
        context = {}
        
        # Get search/filter/sort parameters
        search_query = kwargs.get('search', '')
        category_id = kwargs.get('category', '')
        difficulty = kwargs.get('difficulty', '')
        sort = kwargs.get('sort', 'newest')
        
        try:
            # Build domain for search
            domain = []
            if search_query:
                domain.append(('name', 'ilike', search_query))
            
            if category_id:
                try:
                    category_id = int(category_id)
                    domain.append(('category_id', '=', category_id))
                except (ValueError, TypeError):
                    pass
            
            if difficulty:
                domain.append(('difficulty', '=', difficulty))
            
            # Determine sort order
            order = 'create_date desc'
            if sort == 'popular':
                order = 'student_count desc'
            elif sort == 'rating':
                order = 'average_rating desc'
            elif sort == 'name':
                order = 'name asc'
            
            # Query courses
            courses = request.env['elearning.course'].sudo().search(
                domain,
                order=order
            )
            context['courses'] = courses
        except KeyError:
            context['courses'] = []
        
        try:
            # Get all categories for filter dropdown
            categories = request.env['elearning.category'].sudo().search([])
            context['categories'] = categories
        except KeyError:
            context['categories'] = []
        
        # Get current filters/search for template
        context['search_query'] = search_query
        context['current_category'] = category_id if category_id else ''
        context['current_difficulty'] = difficulty if difficulty else ''
        context['current_sort'] = sort
        
        return request.render('impc_website.impc_courses', context)

    @http.route('/impc/dashboard', type='http', auth='user', website=True)
    def dashboard(self, **kwargs):
        """GET /impc/dashboard - Student dashboard (auth required)"""
        user = request.env.user
        context = {'user': user}
        
        try:
            # Get enrolled courses for current user
            enrollments = request.env['elearning.enrollment'].sudo().search(
                [('student_id', '=', user.partner_id.id)]
            )
            enrolled_courses = enrollments.mapped('course_id')
            context['enrolled_courses'] = enrolled_courses
            context['total_enrolled'] = len(enrollments)
            context['in_progress'] = len(enrollments.filtered(lambda e: not hasattr(e, 'completion_date') or not e.completion_date))
        except KeyError:
            context['enrolled_courses'] = []
            context['total_enrolled'] = 0
            context['in_progress'] = 0
        
        try:
            # Get completed certificates
            certificates = request.env['elearning.certificate'].sudo().search(
                [('student_id', '=', user.partner_id.id)]
            )
            context['certificates'] = certificates
            context['total_completed'] = len(certificates)
        except KeyError:
            context['certificates'] = []
            context['total_completed'] = 0
        
        return request.render('impc_website.impc_dashboard', context)
