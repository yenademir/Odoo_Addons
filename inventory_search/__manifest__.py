{
    'name': "Inventory Custom Search",
    'version': '1.0',
    'summary': "Enhanced search functionalities for the Inventory module",
    'description': """
        This add-on provides enhanced search functionalities to the Inventory module, 
        making it easier and more efficient for users to locate items and manage their inventory.
    """,
    'author': "Emre Mataracı",
    'category': 'Inventory',
    'depends': ['Inventory'],
    'data': [
        'views/transfer_search_view.xml',
        'views/product_search_view.xml'
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

