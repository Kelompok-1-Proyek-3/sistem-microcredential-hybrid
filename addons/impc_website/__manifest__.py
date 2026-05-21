{
    'name': 'IMPC Website - Microcredential Platform',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Website pages for the IMPC microcredential platform',
    'description': 'Public website, course catalog, and student dashboard UI for IMPC.',
    'author': 'IMPC Team',
    'website': 'https://b1study.com',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'portal',
    ],
    'data': [
        'views/homepage.xml',
        'views/courses.xml',
        'views/dashboard.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'impc_website/static/src/css/impc_style.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
