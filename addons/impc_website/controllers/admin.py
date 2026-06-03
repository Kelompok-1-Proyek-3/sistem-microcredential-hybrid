from odoo import fields, http
from odoo.http import request


class IMPCAdminController(http.Controller):
    """Management controller for IMPC Administrators.

    Provides frontend management dashboard, course approvals, and event approvals.
    All routes require the user to belong to the `group_impc_admin` security group.
    """

    def _require_admin(self):
        """Return a redirect response if the current user is not an IMPC Administrator.
        Returns None if access is granted.
        """
        if request.env.user._is_public() or not request.env.user.has_group(
            "base.group_system"
        ):
            return request.redirect("/web/login")
        return None

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    @http.route(["/management/dashboard"], type="http", auth="user", website=True)
    def admin_dashboard(self, **kw):
        """Administrator management dashboard."""
        guard = self._require_admin()
        if guard:
            return guard

        env = request.env

        # Pending course approvals (submitted or under review)
        pending_courses = (
            env["slide.channel"]
            .sudo()
            .search(
                [
                    ("approval_state", "in", ["submitted", "under_review"]),
                ],
                order="write_date desc",
                limit=5,
            )
        )
        pending_courses_count = (
            env["slide.channel"]
            .sudo()
            .search_count(
                [
                    ("approval_state", "in", ["submitted", "under_review"]),
                ]
            )
        )

        # Pending event approvals
        pending_events = (
            env["event.event"]
            .sudo()
            .search(
                [
                    ("impc_approval_state", "in", ["submitted", "under_review"]),
                ],
                order="write_date desc",
                limit=5,
            )
        )
        pending_events_count = (
            env["event.event"]
            .sudo()
            .search_count(
                [
                    ("impc_approval_state", "in", ["submitted", "under_review"]),
                ]
            )
        )

        # Published courses count
        published_courses_count = (
            env["slide.channel"]
            .sudo()
            .search_count(
                [
                    ("is_published", "=", True),
                ]
            )
        )

        # Approved events count (IMPC-approved events)
        published_events_count = (
            env["event.event"]
            .sudo()
            .search_count(
                [
                    ("impc_approval_state", "=", "approved"),
                ]
            )
        )

        # Active learners (unique partners with active enrollments)
        active_partner_ids = (
            env["slide.channel.partner"]
            .sudo()
            .search(
                [
                    ("member_status", "in", ["joined", "ongoing"]),
                ]
            )
            .mapped("partner_id.id")
        )
        active_learners_count = len(set(active_partner_ids))

        # Upcoming events (next 5)
        upcoming_events = (
            env["event.event"]
            .sudo()
            .search(
                [
                    ("date_begin", ">", fields.Datetime.now()),
                ],
                order="date_begin asc",
                limit=5,
            )
        )
        upcoming_events_count = (
            env["event.event"]
            .sudo()
            .search_count(
                [
                    ("date_begin", ">", fields.Datetime.now()),
                ]
            )
        )

        # Certificate statistics
        total_certificates = (
            env["impc.certificate"]
            .sudo()
            .search_count(
                [
                    ("state", "=", "issued"),
                ]
            )
        )
        pending_certificates = (
            env["impc.certificate"]
            .sudo()
            .search_count(
                [
                    ("state", "=", "draft"),
                ]
            )
        )

        # Redeem code statistics
        active_codes = (
            env["impc.redeem.code"]
            .sudo()
            .search_count(
                [
                    ("state", "=", "active"),
                ]
            )
        )
        claimed_codes = (
            env["impc.redeem.code"]
            .sudo()
            .search_count(
                [
                    ("state", "=", "claimed"),
                ]
            )
        )
        expired_codes = (
            env["impc.redeem.code"]
            .sudo()
            .search_count(
                [
                    ("state", "in", ["expired", "revoked"]),
                ]
            )
        )

        values = {
            "pending_courses": pending_courses,
            "pending_courses_count": pending_courses_count,
            "pending_events": pending_events,
            "pending_events_count": pending_events_count,
            "published_courses_count": published_courses_count,
            "published_events_count": published_events_count,
            "active_learners_count": active_learners_count,
            "upcoming_events": upcoming_events,
            "upcoming_events_count": upcoming_events_count,
            "total_certificates": total_certificates,
            "pending_certificates": pending_certificates,
            "active_codes": active_codes,
            "claimed_codes": claimed_codes,
            "expired_codes": expired_codes,
        }
        return request.render("impc_website.admin_dashboard", values)

    # ------------------------------------------------------------------
    # Course Approvals
    # ------------------------------------------------------------------

    @http.route(
        ["/management/approvals/courses"], type="http", auth="user", website=True
    )
    def course_approvals(self, state="pending", **kw):
        """List of courses in the approval pipeline."""
        guard = self._require_admin()
        if guard:
            return guard

        env = request.env

        if state == "pending":
            domain = [("approval_state", "in", ["submitted", "under_review"])]
        elif state in ("draft", "submitted", "under_review", "approved", "rejected"):
            domain = [("approval_state", "=", state)]
        else:
            domain = [("approval_state", "!=", "draft")]

        courses = env["slide.channel"].sudo().search(domain, order="write_date desc")
        pending_count = (
            env["slide.channel"]
            .sudo()
            .search_count(
                [
                    ("approval_state", "in", ["submitted", "under_review"]),
                ]
            )
        )

        values = {
            "courses": courses,
            "current_state": state,
            "pending_count": pending_count,
        }
        return request.render("impc_website.admin_course_approvals", values)

    @http.route(
        ["/management/approvals/courses/<int:channel_id>/review"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def course_review_action(self, channel_id, action="", reason="", **kw):
        """Handle approve / start_review / reject actions on a course."""
        guard = self._require_admin()
        if guard:
            return guard

        channel = request.env["slide.channel"].sudo().browse(channel_id)
        if channel.exists():
            if action == "approve":
                channel.action_approve()
            elif action == "start_review":
                channel.action_start_review()
            elif action == "reject":
                channel.write({"rejection_reason": reason or "No reason provided."})
                channel.action_reject()
            elif action == "reset":
                channel.action_reset_to_draft()

        return request.redirect("/management/approvals/courses")

    # ------------------------------------------------------------------
    # Event Approvals
    # ------------------------------------------------------------------

    @http.route(
        ["/management/approvals/events"], type="http", auth="user", website=True
    )
    def event_approvals(self, state="pending", **kw):
        """List of events in the approval pipeline."""
        guard = self._require_admin()
        if guard:
            return guard

        env = request.env

        if state == "pending":
            domain = [("impc_approval_state", "in", ["submitted", "under_review"])]
        elif state in ("draft", "submitted", "under_review", "approved", "rejected"):
            domain = [("impc_approval_state", "=", state)]
        else:
            domain = [("impc_approval_state", "!=", "draft")]

        events = env["event.event"].sudo().search(domain, order="write_date desc")
        pending_count = (
            env["event.event"]
            .sudo()
            .search_count(
                [
                    ("impc_approval_state", "in", ["submitted", "under_review"]),
                ]
            )
        )

        values = {
            "events": events,
            "current_state": state,
            "pending_count": pending_count,
        }
        return request.render("impc_website.admin_event_approvals", values)

    @http.route(
        ["/management/approvals/events/<int:event_id>/review"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def event_review_action(self, event_id, action="", reason="", **kw):
        """Handle approve / start_review / reject actions on an event."""
        guard = self._require_admin()
        if guard:
            return guard

        event = request.env["event.event"].sudo().browse(event_id)
        if event.exists():
            if action == "approve":
                event.action_impc_approve()
            elif action == "start_review":
                event.action_impc_start_review()
            elif action == "reject":
                event.write({"impc_rejection_reason": reason or "No reason provided."})
                event.action_impc_reject()
            elif action == "reset":
                event.action_impc_reset_to_draft()

        return request.redirect("/management/approvals/events")
