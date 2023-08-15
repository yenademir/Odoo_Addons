{
    'name': 'File Upload',
    'version': '1.0',
    'license': "LGPL-3",
    'summary': 'Product Card File Upload',
    'sequence': -100,
    'description': """Product Card File Upload""",
    'category': 'Product',
    'website': 'https://www.yourcompanywebsite.com',
    'depends': ['base', 'product'],
    'data': [
        'views/product_template_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/icon.png'],
}
