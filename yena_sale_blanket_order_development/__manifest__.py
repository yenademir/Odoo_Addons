{
    'name': 'Yena Sales Blanket Order Development',
    'version': '1.0',
    'author': 'Emre Mataracı',
    'website': 'https://www.yenaengineering.nl',
    'summary': 'Customizations for Sales Blanket Order',
    'sequence': -100,
    'description': """Developments and customizations for Yena Sales Blanket Order""",
    'category': 'Sales',
    'depends': ['base', 'sale_management'],
    'data': [
        'views/sale_blanket_order_development.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
