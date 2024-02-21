{
    'name': "YENA Date Diff Development",
    'version': '15.1.0',
    'summary': "All Development about purchase and sale order date difference",
    'author': "Selçuk Atav",
    'website': "https://yenaengineering.nl",
    'category': 'Purchase and Sales',
    'license': 'LGPL-3',
    'depends': ['sale','yena_sales_development','yena_purchase_development','stock','purchase', 'yena_inventory_development', 'batch_transfer_extension'],
    'data': [
        'views/date_diffs.xml',
    ],
    'installable': True,
    'auto_install': False,
}
