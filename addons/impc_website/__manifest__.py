{
    "name": "IMPC Website - Microcredential LMS Platform",
    "version": "19.0.1.0.0",
    "category": "Website/eLearning",
    "summary": "Indonesia Microcredential Platform Center - LMS with hybrid learning, "
    "voucher enrollment, and digital certification",
    "description": """
IMPC (Indonesia Microcredential Platform Center)
=================================================

A comprehensive LMS platform built on Odoo 19 extending native eLearning.

Features:
- Public marketing website with course catalog
- Student learning portal with progress tracking
- B2C course enrollment via eCommerce
- B2B voucher/redeem code enrollment
- Hybrid learning support (online + offline events)
- Exam gating based on attendance
- Digital certificate generation with QR verification
- External certificate verification API
    """,
    "author": "IMPC Development Team",
    "website": "https://impc.id",
    "license": "LGPL-3",
    "depends": [
        "website_slides",
        "website_sale_slides",
        "website_sale",
        "website_slides_survey",
        "event",
        "website_event",
        "portal",
        "mail",
    ],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        # Data
        "data/website_data.xml",
        "data/mail_template.xml",
        "data/cron.xml",
        # Report
        "report/certificate_report.xml",
        "report/certificate_template.xml",
        # Backend Views
        "views/backend/certificate_views.xml",
        "views/backend/slide_channel_views.xml",
        "views/backend/redeem_code_views.xml",
        "views/backend/session_attendance_views.xml",
        "views/backend/event_approval_views.xml",
        "views/backend/menu.xml",
        # Website Templates
        "views/templates/layout.xml",
        "views/templates/navbar.xml",
        "views/templates/footer.xml",
        "views/templates/homepage.xml",
        "views/templates/courses.xml",
        "views/templates/course_detail.xml",
        "views/templates/course_certification.xml",
        "views/templates/pricing.xml",
        "views/templates/about.xml",
        "views/templates/faq.xml",
        "views/templates/corporate.xml",
        "views/templates/contact.xml",
        "views/templates/verify_certificate.xml",

        # Portal Templates
        "views/portal/dashboard.xml",
        "views/portal/my_courses.xml",
        "views/portal/my_certificates.xml",
        "views/portal/my_events.xml",
        "views/portal/redeem_voucher.xml",
        # Admin Templates
        "views/admin/dashboard.xml",
        "views/admin/course_approvals.xml",
        "views/admin/event_approvals.xml",
        # Wizard
        "wizard/generate_redeem_codes_views.xml",
        "wizard/publish_approved_events_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "impc_website/static/src/css/impc_style.css",
            "impc_website/static/src/js/portal.js",
            "impc_website/static/src/js/redeem.js",
        ],
    },
    "post_init_hook": "post_init_hook",
    "post_load": "post_load",
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": True,
    "auto_install": False,
}
