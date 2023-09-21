{
    'name': "Purchase Order Search",
    'summary': "Add custom search filter for C-Reference Number",
    'description': """
        Add a custom search filter for C-Reference Number in Purchase module.
    """,
    'author': "Emre Mataracı",
    'category': 'Purchases',
    'version': '1.0',
    'depends': ['purchase'],
    'data': [
        'views/purchase_order_search_view.xml',
    ],
}
