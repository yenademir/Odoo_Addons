from odoo import api, fields, models

class VendorWizard(models.TransientModel):
    _name = 'vendor.wizard'
    _description = 'Vendor Wizard'

    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True)
    product_line_ids = fields.Many2many('call.for.vendors.line', string='Products')

    def add_products(self):
        self.ensure_one()
        for line in self.product_line_ids:
            line.vendor_ids |= self.vendor_id
        return {'type': 'ir.actions.act_window_close'}
