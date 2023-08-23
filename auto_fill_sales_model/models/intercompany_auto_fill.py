from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _inter_company_create_sale_order(self, dest_company):
        super(PurchaseOrder, self)._inter_company_create_sale_order(dest_company)

        # Satın almadan satışa aktarılacak verileri alın
        purchase_order = self.env['purchase.order'].browse(self.id)

        project = purchase_order.x_project_purchase
        if project and hasattr(project, 'analytic_account_id') and project.analytic_account_id:
            analytic_account_id = project.analytic_account_id.id
        else:
            analytic_account_id = False

        # Şirket ve partner koşulları
        if purchase_order.company_id.id == 2 and purchase_order.partner_id.id == 1:
            # Satış siparişi değerleri
            sale_order_vals = {
                'x_project_sales': project.id if project else False,
                'analytic_account_id': analytic_account_id,
                'x_customer_reference': purchase_order.x_customer_ref,
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