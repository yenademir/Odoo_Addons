from odoo import fields, models

class ProductMaterial(models.Model):
    _name = "product.yena_material"

    name = fields.Char(string="Name")

class HsCode(models.Model):
    _name = "yena.hscode"

    name = fields.Char(string="HS Code")
    category = fields.Many2one("product.category", string="Category")
    industry = fields.Many2one("res.partner.industry", string="Industry")
    product_description = fields.Char(string="Product Description",)
    customs_description_tr = fields.Char(string="Customs Description(Türkçe)",)
    customs_description_en = fields.Char(string="Customs Description(English)")
    example_description = fields.Char(string="Well-known Example Product",)
