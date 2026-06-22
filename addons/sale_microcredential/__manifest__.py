# addons/sale_microcredential/__manifest__.py
{
    'name': 'Sale Microcredential B2B',
    'version': '19.0.1.0.0',
    'summary': 'B2B Contract Management & HR Partner Portal for Microcredential IMPC',
    'category': 'Sales/Sales',
    'author': 'IMPC',
    'depends': [
        'sale_management',
        'crm',
        'contacts',
        'portal',
        'mail',
        'base_setup',
        'website_slides',   # untuk slide.channel (eLearning model di Odoo 19)
        'impc_website',     # direct ORM access to impc.redeem.code.batch
    ],
    'data': [
        # Security (DEV 1) — harus di-load pertama
        'security/sale_microcredential_groups.xml',
        'security/ir.model.access.csv',

        # Data & Automation (DEV 2)
        'data/email_templates.xml',
        'data/server_actions.xml',
        'data/ir_cron.xml',

        # Wizard Views (DEV 2)
        'wizards/wizard_views.xml',

        # Backend Views (DEV 3)
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
        'views/dashboard_views.xml',

        # Portal Templates (DEV 3)
        'templates/portal_contract_list.xml',
        'templates/portal_contract_detail.xml',
        'templates/portal_redeem_codes.xml',
        'templates/portal_dashboard_inherit.xml',

        # Report
        'report/sale_contract_report_action.xml',
        'report/sale_contract_report_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
