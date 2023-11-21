from odoo import api, fields, models

class VehicleType(models.Model):
    _name = 'vehicle.type'
    _description = 'Vehicle Type'

    name = fields.Char(string='Name', required=True)
