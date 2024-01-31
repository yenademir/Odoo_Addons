{
    'name': "YENA Inventory Development",
    'version': '15.1.1',
    'summary': "All Development about product.template and stock.picking",
    'author': "Emre MATARACI, Alperen Alihan ER, Selçuk ATAV",
    'website': "https://yenaengineering.nl",
    'category': 'Inventory',
    'license': 'LGPL-3',
    'depends': ['product', 'stock', 'barcodes', 'digest', 'purchase', 'base', 'account', 'delivery' , 'batch_transfer_extension_test'],
    'data': [
        'views/inventory_development.xml',
        'security/ir.model.access.csv',
        'views/hs_code.xml',
        'data/mail_activity_data.xml'
    ],
    'installable': True,
    'auto_install': False,
}
