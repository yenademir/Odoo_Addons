from odoo import _, models, fields, api
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    call_for_vendors_id = fields.Many2one('call.for.vendors', string='Related Call for Vendors')
    custom_attachment_ids = fields.Many2many(
        'ir.attachment', 'purchase_order_attachment_rel',
        'purchase_order_id', 'attachment_id',
        string='Attachments'
    )
    portal_status = fields.Selection([
        ('offer', 'Teklif'),
        ('offer_requested', 'Teklif İstendi'),
        ('offer_received', 'Teklif Geldi'),
        ('revision_requested', 'Revize Talep Edildi'),
        ('revision_received', 'Revize Geldi'),
        ('purchase_sent', 'Satınalma Gönderildi'),
        ('purchase_approved', 'Satınalma Onaylandı'),
    ], string="Portal Status", default='offer',)

    @api.model
    def button_confirm_portal(self, order_id):
        order = self.browse(order_id)
        if not order:
            return {'success': False, 'error': 'Order not found.'}
        order.write({'portal_status': 'purchase_approved'})
        return {'success': True}

    @api.model
    def update_custom_data_portal(self, order_id, custom_prices, custom_dates):

        order = self.browse(order_id)
        if not order:
            return {'success': False, 'error': 'Order not found.'}

        # portal_status'u güncelleme
        if order.portal_status == 'offer_requested':
            order.portal_status = 'offer_received'
        elif order.portal_status == 'revision_requested':
            order.portal_status = 'revision_received'

        for line, price, date in zip(order.order_line, custom_prices, custom_dates):
            # Only allow changing price_unit and date_planned
            line.write({
                'price_unit': float(price) if price else line.price_unit,
                'date_planned': date if date else line.date_planned
            })

        self._send_notification_email(order)

        return {'success': True}

    def button_request_revision(self):
        for record in self:
            record.portal_status = 'revision_requested'

    def _send_notification_email(self, order):
        # Eğer belirli bir e-posta şablonu kullanacaksanız:
        template = self.env.ref(
            'purchase_portal.email_template_send_price')
        if template:
            template.send_mail(order.id, force_send=True)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    call_for_vendors_id = fields.Many2one('call.for.vendors', string='Related Call for VAF', ondelete='set null')
    is_cheapest = fields.Boolean(string="Is Cheapest", compute="_compute_best_rfqs")
    is_earliest = fields.Boolean(string="Is Earliest", compute="_compute_best_rfqs")
    approved = fields.Boolean(string='Approved')
    cancelled = fields.Boolean(string='Cancelled')

    def write(self, vals):
        # Önceki fiyatları elde et
        old_values = {line.id: line.price_unit for line in self}

        # write fonksiyonunu orijinal şekliyle çalıştır
        res = super(PurchaseOrderLine, self).write(vals)

        # Fiyat değişikliklerini toplamak için bir liste oluştur
        changes = []

        # Her bir satır için, önceki fiyatla şimdiki fiyatı karşılaştır
        for line in self:
            old_price = old_values.get(line.id)
            if old_price and old_price != line.price_unit:
                changes.append(_('%s: %s -> %s') % (line.product_id.name, old_price, line.price_unit))

        # Eğer bu fonksiyon birden fazla kere çağrılmışsa, bu değişiklikleri biriktirin
        if self.env.context.get('changes_accumulator') is not None:
            self.env.context.get('changes_accumulator').extend(changes)
        else:
            if changes:
                message = '<br/>'.join(changes)
                self[0].order_id.message_post(body=message)

        return res

    def button_approve(self):
        self.write({'approved': True, 'cancelled': False})

    def button_cancel(self):
        self.write({'approved': False, 'cancelled': True})

    @api.depends('price_unit', 'date_planned')
    def _compute_best_rfqs(self):
        for line in self:
            other_lines = self.search([
                ('product_id', '=', line.product_id.id),
                ('call_for_vendors_id', '=', line.call_for_vendors_id.id)
            ])

            min_price = min(other_lines.mapped('price_unit'))
            earliest_date = min(other_lines.mapped('date_planned'))

            line.is_cheapest = line.price_unit == min_price
            line.is_earliest = line.date_planned == earliest_date
