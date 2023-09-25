from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    contact_type = fields.Selection([
        ('vendor', 'Vendor'),
        ('potential_vendor', 'Potential Vendor'),
        ('customer', 'Customer'),
        ('potential_customer', 'Potential Customer')
    ], string='Contact Type')
