from odoo import models, fields,api
 
class SalePriceHistory(models.Model):
    _name = 'sale.price.history'
    _description = 'Sale Price History'
        
    order_id = fields.Many2one('sale.order', string='Order Reference')
    order_name = fields.Char(string='Order Number')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', string='Customer')
    price = fields.Float(string='Price')
    cancelled_reasons=fields.Char(string="Cancelled Reasons")
    lost_reason=fields.Char(string="Lost Reasons")
    weight = fields.Float(string="Weight")
    project_number = fields.Many2one('project.project', string="Project Number")
    date = fields.Date(string='Date')
    status = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status')
 
class PurchasePriceHistory(models.Model):
    _name = 'purchase.price.history'
    _description = 'Purchase Price History'
    
    order_id = fields.Many2one('sale.order', string='Order Reference')
    order_name = fields.Char(string='Order Number')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', string='Supplier')
    price = fields.Float(string='Price')
    cancelled_reasons=fields.Char(string="Cancelled Reasons")
    weight = fields.Float(string="Weight")
    project_number = fields.Many2one('project.project', string="Project Number")

    date = fields.Date(string='Date')
    status = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('purchase', 'Purchase Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status')
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_price_history_ids = fields.One2many('sale.price.history', 'order_id', string='Sale Price History')
    purchase_price_history_ids = fields.One2many('purchase.price.history', 'order_id', string='Purchase Price History')
    
    def delete_price_history(self):
       self.ensure_one()  # İşlemi yalnızca tek bir kayıt üzerinde gerçekleştiriyoruz.
       
       # İlgili sale.price.history kayıtlarını bul ve sil
       sale_price_histories = self.env['sale.price.history'].search([('order_id', '=', self.id)])
       sale_price_histories.unlink()
       
       # İlgili purchase.price.history kayıtlarını bul ve sil
       purchase_price_histories = self.env['purchase.price.history'].search([('order_id', '=', self.id)])
       purchase_price_histories.unlink()
   
       return True
    def update_price_history(self):
        self.ensure_one()
        existing_sale_price_histories = set(self.env['sale.price.history'].search([('order_id', 'in', self.ids)]).mapped(lambda r: (r.product_id.id, r.order_id.id)))
        existing_purchase_price_histories = set(self.env['purchase.price.history'].search([('order_id', 'in', self.ids)]).mapped(lambda r: (r.product_id.id, r.order_id.id)))

        sale_price_history_data = []
        purchase_price_history_data = []

        for line in self.order_line:
            sale_orders = self.env['sale.order.line'].search([('product_id', '=', line.product_id.id), ('state', 'in', ['sale', 'done', 'cancel'])])
            for sale_order in sale_orders:
                if sale_order.order_id.partner_id.id == 63532:
                   continue
                 
                if (sale_order.product_id.id, sale_order.order_id.id) not in existing_sale_price_histories:
                    sale_price_history_data.append((0, 0, {
                        'product_id': sale_order.product_id.id,
                        'order_name': sale_order.order_id.name,
                        'weight': sale_order.product_id.weight,
                        'project_number': sale_order.order_id.project_sales.id,
                        'partner_id': sale_order.order_id.partner_id.id,
                        'price': sale_order.price_unit,
                        'cancelled_reasons': sale_order.order_id.quota_cancel_reason_id.name if sale_order.order_id.quota_cancel_reason_id else '',
                        'lost_reason': sale_order.order_id.lost_reason.name if sale_order.order_id.lost_reason else '',
                        'date': sale_order.order_id.date_order,
                        'status': sale_order.state,
                    }))

            # Satın alma siparişleri için tarihçe güncellemesi
            purchase_orders = self.env['purchase.order.line'].search([('product_id', '=', line.product_id.id), ('state', 'in', ['purchase', 'done', 'cancel'])])
            for purchase_order in purchase_orders:
                if purchase_order.order_id.partner_id.id == 1:
                   continue
                 
                if (purchase_order.product_id.id, purchase_order.order_id.id) not in existing_purchase_price_histories:
                    purchase_price_history_data.append((0, 0, {
                        'product_id': purchase_order.product_id.id,
                        'order_name': purchase_order.order_id.name,
                        'weight': purchase_order.product_id.weight,
                        'project_number': purchase_order.order_id.project_purchase.id,
                        'partner_id': purchase_order.order_id.partner_id.id,
                        'price': purchase_order.price_unit,
                        'cancelled_reasons': purchase_order.order_id.cancel_reason_id.name if purchase_order.order_id.cancel_reason_id else '',
                        'date': purchase_order.order_id.date_order,
                        'status': purchase_order.state,
                    }))

        self.write({
            'sale_price_history_ids': sale_price_history_data,
            'purchase_price_history_ids': purchase_price_history_data,
        })
