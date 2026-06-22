from odoo import http
from odoo.http import request


class MarketingAdmin(http.Controller):

    def _require_admin(self):
        if request.env.user._is_public() or not request.env.user.has_group("base.group_system"):
            return request.redirect("/web/login")
        return None

    @http.route('/management/reports/conversions', type='http', auth='user', website=True)
    def report_conversions(self, **kw):
        redirect = self._require_admin()
        if redirect:
            return redirect

        reports = request.env['marketing.event.conversion.report'].sudo().search(
            [], limit=50, order='week_start desc, event_id')
        return request.render('marketing_microcredential.admin_reports_conversions', {
            'reports': reports,
            'page_name': 'reports_conversions',
        })

    @http.route('/management/reports/surveys', type='http', auth='user', website=True)
    def report_surveys(self, **kw):
        redirect = self._require_admin()
        if redirect:
            return redirect

        reports = request.env['marketing.survey.report'].sudo().search(
            [], limit=50, order='month_start desc, survey_id')
        return request.render('marketing_microcredential.admin_reports_surveys', {
            'reports': reports,
            'page_name': 'reports_surveys',
        })
