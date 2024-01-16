{
    "name": "Yena Sale order line price history",
    "version": "15.0.1.0.0",
    "category": "Purchase Management",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/purchase-workflow",
    "license": "AGPL-3",
    
    "depends": ["sale", "sale_blanket_order"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/sale_order_line_history.xml",
        "views/sale_views.xml",
    ],
    
    "installable": True,
}
