from odoo import http
from odoo.http import request
from odoo.addons.website_event.controllers.main import WebsiteEventController


class IMPCEventController(WebsiteEventController):
    """Override event registration to require login and prevent duplicate registration."""

    @http.route()
    def registration_new(self, event, **post):
        """Override registration to require authentication and check existing registration."""
        # Check if user is logged in (not public user)
        if request.env.user._is_public():
            # Redirect to login page with return URL
            return request.redirect(
                f'/web/login?redirect=/event/{event.id}/register'
            )
        
        # Check if user is already registered for this event
        existing_registration = request.env['event.registration'].sudo().search([
            ('event_id', '=', event.id),
            ('partner_id', '=', request.env.user.partner_id.id),
            ('state', 'in', ['draft', 'open', 'done']),  # Exclude cancelled
        ], limit=1)
        
        if existing_registration:
            # User already registered, redirect to Odoo success page with their registration
            from odoo.addons.http_routing.models.ir_http import slug
            return request.redirect(
                f'/event/{slug(event)}/registration/success?registration_ids={existing_registration.id}'
            )
        
        # User is authenticated and not registered, proceed with normal registration
        return super().registration_new(event, **post)

    @http.route()
    def registration_confirm(self, event, **post):
        """Override registration confirmation to require authentication."""
        # Check if user is logged in (not public user)
        if request.env.user._is_public():
            # Redirect to login page
            return request.redirect(
                f'/web/login?redirect=/event/{event.id}/register'
            )
        
        # Check if user is already registered (double-check before confirmation)
        existing_registration = request.env['event.registration'].sudo().search([
            ('event_id', '=', event.id),
            ('partner_id', '=', request.env.user.partner_id.id),
            ('state', 'in', ['draft', 'open', 'done']),
        ], limit=1)
        
        if existing_registration:
            from odoo.addons.http_routing.models.ir_http import slug
            return request.redirect(
                f'/event/{slug(event)}/registration/success?registration_ids={existing_registration.id}'
            )
        
        # User is authenticated, proceed with normal registration
        return super().registration_confirm(event, **post)
