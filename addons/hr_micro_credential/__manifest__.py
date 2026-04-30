# Part of IMPC Microcredential Platform. See LICENSE file for full copyright and licensing details.

{
    'name': 'HR Microcredential',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Employees',
    'sequence': 275,
    'summary': 'Employee learning tracking, skills mapping & analytics for Microcredential Platform',
    'description': """
HR Microcredential - IMPC Platform
====================================

Custom module untuk HR Group pada platform Microcredential IMPC.

Fitur utama:
- Real-time employee learning progress dashboard
- Hybrid attendance monitoring (check-in status)
- Certificate → Skill mapping otomatis
- At-risk employee detection & alerts
- Department learning analytics & reporting
- Employee skills profile & gap analysis
    """,
    'depends': [
        'hr',
        'hr_skills',
        'mail',
    ],
    'data': [
        # Security
        'security/hr_micro_credential_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',

        # Views
        'views/hr_learning_progress_views.xml',
        'views/hr_learning_profile_note_views.xml',
        'views/hr_learning_analytics_views.xml',
        'views/hr_course_skill_mapping_views.xml',
        'views/hr_skill_mapping_log_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_micro_credential_menus.xml',
    ],
    'demo': [
        'data/hr_micro_credential_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'assets': {
        'web.assets_backend': [
            'hr_micro_credential/static/src/**/*',
        ],
    },
    'author': 'IMPC Microcredential Team - HR Group',
    'license': 'LGPL-3',
}
