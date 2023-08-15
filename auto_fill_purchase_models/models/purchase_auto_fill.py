from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_contact_id = fields.Many2one('res.partner', string='Contact Person')
    x_rfq_sent_date = fields.Date('S-RFQ Sent Date')
    x_required_delivery_date = fields.Date('Required Delivery Date')
    is_current_user = fields.Boolean(compute='_compute_is_current_user')

    @api.depends('user_id')
    def _compute_is_current_user(self):
        for record in self:
            record.is_current_user = record.user_id == self.env.user

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
    
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()

        for order in self:

            # İlişkili tüm teslimat emirlerini bul (receipt belgeleri)
            delivery_orders = self.env['stock.picking'].search(
                [('origin', '=', order.name)])
            # İlişkili tüm teslimat emirlerini güncelle
            for delivery_order in delivery_orders:
                delivery_order.write({
                    'x_project_transfer': [(6, 0, order.x_project_purchase.ids)],
                })

        return res

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_product_required_delivery_date = fields.Date('Product Required Delivery Date')
    pricekg = fields.Float(compute='_compute_pricekg', string='EUR/kg', readonly=True, store=True)

    @api.depends('price_subtotal', 'x_totalweight')
    def _compute_pricekg(self):
        for line in self:
            line.pricekg = line.price_subtotal / line.x_totalweight if line.x_totalweight else 0
