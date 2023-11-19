{
    'name': "YENA Replace Views",
    'version': '15.1.1',
    'summary': "Replace Views",
    'author': "Emre MATARACI",
    'website': "https://yenaengineering.nl",
    'category': 'Inventory',
    'license': 'LGPL-3',
    'depends': ['sale', 'crm','sale_crm', 'product', 'stock', 'barcodes', 'digest', 'purchase', 'base', 'account'],
    'data': [
        'views/replace.xml',
    ],
    'installable': True,
    'auto_install': False,
}
