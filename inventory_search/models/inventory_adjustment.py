from odoo import api, fields, models

class Inventory(models.Model):
    _inherit = 'stock.picking'

