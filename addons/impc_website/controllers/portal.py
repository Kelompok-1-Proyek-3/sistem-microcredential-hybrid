import base64

from odoo import fields, http
from odoo.http import request


class IMPCPortalController(http.Controller):
    """Student portal controller for IMPC Microcredential Platform."""

    @http.route(
        ["/my-learning", "/impc/my-learning"], type="http", auth="user", website=True
    )
    def my_learning_dashboard(self, **kw):
        """Student dashboard with progress overview."""
        # Administrators are not learners — redirect to management dashboard
        if request.env.user.has_group("base.group_system"):
            return request.redirect("/management/dashboard")

        partner = request.env.user.partner_id

        # Get all enrollments
        enrollments = (
            request.env["slide.channel.partner"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", partner.id),
                    ("member_status", "in", ["joined", "ongoing", "completed"]),
                ],
                order="create_date desc",
            )
        )

        # Stats
        in_progress = enrollments.filtered(
            lambda e: e.member_status in ("joined", "ongoing")
        )
        completed = enrollments.filtered(lambda e: e.member_status == "completed")

        # Certificates
        certificates = (
            request.env["impc.certificate"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", partner.id),
                    ("state", "=", "issued"),
                ],
                order="completion_date desc",
                limit=5,
            )
        )

        # Continue learning (last accessed / most recent enrollment not completed)
        continue_course = in_progress[:1] if in_progress else None

        # Upcoming events (for hybrid courses)
        upcoming_events = []
        for enrollment in in_progress:
            if enrollment.channel_id.learning_mode in ("hybrid", "offline"):
                event = enrollment.channel_id.event_id
                if (
                    event
                    and event.date_begin
                    and event.date_begin > fields.Datetime.now()
                ):
                    upcoming_events.append(
                        {
                            "enrollment": enrollment,
                            "event": event,
                        }
                    )

        values = {
            "enrollments": enrollments,
            "in_progress": in_progress,
            "completed": completed,
            "certificates": certificates,
            "continue_course": continue_course,
            "upcoming_events": upcoming_events[:5],
            "total_in_progress": len(in_progress),
            "total_completed": len(completed),
            "total_certificates": len(certificates),
        }
        return request.render("impc_website.portal_dashboard", values)

    @http.route(
        ["/my-learning/courses", "/impc/my-learning/courses"],
        type="http",
        auth="user",
        website=True,
    )
    def my_courses(self, status="all", **kw):
        """Student enrolled courses list."""
        partner = request.env.user.partner_id

        domain = [
            ("partner_id", "=", partner.id),
            ("member_status", "in", ["joined", "ongoing", "completed"]),
        ]

        if status == "in_progress":
            domain = [
                ("partner_id", "=", partner.id),
                ("member_status", "in", ["joined", "ongoing"]),
            ]
        elif status == "completed":
            domain = [
                ("partner_id", "=", partner.id),
                ("member_status", "=", "completed"),
            ]

        enrollments = (
            request.env["slide.channel.partner"]
            .sudo()
            .search(domain, order="create_date desc")
        )

        values = {
            "enrollments": enrollments,
            "status": status,
        }
        return request.render("impc_website.portal_my_courses", values)

    @http.route(
        ["/my-learning/certificates", "/impc/my-learning/certificates"],
        type="http",
        auth="user",
        website=True,
    )
    def my_certificates(self, **kw):
        """Student certificates list."""
        partner = request.env.user.partner_id

        certificates = (
            request.env["impc.certificate"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", partner.id),
                    ("state", "=", "issued"),
                ],
                order="completion_date desc",
            )
        )

        values = {
            "certificates": certificates,
        }
        return request.render("impc_website.portal_my_certificates", values)

    @http.route(
        ["/my-learning/events", "/impc/my-learning/events"],
        type="http",
        auth="user",
        website=True,
    )
    def my_events(self, **kw):
        """Student upcoming events/sessions."""
        partner = request.env.user.partner_id

        # Get enrollments with hybrid/offline courses
        enrollments = (
            request.env["slide.channel.partner"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", partner.id),
                    ("channel_id.learning_mode", "in", ["hybrid", "offline"]),
                    ("member_status", "in", ["joined", "ongoing"]),
                ]
            )
        )

        events_data = []
        for enrollment in enrollments:
            event = enrollment.channel_id.event_id
            if event:
                # Check registration
                registration = (
                    request.env["event.registration"]
                    .sudo()
                    .search(
                        [
                            ("event_id", "=", event.id),
                            ("partner_id", "=", partner.id),
                        ],
                        limit=1,
                    )
                )

                # Check attendance
                attendance = (
                    request.env["impc.session.attendance"]
                    .sudo()
                    .search(
                        [
                            ("channel_partner_id", "=", enrollment.id),
                            ("event_id", "=", event.id),
                        ],
                        limit=1,
                    )
                )

                events_data.append(
                    {
                        "enrollment": enrollment,
                        "event": event,
                        "registration": registration,
                        "attendance": attendance,
                        "is_registered": bool(registration),
                        "attendance_status": attendance.attendance_status
                        if attendance
                        else "pending",
                    }
                )

        values = {
            "events_data": events_data,
        }
        return request.render("impc_website.portal_my_events", values)

    @http.route(
        [
            "/my-learning/certificate/<int:cert_id>/download",
            "/impc/my-learning/certificate/<int:cert_id>/download",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def download_certificate(self, cert_id, **kw):
        """Download certificate PDF."""
        partner = request.env.user.partner_id
        certificate = (
            request.env["impc.certificate"]
            .sudo()
            .search(
                [
                    ("id", "=", cert_id),
                    ("partner_id", "=", partner.id),
                    ("state", "=", "issued"),
                ],
                limit=1,
            )
        )

        if not certificate or not certificate.attachment_id:
            return request.redirect("/my-learning/certificates")

        attachment = certificate.attachment_id
        return request.make_response(
            base64.b64decode(attachment.datas) if attachment.datas else b"",
            headers=[
                ("Content-Type", "application/pdf"),
                (
                    "Content-Disposition",
                    f'attachment; filename="{certificate.name}.pdf"',
                ),
            ],
        )
