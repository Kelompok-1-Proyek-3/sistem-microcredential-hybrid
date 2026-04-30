{
    'name': 'Microcredential Sales',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'B2B Contract Management untuk Platform Microcredential IMPC',
    'author': 'IMPC Dev Team',
    'depends': [
        'sale',           # sale.order, sale.order.line
        'crm',            # crm.stage, pipeline
        'contacts',       # res.partner UI
        'mail',           # mail.template, chatter
        'portal',         # CustomerPortal, portal views
        'account',        # link ke invoice (A-06)
        'website_slides', # slide.channel (model kursus eLearning)
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_templates.xml',
        'data/crm_pipeline_data.xml',
        'views/sale_order_contract_views.xml',
        'views/sale_order_line_contract_views.xml',
        'views/sale_order_integration_views.xml',
        'views/redeem_code_log_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_dashboard_views.xml',
        'views/portal_hr_templates.xml',
        'report/quotation_b2b_report.xml',
        'wizard/redeem_code_wizard.xml',
    ],
    'installable': True,
    'application': True,
}
