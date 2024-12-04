{
    'name': 'Product Phases',
    'version': '15.0.0.1',
    'summary': 'Adds phase status to products',
    'description': """
        This module adds a phase status field to the product template, allowing products to be categorized into different phases.
    """,
    'author': 'Emre Mataracı',
    'website': 'https://yenaengineering.nl',
    'category': 'Inventory',
    'depends': ['product'],
    'data': [
        'views/product_phases.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
