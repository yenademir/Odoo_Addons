from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    contact_type = fields.Selection([
        ('potential_vendor', 'Potential Vendor'),
        ('potential_customer', 'Potential Customer')
    ], string='Contact Type',
    )

    contact_status = fields.Many2many(
        'res.partner.contact.status',
        'partner_status_rel',
        'partner_id',
        'status_id',
        string='Contact Status',
        compute='_compute_contact_status',
        readonly=False,
        store=True
    )

    contact_status_visibility = fields.Boolean(compute='_compute_contact_status_visibility')

    @api.depends('contact_status')
    def _compute_contact_status_visibility(self):
        for record in self:
            status_names = record.contact_status.mapped('name')
            if 'Vendor' in status_names or 'Customer' in status_names:
                record.contact_status_visibility = True
            else:
                record.contact_status_visibility = False

    @api.depends('invoice_ids', 'invoice_ids.move_type', 'contact_type')
    def _compute_contact_status(self):
        vendor_status = self.env['res.partner.contact.status'].search([('name', '=', 'Vendor')], limit=1)
        customer_status = self.env['res.partner.contact.status'].search([('name', '=', 'Customer')], limit=1)

        for partner in self:
            status_ids = self.env['res.partner.contact.status']

            if partner.invoice_ids.filtered(lambda inv: inv.move_type == 'in_invoice'):
                status_ids |= vendor_status
                partner.contact_type = False

            if partner.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice'):
                status_ids |= customer_status
                partner.contact_type = False

            partner.contact_status = status_ids


class ResPartnerContactStatus(models.Model):
    _name = 'res.partner.contact.status'
    _description = 'Contact Status'

    name = fields.Char("Status")
