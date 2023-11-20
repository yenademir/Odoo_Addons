{
    'name': 'Purchase Portal',
    'version': '1.0',
    'category': 'Purchase',
    'summary': 'Manage Purchase Portal',
    'depends': ['web', 'purchase', 'base', 'sale_management', 'project', 'account', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'views/call_for_vendors.xml',
        'views/purchase_order.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_portal_templates.xml',
        'views/call_for_vendors_purchase_wizards.xml',
        'views/call_for_vendors_wizards.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'purchase_portal/static/src/js/send_button.js',
            'purchase_portal/static/src/js/confirm_button.js',
            'purchase_portal/static/src/js/script.js',
        ]
    },
    'installable': True,
}
