from odoo import http
from odoo.http import request

class CurrencyController(http.Controller):

    @http.route('/get_currencies', type='json', auth='public')
    def get_currencies(self):
        currencies = request.env['res.currency'].sudo().search([])
        currency_data = []
        for currency in currencies:
            currency_data.append({'id': currency.id, 'name': currency.name})
        return currency_data
