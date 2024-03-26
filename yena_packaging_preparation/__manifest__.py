{
    'name': "YENA Packaging Preparation",
    'version': '15.1.0',
    'summary': "Easy preparation of transfer documents",
    'author': "Alperen Alihan ER",
    'website': "https://yenaengineering.nl",
    'category': 'Inventory',
    'license': 'LGPL-3',
    'depends': ['product', 'stock', 'barcodes', 'digest', 'purchase', 'base', 'account', 'delivery'],
    'data': [
        'views/packaging_preparation.xml',
        'security/ir.model.access.csv',
        'reports/packaging_preparation_report.xml',
        'reports/packaging_bill_of_laid_report.xml',
        'reports/packaging_preparation_packing_list_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
