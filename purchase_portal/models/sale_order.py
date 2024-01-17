from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    call_for_vendors_id = fields.Many2one('call.for.vendors', string='Related Call for Vendors')

    def action_create_call_for_vendors(self):
        CallForVendors = self.env['call.for.vendors']

        CallForVendorsLine = self.env['call.for.vendors.line']

        for record in self:
            # Check if the sale.order record is already in the call.for.vendors model
            call_for_vendors_record = CallForVendors.search([('sale_order_id', '=', record.id)], limit=1)
            vals = {
                'sale_order_id': record.id,
                'partner_id': record.partner_id.id,
                'incoterm': record.incoterm.id,
                'payment_term_id': record.payment_term_id.id,
                'commitment_date': record.commitment_date,
                'customer_reference': record.customer_reference,
                'project_sales': record.project_sales.id,
                'analytic_account_id': record.analytic_account_id.id,
                'notes': record.note,
            }
            if call_for_vendors_record:
                # If the record exists, update it
                call_for_vendors_record.write(vals)
                # Send updated email
                template = self.env.ref('purchase_portal.email_template_updated_call_for_vendors')
            else:
                # If the record does not exist, create it
                call_for_vendors_record = CallForVendors.create(vals)
                # Send new email
                template = self.env.ref('purchase_portal.email_template_new_call_for_vendors')

            template.send_mail(call_for_vendors_record.id, force_send=True)

            for line in record.order_line:
                # Check if the sale.order.line record is already in the call.for.vendors.line model
                call_for_vendors_line_record = CallForVendorsLine.search([
                    ('call_id', '=', call_for_vendors_record.id),
                    ('product_id', '=', line.product_id.id),
                ], limit=1)
                line_vals = {
                    'call_id': call_for_vendors_record.id,
                    'product_id': line.product_id.id,
                    'quantity': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'total_weight': line.totalweight,
                    'delivery_date': line.product_delivery_date,
                    'order_line_id': line.id,
                }
                if call_for_vendors_line_record:
                    # If the record exists, update it
                    call_for_vendors_line_record.write(line_vals)
                else:
                    # If the record does not exist, create it
                    CallForVendorsLine.create(line_vals)
