{
    'name': "Yena Schedule Activity Extension",
    'version': "1.0",
    'summary': "Scheduled Activites View Customization for YENA",
    'sequence': -100,
    'description': """Schedule Activity View Customizations to include User in the list view for Yena""",
    'category': 'Productivity',
    'author': "YENA Engineering",
    'website': "www.yenaengineering.nl",
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'views/scheduled_activities.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
