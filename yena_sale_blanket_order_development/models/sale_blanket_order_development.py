from odoo import models, fields, api

class SaleBlanketOrder(models.Model):
    _inherit = 'sale.blanket.order'

    invoiced_total = fields.Monetary(compute='_compute_totals', string='Invoiced Total')
    ordered_total = fields.Monetary(compute='_compute_totals', string='Ordered Total')
    remaining_invoice_total = fields.Monetary(compute='_compute_totals', string='Remaining to Invoice Total')
    remaining_total = fields.Monetary(compute='_compute_totals', string='Remaining Total')

    @api.depends('line_ids.invoiced_subtotal', 'line_ids.ordered_subtotal', 'line_ids.remaining_invoice_subtotal', 'line_ids.remaining_subtotal')
    def _compute_totals(self):
        for order in self:
            order.invoiced_total = sum(line.invoiced_subtotal for line in order.line_ids)
            order.ordered_total = sum(line.ordered_subtotal for line in order.line_ids)
            order.remaining_invoice_total = sum(line.remaining_invoice_subtotal for line in order.line_ids)
            order.remaining_total = sum(line.remaining_subtotal for line in order.line_ids)

class SaleBlanketOrderLine(models.Model):
    _inherit = 'sale.blanket.order.line'

    invoiced_subtotal = fields.Monetary(compute='_compute_subtotals', string='Invoiced Subtotal')
    ordered_subtotal = fields.Monetary(compute='_compute_subtotals', string='Ordered Subtotal')
    remaining_invoice_subtotal = fields.Monetary(compute='_compute_subtotals', string='Remaining Invoice Subtotal')
    remaining_subtotal = fields.Monetary(compute='_compute_subtotals', string='Remaining Subtotal')

    @api.depends('invoiced_uom_qty', 'ordered_uom_qty', 'original_uom_qty', 'price_unit')
    def _compute_subtotals(self):
        for line in self:
            line.invoiced_subtotal = line.invoiced_uom_qty * line.price_unit
            line.ordered_subtotal = line.ordered_uom_qty * line.price_unit
            line.remaining_invoice_subtotal = (line.original_uom_qty - line.invoiced_uom_qty) * line.price_unit
            line.remaining_subtotal = (line.original_uom_qty - line.ordered_uom_qty) * line.price_unit
