from odoo import models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        # Tüm satış siparişleri için döngü başlat
        for order in self:
            # İlişkili tüm satın alma siparişlerini bul
            purchase_orders = self.env['purchase.order'].search([('origin', '=', order.name)])
            # İlişkili tüm satın alma siparişlerini güncelle
            for purchase_order in purchase_orders:
                purchase_order.write({
                    'x_customer_ref': order.x_customer_reference,
                    'x_project_purchase': order.x_project_sales.id,
                })
                # İlişkili tüm satın alma sipariş satırlarını güncelle
                for line in purchase_order.order_line:
                    line.write({
                        'account_analytic_id': order.analytic_account_id.id,
                    })

            # İlişkili tüm teslimat emirlerini bul
            delivery_orders = self.env['stock.picking'].search([('origin', '=', order.name)])
            # İlişkili tüm teslimat emirlerini güncelle
            for delivery_order in delivery_orders:
                delivery_order.write({
                    'x_project_transfer': [(6, 0, order.x_project_sales.ids)],
                })

        return res
