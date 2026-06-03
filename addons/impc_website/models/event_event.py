from odoo import fields, models


class EventEvent(models.Model):
    """Extends event.event with IMPC approval workflow."""

    _inherit = "event.event"

    # === IMPC Approval Workflow ===
    # Fields are prefixed with 'impc_' to avoid conflicts with native event fields.
    impc_approval_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted for Review"),
            ("under_review", "Under Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="IMPC Approval Status",
        default="draft",
        tracking=True,
        copy=False,
        help="Event approval workflow state managed by IMPC Administrator.",
    )
    impc_rejection_reason = fields.Text(
        string="Rejection Reason",
        copy=False,
    )
    impc_submitted_by = fields.Many2one(
        "res.users",
        string="Submitted By",
        readonly=True,
        copy=False,
    )
    impc_reviewed_by = fields.Many2one(
        "res.users",
        string="Reviewed By",
        readonly=True,
        copy=False,
    )
    impc_review_date = fields.Datetime(
        string="IMPC Review Date",
        readonly=True,
        copy=False,
    )

    def action_impc_submit_for_review(self):
        """Event Coordinator submits the event for Administrator review."""
        self.ensure_one()
        self.write(
            {
                "impc_approval_state": "submitted",
                "impc_submitted_by": self.env.user.id,
                "impc_rejection_reason": False,
            }
        )

    def action_impc_start_review(self):
        """Administrator marks the event as under review."""
        self.ensure_one()
        self.impc_approval_state = "under_review"

    def action_impc_approve(self):
        """Administrator approves the event and confirms it."""
        self.ensure_one()
        self.write(
            {
                "impc_approval_state": "approved",
                "impc_reviewed_by": self.env.user.id,
                "impc_review_date": fields.Datetime.now(),
                "website_published": True,  # Auto-publish to website when approved
            }
        )

    def action_impc_reject(self):
        """Administrator rejects the event. Set impc_rejection_reason before calling."""
        self.ensure_one()
        self.write(
            {
                "impc_approval_state": "rejected",
                "impc_reviewed_by": self.env.user.id,
                "impc_review_date": fields.Datetime.now(),
            }
        )

    def action_impc_reset_to_draft(self):
        """Reset event IMPC approval back to draft."""
        self.ensure_one()
        self.write(
            {
                "impc_approval_state": "draft",
                "impc_rejection_reason": False,
            }
        )

    def _auto_publish_approved_events(self):
        """Utility method to auto-publish all approved events that are not yet published.
        Can be called manually or via scheduled action."""
        approved_unpublished = self.search([
            ("impc_approval_state", "=", "approved"),
            ("website_published", "=", False),
        ])
        if approved_unpublished:
            approved_unpublished.write({"website_published": True})
        return len(approved_unpublished)

    def action_publish_event(self):
        """Manually publish an approved event to the website."""
        self.ensure_one()
        if self.impc_approval_state == "approved":
            self.website_published = True
        return True
