from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SlideChannel(models.Model):
    _inherit = "slide.channel"

    # === Learning Mode ===
    learning_mode = fields.Selection(
        selection=[
            ("online", "Online"),
            ("offline", "Offline"),
            ("hybrid", "Hybrid"),
        ],
        string="Learning Mode",
        default="online",
        required=True,
        help="Determines the delivery method for this course.",
    )

    # === Event Integration (Hybrid/Offline) ===
    event_id = fields.Many2one(
        "event.event",
        string="Linked Event Session",
        help="The offline event session linked to this course (required for Hybrid/Offline mode).",
    )
    event_date_begin = fields.Datetime(
        related="event_id.date_begin",
        string="Session Start Date",
        readonly=True,
    )
    event_date_end = fields.Datetime(
        related="event_id.date_end",
        string="Session End Date",
        readonly=True,
    )
    event_location = fields.Char(
        related="event_id.address_inline",
        string="Session Location",
        readonly=True,
    )

    # === Course Metadata ===
    is_featured = fields.Boolean(
        string="Featured on Homepage",
        default=False,
        help="Display this course in the featured section on the homepage.",
    )
    difficulty_level = fields.Selection(
        selection=[
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
        ],
        string="Difficulty Level",
        default="beginner",
    )
    estimated_duration = fields.Float(
        string="Estimated Duration (Hours)",
        help="Total estimated learning hours for this course.",
    )
    instructor_ids = fields.Many2many(
        "res.partner",
        "slide_channel_instructor_rel",
        "channel_id",
        "partner_id",
        string="Instructors",
    )
    prerequisite_ids = fields.Many2many(
        "slide.channel",
        "slide_channel_prerequisite_rel",
        "channel_id",
        "prerequisite_id",
        string="Prerequisites",
    )
    sks_weight = fields.Integer(
        string="SKS Credit Weight",
        default=0,
        help="Informational SKS credit weight for this course.",
    )
    short_description = fields.Text(
        string="Short Description",
        help="Brief description shown in course cards (max 200 chars).",
    )
    target_audience = fields.Text(
        string="Target Audience",
        help="Who should take this course.",
    )
    learning_outcomes = fields.Text(
        string="Learning Outcomes",
        help="What students will learn from this course.",
    )

    # === Computed Fields ===
    enrolled_count = fields.Integer(
        string="Enrolled Students",
        compute="_compute_enrolled_count",
        compute_sudo=True,
    )
    certificate_count = fields.Integer(
        string="Certificates Issued",
        compute="_compute_certificate_count",
        compute_sudo=True,
    )

    @api.depends("channel_partner_ids", "channel_partner_ids.member_status")
    def _compute_enrolled_count(self):
        grouped_data = self.env["slide.channel.partner"].sudo()._read_group(
            [
                ("channel_id", "in", self.ids),
                ("member_status", "in", ["joined", "ongoing", "completed"]),
            ],
            groupby=["channel_id"],
            aggregates=["__count"],
        )
        counts = {channel.id: count for channel, count in grouped_data}
        for record in self:
            record.enrolled_count = counts.get(record.id, 0)

    def _compute_certificate_count(self):
        Certificate = self.env["impc.certificate"].sudo()
        for record in self:
            record.certificate_count = Certificate.search_count(
                [
                    ("channel_id", "=", record.id),
                    ("state", "=", "issued"),
                ]
            )

    def _get_categorized_slides(self, base_domain, order, force_void=True, limit=False, offset=False):
        category_data = super()._get_categorized_slides(
            base_domain,
            order,
            force_void=force_void,
            limit=limit,
            offset=offset,
        )
        visible_category_data = []
        for category in category_data:
            slides = category["slides"].filtered(
                lambda slide: slide.slide_category != "certification"
            )
            if not slides and not force_void:
                continue
            visible_category_data.append({
                **category,
                "total_slides": len(slides),
                "slides": slides,
            })
        return visible_category_data

    def _impc_certification_slide(self):
        self.ensure_one()
        return self.slide_content_ids.filtered(
            lambda slide: slide.slide_category == "certification"
        )[:1]

    def _impc_lesson_slides(self):
        self.ensure_one()
        return self.slide_content_ids.filtered(
            lambda slide: (
                slide.slide_category != "certification"
                and not slide.is_category
                and slide.website_published
            )
        )

    def _impc_lessons_completed(self, channel_progress):
        self.ensure_one()
        for slide in self._impc_lesson_slides():
            if not channel_progress.get(slide.id, {}).get("completed"):
                return False
        return True

    # === Approval Workflow ===
    approval_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted for Review"),
            ("under_review", "Under Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Approval Status",
        default="draft",
        tracking=True,
        copy=False,
        help="Course approval workflow state. Teachers submit; Administrators approve or reject.",
    )
    rejection_reason = fields.Text(
        string="Rejection Reason",
        copy=False,
        help="Reason for rejection provided by the Administrator.",
    )
    submitted_by = fields.Many2one(
        "res.users",
        string="Submitted By",
        readonly=True,
        copy=False,
    )
    reviewed_by = fields.Many2one(
        "res.users",
        string="Reviewed By",
        readonly=True,
        copy=False,
    )
    review_date = fields.Datetime(
        string="Review Date",
        readonly=True,
        copy=False,
    )

    def action_submit_for_review(self):
        """Teacher submits this course for Administrator review."""
        self.ensure_one()
        self.write(
            {
                "approval_state": "submitted",
                "submitted_by": self.env.user.id,
                "rejection_reason": False,
            }
        )

    def action_start_review(self):
        """Administrator marks the course as under review."""
        self.ensure_one()
        self.approval_state = "under_review"

    def action_approve(self):
        """Administrator approves and publishes the course and all its content."""
        self.ensure_one()
        self.write(
            {
                "approval_state": "approved",
                "reviewed_by": self.env.user.id,
                "review_date": fields.Datetime.now(),
                "is_published": True,
            }
        )
        # Automatically publish all slides/content in the course
        if self.slide_content_ids:
            self.slide_content_ids.write({"website_published": True})

    def action_reject(self):
        """Administrator rejects the course. Set rejection_reason before calling."""
        self.ensure_one()
        self.write(
            {
                "approval_state": "rejected",
                "reviewed_by": self.env.user.id,
                "review_date": fields.Datetime.now(),
                "is_published": False,
            }
        )
        # Unpublish all slides/content when course is rejected
        if self.slide_content_ids:
            self.slide_content_ids.write({"website_published": False})

    def action_reset_to_draft(self):
        """Reset the course approval state back to draft (e.g., after rejection)."""
        self.ensure_one()
        self.write(
            {
                "approval_state": "draft",
                "rejection_reason": False,
                "is_published": False,
            }
        )
        # Unpublish all slides/content when reset to draft
        if self.slide_content_ids:
            self.slide_content_ids.write({"website_published": False})

    # === Search API ===
    @api.model
    def search_published_courses(
        self,
        search="",
        category=None,
        level=None,
        mode=None,
        sort="newest",
        page=1,
        per_page=12,
    ):
        """Search and filter published courses with pagination.
        Returns dict with courses, total, pagination info.
        """
        domain = [("is_published", "=", True)]

        if search:
            domain += [
                "|",
                "|",
                ("name", "ilike", search),
                ("short_description", "ilike", search),
                ("tag_ids.name", "ilike", search),
            ]

        if category:
            domain += [("tag_ids.id", "=", int(category))]

        if level and level in ("beginner", "intermediate", "advanced"):
            domain += [("difficulty_level", "=", level)]

        if mode and mode in ("online", "offline", "hybrid"):
            domain += [("learning_mode", "=", mode)]

        order_map = {
            "newest": "create_date desc",
            "popular": "total_views desc",
            "name_asc": "name asc",
            "name_desc": "name desc",
        }
        order = order_map.get(sort, "create_date desc")

        page = int(page)
        offset = (page - 1) * per_page
        total = self.search_count(domain)
        courses = self.search(domain, order=order, limit=per_page, offset=offset)
        total_pages = (total + per_page - 1) // per_page

        return {
            "courses": courses,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "per_page": per_page,
        }

    # === Constraints ===
    @api.constrains("learning_mode", "event_id")
    def _check_event_required_for_hybrid(self):
        for record in self:
            if record.learning_mode in ("hybrid", "offline") and not record.event_id:
                raise ValidationError(
                    "An event session must be linked for Hybrid or Offline courses. "
                    'Please select an event in the "Linked Event Session" field.'
                )
