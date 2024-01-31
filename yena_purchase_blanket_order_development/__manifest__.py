{
    'name': 'Yena Purchase Blanket Order Development',
    'version': '1.0',
    'author': 'Emre Mataracı',
    'website': 'https://www.yenaengineering.nl',
    'summary': 'Purchase Blanket Order Developments',
    'sequence': -100,
    'description': """Yena Purchase Blanket Order Developments and Customizations""",
    'category': 'Purchases',
    'depends': ['base', 'purchase'],
    'data': [
        'views/purchase_blanket_order_development.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
