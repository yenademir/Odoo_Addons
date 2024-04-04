from odoo import models, fields, api

class PurchaseBlanketOrder(models.Model):
    _inherit = 'purchase.blanket.order'

    invoiced_total = fields.Monetary(compute='_compute_totals', store=True, string='Invoiced Total')
    ordered_total = fields.Monetary(compute='_compute_totals', store=True, string='Ordered Total')
    remaining_invoice_total = fields.Monetary(compute='_compute_totals', store=True, string='Remaining to Invoice Total')
    remaining_total = fields.Monetary(compute='_compute_totals', store=True, string='Remaining Total')


    @api.depends('line_ids.invoiced_subtotal', 'line_ids.ordered_subtotal', 'line_ids.remaining_invoice_subtotal', 'line_ids.remaining_subtotal','amount_untaxed')
    def _compute_totals(self):
        for order in self:
            order.invoiced_total = sum(line.invoiced_subtotal for line in order.line_ids)
            order.ordered_total = sum(line.ordered_subtotal for line in order.line_ids)
            order.remaining_invoice_total = sum(line.remaining_invoice_subtotal for line in order.line_ids)
            order.remaining_total = sum(line.remaining_subtotal for line in order.line_ids)
            if order.ordered_total > 0 and order.amount_untaxed > 0 and order.ordered_total == order.amount_untaxed:
                order.state = 'done'

class PurchaseBlanketOrderLine(models.Model):
    _inherit = 'purchase.blanket.order.line'

    invoiced_subtotal = fields.Monetary(compute='_compute_subtotals', string='Invoiced Subtotal')
    ordered_subtotal = fields.Monetary(compute='_compute_subtotals', string='Ordered Subtotal')
    remaining_invoice_subtotal = fields.Monetary(compute='_compute_subtotals', string='Remaining Invoice Subtotal')
    remaining_subtotal = fields.Monetary(compute='_compute_subtotals', string='Remaining Subtotal')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('done', 'Done'),
        ('expired', 'Expired'),
    ], string='State', related='order_id.state', store=True, readonly=True)
    partner_ref = fields.Char(
        string='Partner Reference',
        related='order_id.partner_ref',  
        readonly=True, 
        store=True,  
    )
    
    @api.depends('invoiced_uom_qty', 'ordered_uom_qty', 'original_uom_qty', 'price_unit')
    def _compute_subtotals(self):
        for line in self:
            line.invoiced_subtotal = line.invoiced_uom_qty * line.price_unit
            line.ordered_subtotal = line.ordered_uom_qty * line.price_unit
            line.remaining_invoice_subtotal = (line.original_uom_qty - line.invoiced_uom_qty) * line.price_unit
            line.remaining_subtotal = (line.original_uom_qty - line.ordered_uom_qty) * line.price_unit
