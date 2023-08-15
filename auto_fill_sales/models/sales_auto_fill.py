from odoo import api, fields, models
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_rfq_reference = fields.Char(string='RFQ Reference')
    x_contact_id = fields.Many2one('res.partner', string='Contact Person')
    is_current_user = fields.Boolean(compute='_compute_is_current_user')

    @api.depends('user_id')
    def _compute_is_current_user(self):
        for record in self:
            record.is_current_user = record.user_id == self.env.user

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.x_contact_id = False
        return {'domain': {'x_contact_id': [('parent_id', '=', self.partner_id.id), ('type', '=', 'contact')]}}

    @api.model
    def create(self, vals):

        company_id = vals.get('company_id', False)
        if company_id == 1:
            return super().create(vals)

        # x_customer_reference'ın x_rfq_reference'a kopyalandığını kontrol edin.
        if 'x_customer_reference' in vals and vals['x_customer_reference']:
            vals['x_rfq_reference'] = vals['x_customer_reference']

        # x_rfq_date'i bugünün tarihi ile doldurun.
        vals['x_rfq_date'] = fields.Date.today()

        record = super().create(vals)

        if not record.x_customer_reference:
            return record

        # Eğer x_customer_reference boş ise, daha fazla işlem yapma.
        if not record.x_customer_reference:
            return record

        # satış oluşturulduktan sonra bir proje oluştur.
        project_vals = {
            'name': record.name + '-' + record.x_customer_reference,
            'partner_id': record.partner_id.id,
            # ... Daha fazla alanı burada ekleyebilirsiniz.
        }
        project = self.env['project.project'].create(project_vals)

        # Proje oluşturulduktan sonra analitik hesap ID'yi al
        analytic_account_id = project.analytic_account_id.id if project.analytic_account_id else None

        # Son olarak, satışa analitik hesabı ve proje ID'yi ekleyin.
        record.write({
            'analytic_account_id': analytic_account_id,
            'x_project_sales': project.id,
        })

        return record

    def action_confirm(self):
        if self.company_id.id == 1:
            return super().action_confirm()

        res = super().action_confirm()

        # Eğer x_customer_reference değiştiyse analitik hesap ve proje adını güncelle
        if self.x_rfq_reference != self.x_customer_reference:
            project = self.x_project_sales
            project.write({
                'name': self.name + '-' + self.x_customer_reference
            })
            analytic_account = self.analytic_account_id
            analytic_account.write({
                'name': project.name
            })
        return res

    def action_quotation_sent(self):
        res = super(SaleOrder, self).action_quotation_sent()

        # Quotation gönderildiğinde x_quo_date'i güncelle
        for record in self:
            record.write({
                'x_quo_date': fields.Date.today(),
            })

        return res

    def action_mark_as_sent(self):
        res = super(SaleOrder, self).action_mark_as_sent()

        # Quotation gönderildi olarak işaretlendiğinde x_quo_date'i güncelle
        for record in self:
            record.write({
                'x_quo_date': fields.Date.today(),
            })

        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    pricekg = fields.Float(compute='_compute_pricekg', string='EURkg', readonly=True, store=True)

    @api.depends('price_subtotal', 'x_totalweight')
    def _compute_pricekg(self):
        for line in self:
            line.pricekg = line.price_subtotal / line.x_totalweight if line.x_totalweight else 0
