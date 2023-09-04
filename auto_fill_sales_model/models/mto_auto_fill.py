from odoo import models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        current_user = self.env.user  # Şu anki kullanıcıyı al
        incoterm = self.env['account.incoterms'].browse(10)

        # Tüm satış siparişleri için döngü başlat
        for order in self:
            # İlişkili tüm satın alma siparişlerini bul
            purchase_orders = self.env['purchase.order'].search([('origin', '=', order.name)])
            # İlişkili tüm satın alma siparişlerini güncelle
            for purchase_order in purchase_orders:
                purchase_order.write({
                    'user_id': current_user.id,  # Mevcut kullanıcıyı user_id alanına yaz
                    'x_customer_ref': order.x_customer_reference,
                    'x_project_purchase': order.x_project_sales.id,
                    'incoterm_id': incoterm.id
                })
                # İlişkili tüm satın alma sipariş satırlarını güncelle
                for po_line in purchase_order.order_line:
                    # Satış siparişi satırını, ürün kimliği ile eşleştir
                    # Satış siparişi satırlarını, ürün kimliği ile eşleştir
                    so_lines = order.order_line.filtered(lambda line: line.product_id == po_line.product_id)
                    for so_line in so_lines:  # Bu döngü, her bir satış sipariş satırı için çalışır
                        new_price_unit = so_line.price_unit * 0.72  # Satış fiyatını 0.72 ile çarp
                        po_line.write({
                            'price_unit': new_price_unit,  # Yeni fiyatı güncelle
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
