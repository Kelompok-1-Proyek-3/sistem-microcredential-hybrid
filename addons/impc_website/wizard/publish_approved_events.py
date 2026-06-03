from odoo import api, fields, models


class PublishApprovedEventsWizard(models.TransientModel):
    """Wizard to bulk publish approved events to website."""

    _name = "impc.publish.approved.events.wizard"
    _description = "Publish Approved Events to Website"

    event_count = fields.Integer(
        string="Events to Publish",
        readonly=True,
        compute="_compute_event_count",
    )
    event_ids = fields.Many2many(
        "event.event",
        string="Events",
        compute="_compute_event_ids",
        readonly=True,
    )

    @api.depends_context("active_model", "active_ids")
    def _compute_event_count(self):
        """Count approved but unpublished events."""
        for wizard in self:
            if self.env.context.get("active_model") == "event.event" and self.env.context.get("active_ids"):
                # Called from event list view with selection
                events = self.env["event.event"].browse(self.env.context.get("active_ids"))
                wizard.event_count = len(
                    events.filtered(
                        lambda e: e.impc_approval_state == "approved" and not e.website_published
                    )
                )
            else:
                # Called from menu or without selection
                wizard.event_count = self.env["event.event"].search_count([
                    ("impc_approval_state", "=", "approved"),
                    ("website_published", "=", False),
                ])

    @api.depends_context("active_model", "active_ids")
    def _compute_event_ids(self):
        """Get approved but unpublished events."""
        for wizard in self:
            if self.env.context.get("active_model") == "event.event" and self.env.context.get("active_ids"):
                # Called from event list view with selection
                events = self.env["event.event"].browse(self.env.context.get("active_ids"))
                wizard.event_ids = events.filtered(
                    lambda e: e.impc_approval_state == "approved" and not e.website_published
                )
            else:
                # Called from menu or without selection
                wizard.event_ids = self.env["event.event"].search([
                    ("impc_approval_state", "=", "approved"),
                    ("website_published", "=", False),
                ])

    def action_publish_events(self):
        """Publish all approved but unpublished events."""
        self.ensure_one()
        
        if self.event_ids:
            self.event_ids.write({"website_published": True})
            
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Success",
                    "message": f"{len(self.event_ids)} event(s) successfully published to website!",
                    "type": "success",
                    "sticky": False,
                },
            }
        else:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "No Events",
                    "message": "No approved events to publish.",
                    "type": "info",
                    "sticky": False,
                },
            }
