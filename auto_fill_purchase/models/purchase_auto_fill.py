from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_contact_id = fields.Many2one('res.partner', string='Contact Person')
    x_rfq_sent_date = fields.Date('S-RFQ Sent Date')
    x_required_delivery_date = fields.Date('Required Delivery Date')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.x_contact_id = False
        return {'domain': {'x_contact_id': [('parent_id', '=', self.partner_id.id), ('type', '=', 'contact')]}}

    @api.model
    def create(self, vals):
        # x_order_date'i bugünün tarihi ile doldurun.
        vals['x_order_date'] = fields.Date.today()

        return super().create(vals)

    def button_send_rfq_email(self):
        res = super(PurchaseOrder, self).button_send_rfq_email()

        # RFQ gönderildiğinde x_rfq_sent_date'i güncelle
        for record in self:
            record.write({
                'x_rfq_sent_date': fields.Date.today(),
            })

        return res
    
    def button_approve(self, force=False):
        res = super(PurchaseOrder, self).button_approve(force=force)

        # Transfer project number to receipts
        for order in self:
            for pick in order.picking_ids:
                pick.write({'x_project_transfer': order.x_project_purchase})

        return res

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_product_required_delivery_date = fields.Date('Product Required Delivery Date')
    pricekg = fields.Float(compute='_compute_pricekg', string='EUR/kg', readonly=True, store=True)

    @api.depends('price_subtotal', 'x_totalweight')
    def _compute_pricekg(self):
        for line in self:
            line.pricekg = line.price_subtotal / line.x_totalweight if line.x_totalweight else 0

    @api.model
    def create(self, vals):
        # Set x_stage to 21 when a purchase order line is created
        vals['x_stage'] = 21

        return super(PurchaseOrderLine, self).create(vals)