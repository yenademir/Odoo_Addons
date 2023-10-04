# my_module/models/partner.py
from odoo import models, fields, api
from odoo.exceptions import UserError
class ResPartner(models.Model):
    _inherit = 'res.partner'

    email = fields.Char(string='Email', required=True)

    @api.constrains('email')
    def _check_unique_email(self):
        for partner in self:
            if partner.email:
                existing_partner = self.env['res.partner'].search([('email', '=', partner.email), ('id', '!=', partner.id)])
                if existing_partner:
                    raise UserError('This email address already exists. Please use a different email address.')