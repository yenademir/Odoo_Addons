{
    'name': 'Send Balance Letter',
    'version': '1.0',
    'license': "LGPL-3",
    'summary': 'Send Balance Letter',
    'sequence': -100,
    'description': """Send Balance Letter""",
    'category': 'Product',
    'depends': ['base', 'mail'],
    'data': [
        'views/res_partner_view.xml',  # Add here all your xml files
        'data/mail_template_data.xml',  # Example for mail template data file
    ],
    'installable': True,
}