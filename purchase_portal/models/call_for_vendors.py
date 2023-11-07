from odoo import _, api, fields, models
from .create import process_line, get_suffix

class CallForVendors(models.Model):
    _name = 'call.for.vendors'
    _description = 'Call For Vendors'

    name = fields.Char(string='Name', required=True, copy=False, readonly=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('call.for.vendors'))
    sale_order_id = fields.Many2one('sale.order', string='Related Sale Order')
    partner_id = fields.Many2one('res.partner', string='Customer')
    incoterm = fields.Many2one('account.incoterms', string='C-Incoterm')
    payment_term_id = fields.Many2one('account.payment.term', string='C-Payment Terms')
    commitment_date = fields.Date(string='C-Delivery Date')
    x_project_sales = fields.Many2one('project.project', string='Project Sales', ondelete='set null')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    x_customer_reference = fields.Char(string='Customer Reference')
    notes = fields.Char(string='Notes')
    line_ids = fields.One2many('call.for.vendors.line', 'call_id', string='Lines')
    rfqs = fields.One2many('purchase.order', compute='_compute_rfqs', string='Related RFQs', readonly=False)
    purchases = fields.One2many('purchase.order', compute='_compute_purchases', string='Related Purchases')
    rfqs_line = fields.One2many('purchase.order.line', 'call_for_vendors_id', string='Related RFQs')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'call_for_vendors_attachment_rel',
        'call_id', 'attachment_id', string='Attachments')
    is_cheapest = fields.Boolean(string="Is Cheapest", compute="_compute_best_rfqs")
    is_earliest = fields.Boolean(string="Is Earliest", compute="_compute_best_rfqs")

    def _compute_rfqs(self):
        for record in self:
            rfqs = self.env['purchase.order'].search([
                ('call_for_vendors_id', '=', record.id),
                ('state', 'in', ['draft', 'sent', 'cancel'])
            ])
            record.rfqs = rfqs

    def _compute_purchases(self):
        for record in self:
            purchases = self.env['purchase.order'].search([
                ('call_for_vendors_id', '=', record.id),
                ('state', 'in', ['purchase', 'done'])
            ])
            record.purchases = purchases

    @api.depends('rfqs_line')
    def _compute_best_rfqs(self):
        for record in self:
            best_price = float('inf')
            earliest_date = False
            for line in record.rfqs_line:
                if line.price_unit < best_price:
                    best_price = line.price_unit
                if not earliest_date or line.x_required_delivery_date < earliest_date:
                    earliest_date = line.x_required_delivery_date

            record.is_cheapest = all(line.price_unit == best_price for line in record.rfqs_line)
            record.is_earliest = all(line.x_required_delivery_date == earliest_date for line in record.rfqs_line)

    def open_send_to_rfqs_wizard(self):
        return {
            'name': _('Confirm Send RFQs'),
            'type': 'ir.actions.act_window',
            'res_model': 'call.for.vendors.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('purchase_portal.view_call_for_vendors_wizard').id,
            'target': 'new',
            'context': {'active_id': self.id},
        }

    def open_send_to_purchases_wizard(self):
        # state'i "cancel" olanları filtrele
        filtered_rfqs = self.rfqs.filtered(lambda r: r.state != 'cancel')
        approved_rfqs_lines = self.rfqs_line.filtered(lambda l: l.approved and l.order_id.state != 'cancel')

        context = {
            'default_call_for_vendors_id': self.id,
            'default_rfqs_ids': [(6, 0, filtered_rfqs.ids)],
            'default_rfqs_line_ids': [(6, 0, approved_rfqs_lines.ids)]
        }

        return {
            'name': _('Send Purchases'),
            'type': 'ir.actions.act_window',
            'res_model': 'call.for.vendors.purchase.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('purchase_portal.view_call_for_vendors_purchase_wizard').id,
            'target': 'new',
            'context': context,
        }

    @api.model
    def create(self, vals):
        # RFQ oluşturma veya güncelleme işlevini kaldırdık
        return super(CallForVendors, self).create(vals)

    def write(self, vals):
        # RFQ oluşturma veya güncelleme işlevini kaldırdık
        return super(CallForVendors, self).write(vals)

    def send_to_vendors(self):
        for record in self:
            vendor_to_rfq = {}
            for line in record.line_ids:
                # Wizard üzerindeki vendor_line_ids bilgilerini alıyoruz
                vendor_wizard_lines = self.env['vendor.wizard.line'].browse(
                    self._context.get('active_id')).wizard_id.vendor_line_ids
                products_to_add = process_line(self.env, line, line.partial_line)
                for product in products_to_add:
                    self._manage_rfq_for_vendors(line, self, product, {}, vendor_wizard_lines)

            return record

    def _manage_rfq_for_vendors(self, line, record, product_to_add, vendor_to_rfq, vendor_wizard_lines):
        PurchaseOrder = self.env['purchase.order']
        for vendor in line.vendor_ids:
            rfq = vendor_to_rfq.setdefault(vendor, self._get_or_create_rfq(vendor, record))
            self._manage_rfq_lines(rfq, product_to_add, line, record)

            for vendor_wizard_line in vendor_wizard_lines:
                if vendor_wizard_line.vendor_id == vendor:
                    rfq.write({
                        'notes': vendor_wizard_line.notes,
                        'custom_attachment_ids': [(6, 0, vendor_wizard_line.attachment_ids.ids)]
                    })

    def _get_or_create_rfq(self, vendor, record):
        PurchaseOrder = self.env['purchase.order']
        existing_rfq = PurchaseOrder.search([
            ('partner_id', '=', vendor.id),
            ('call_for_vendors_id', '=', record.id),
            ('state','=','sent'),
            ('portal_status','=','offer_requested'),
            ('x_customer_ref','=', record.x_customer_reference),
            ('x_project_purchase','=', record.x_project_sales.id)

        ], limit=1)
        return existing_rfq or PurchaseOrder.create({
            'partner_id': vendor.id,
            'call_for_vendors_id': record.id,
            'state':'sent',
            'portal_status':'offer_requested',
            'x_customer_ref': record.x_customer_reference,
            'x_project_purchase': record.x_project_sales.id
        })

    def _manage_rfq_lines(self, rfq, product_to_add, line, record):
        PurchaseOrderLine = self.env['purchase.order.line']
        existing_product_in_rfq = PurchaseOrderLine.search([
            ('order_id', '=', rfq.id),
            ('product_id', '=', product_to_add.id)
        ], limit=1)

        if not existing_product_in_rfq:
            PurchaseOrderLine.create({
                'order_id': rfq.id,
                'product_id': product_to_add.id,
                'product_qty': line.quantity,
                'price_unit': 0.0,
                'call_for_vendors_id': record.id,
                'account_analytic_id': record.analytic_account_id.id
            })


class CallForVendorsLine(models.Model):
    _name = 'call.for.vendors.line'
    _description = 'Call For Vendors Line'

    call_id = fields.Many2one('call.for.vendors', string='Call For Vendors')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity')
    product_uom = fields.Many2one('uom.uom', string='UoM')
    delivery_date = fields.Date(string='C-Delivery Date')
    total_weight = fields.Char(string='Total Weight')
    order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    vendor_ids = fields.Many2many('res.partner', string='Vendors')

    rawmaterial_line = fields.Boolean(string='Raw Material')
    cutting_line = fields.Boolean(string='Cutting')
    welding_line = fields.Boolean(string='Welding')
    coating_line = fields.Boolean(string='Coating')
    montage_line = fields.Boolean(string='Montage')
    partial_line = fields.Boolean(string='Partial')

