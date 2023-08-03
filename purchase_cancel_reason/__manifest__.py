{
    'name': 'Purchase Order Cancel Reason',
    'version': '1.0',
    'category': 'Purchase',
    'summary': 'This module adds a cancel reason to purchase orders',
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_view.xml',
        'views/cancel_order_wizard.xml',
    ],
    'installable': True,
    'auto_install': False,
}
