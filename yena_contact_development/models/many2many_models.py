from odoo import models, fields

class TypeOfMaterial(models.Model):
    _name = "type.material"

    name = fields.Char(string="Name")

class AreaOfExpertise(models.Model):
    _name = "area.expertise"

    name = fields.Char(string="Name")

class Coating(models.Model):
    _name = 'coating'

    name = fields.Char(string="Name")

class Welding(models.Model):
    _name = 'welding'

    name = fields.Char(string="Name")
