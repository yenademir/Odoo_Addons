from odoo import api, fields, models
import logging
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    bid_time=fields.Char(string="Bid Time")
    contact_id = fields.Many2one('res.partner', string='Contact Person', store=True)
    customer_reference=fields.Char(string="Customer Reference No", store=True)
    delivery_date=fields.Char(string="C-Delivery Date (Text)")
    invoice_report=fields.Selection([("fullyinvoiced","Fully Invoiced"),("partiallyinvoice","Partially Invoiced"),("nothinginvoiced","Nothing Invoiced")],string="Invoice Report")
    lost=fields.Many2one("crm.lost.reason",string="Lost Reason")
    lost_reason=fields.Many2one("crm.lost.reason",string="Lost Reason")
    project_sales=fields.Many2one("project.project",string="Project Number", store=True)
    quo_date=fields.Date(string="C-Quotation Date")
    rfq_date=fields.Date(string="C-RFQ Date")
    rfq_reference=fields.Char(string="RFQ Reference", store=True)
    is_current_user = fields.Boolean(compute='_compute_is_current_user')
    account_note = fields.Html(string="Account Note")

    @api.model
    def create(self, vals):

        company_id = vals.get('company_id', False)
        if company_id == 1:
            return super().create(vals)

        # customer_reference'ın rfq_reference'a kopyalandığını kontrol edin.
        if 'customer_reference' in vals and vals['customer_reference']:
            vals['rfq_reference'] = vals['customer_reference']

        # rfq_date'i bugünün tarihi ile doldurun.
        vals['rfq_date'] = fields.Date.today()

        record = super().create(vals)

        if not record.customer_reference:
            return record

        # satış oluşturulduktan sonra bir proje oluştur.
        project_vals = {
            'name': record.name + '-' + record.customer_reference,
            'partner_id': record.partner_id.id,
            # ... Daha fazla alanı burada ekleyebilirsiniz.
        }
        project = self.env['project.project'].create(project_vals)

        # Proje oluşturulduktan sonra analitik hesap ID'yi al
        analytic_account_id = project.analytic_account_id.id if project.analytic_account_id else None

        # Son olarak, satışa analitik hesabı ve proje ID'yi ekleyin.
        record.write({
            'analytic_account_id': analytic_account_id,
            'project_sales': project.id,
            'company_id': 2,
        })

        return record

    def action_confirm(self):

        # C-Delivery Date kontrolü
        if not self.commitment_date:
            raise UserError('The C-Delivery Date is mandatory! Please add this date and try again.')

        # company_id 1 ise, özel işlem yap
        if self.company_id.id == 1:
            # Standart onay işlemi yapılır
            res = super(SaleOrder, self).action_confirm()
            
            for order in self:
                # İlgili transfer emirlerini bul ve güncelle
                delivery_orders = self.env['stock.picking'].search([('origin', '=', order.name)])
                for delivery_order in delivery_orders:
                    delivery_order.write({
                        'project_transfer': [(6, 0, order.project_sales.ids)],
                    })
        
                return res

        # Diğer durumlarda, öncelikle standart onay işlemi yapılır
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
                    'customer_reference': order.customer_reference,
                    'project_purchase': order.project_sales.id,
                    'incoterm_id': incoterm.id
                })
                # İlişkili tüm satın alma sipariş satırlarını güncelle
                for po_line in purchase_order.order_line:
                    # Satış siparişi satırını, ürün kimliği ile eşleştir
                    so_line = order.order_line.filtered(lambda line: line.product_id == po_line.product_id)
                    if so_line:
                        new_price_unit = so_line.price_unit * 0.92  # Satış fiyatını 0.72 ile çarp
                        po_line.write({
                            'price_unit': new_price_unit,  # Yeni fiyatı güncelle
                            'account_analytic_id': order.analytic_account_id.id,
                        })

            # İlişkili tüm teslimat emirlerini bul
            delivery_orders = self.env['stock.picking'].search([('origin', '=', order.name)])
            # İlişkili tüm teslimat emirlerini güncelle
            for delivery_order in delivery_orders:
                delivery_order.write({
                    'project_transfer': [(6, 0, order.project_sales.ids)],
                })
                
        # Eğer customer_reference değiştiyse analitik hesap ve proje adını güncelle
        if self.rfq_reference != self.customer_reference:
            project = self.project_sales
            project.write({
                'name': self.name + '-' + self.customer_reference
            })
            analytic_account = self.analytic_account_id
            analytic_account.write({
                'name': project.name
            })
        return res

    def action_quotation_sent(self):
        res = super(SaleOrder, self).action_quotation_sent()

        # Quotation gönderildiğinde quo_date'i güncelle
        for record in self:
            record.write({
                'quo_date': fields.Date.today(),
            })

        return res

    @api.onchange('delivery_date')
    def _onchange_delivery_date(self):
        for line in self.order_line:
            line.product_delivery_date = self.delivery_date

    @api.depends('user_id')
    def _compute_is_current_user(self):
        for record in self:
            record.is_current_user = record.user_id == self.env.user

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.contact_id = False
        return {'domain': {'contact_id': [('parent_id', '=', self.partner_id.id), ('type', '=', 'contact')]}}

    def print_proposal_form(self):
        # id'si 2298 olan raporu indir
        return self.env.ref('__export__.ir_act_report_xml_2298_852ac486').report_action(self)

class SaleOrderLine(models.Model):
        _inherit = 'sale.order.line'

        product_delivery_date = fields.Date(string="Product Delivery Date")


#Intercompany & autofill

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _inter_company_create_sale_order(self, dest_company):
        super(PurchaseOrder, self)._inter_company_create_sale_order(dest_company)

        # Satın almadan satışa aktarılacak verileri alın
        purchase_order = self.env['purchase.order'].browse(self.id)

        project = purchase_order.project_purchase
        if project and hasattr(project, 'analytic_account_id') and project.analytic_account_id:
            analytic_account_id = project.analytic_account_id.id
        else:
            analytic_account_id = False

        # Şirket ve partner koşulları
        if purchase_order.company_id.id == 2 and purchase_order.partner_id.id == 1:
            # Satış siparişi değerleri
            sale_order_vals = {
                'project_sales': project.id if project else False,
                'analytic_account_id': analytic_account_id,
                'customer_reference': purchase_order.customer_reference,
            }

            # Satış siparişini bulun
            sale_order = self.env['sale.order'].search([('auto_purchase_order_id', '=', self.id)], limit=1)
            sale_order.write(sale_order_vals)

            # Satın alma siparişi satırlarını döngüleyin ve satış siparişi satırlarını güncelleyin
            for po_line, so_line in zip(purchase_order.order_line, sale_order.order_line):
                sale_line_vals = {
                    'price_unit': po_line.price_unit,
                }
                so_line.write(sale_line_vals)
