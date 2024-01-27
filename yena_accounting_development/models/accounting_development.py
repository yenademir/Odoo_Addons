from odoo import models, fields, api

class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    customer_reference = fields.Char(string='Müşteri Referansı')

    @api.model
    def create(self, vals):
        sale_line_id = vals.get('sale_line_ids', [])
        if sale_line_id:
            sale_line = self.env['sale.order.line'].browse(sale_line_id[0][2][0])  # sale_line_ids alanından ilk sale.order.line ID'sini alır
            if sale_line and sale_line.order_id:
                vals['customer_reference'] = sale_line.order_id.customer_reference
        return super(AccountMoveLineInherit, self).create(vals)

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    customer_references = fields.Char(string='Müşteri Referansları', compute='_compute_customer_references')

    @api.depends('invoice_line_ids.customer_reference')
    def _compute_customer_references(self):
        for record in self:
            references = record.invoice_line_ids.mapped('customer_reference')
            # Boş olmayan ve string türündeki değerleri filtrele
            valid_references = {ref for ref in references if ref and isinstance(ref, str)}
            # Benzersiz string değerleri virgülle birleştir
            record.customer_references = ','.join(valid_references)
