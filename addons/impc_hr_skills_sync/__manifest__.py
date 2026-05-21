{
    'name': 'IMPC HR Skills Sync',
    'version': '19.0.1.0.0',
    'summary': 'Sync employee skills from course certificates',
    'category': 'Human Resources/Employees',
    'depends': [
        'hr',
        'hr_skills',
        'website_slides',
        'impc_lms',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/impc_course_skill_mapping_views.xml',
        'views/hr_employee_skill_mapping_log_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
