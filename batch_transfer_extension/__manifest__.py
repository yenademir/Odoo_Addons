{
    'name': 'Batch Transfer Extension',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Extends Batch Transfer with additional fields',
    'author': 'Emre Mataracı',
    'website': 'http://yourwebsite.com',
    'depends': ['stock', 'project', 'purchase', 'contacts', 'l10n_tr_stock_edespatch'],
    'data': [
        'views/batch_transfer_view.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'auto_install': False,
}
