from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    status = fields.Selection([
        ('phase1', 'Phase-1'),
        ('phase2', 'Phase-2'),
        ('phase3', 'Phase-3'),
    ], string='Durum', default='phase1', required=True, tracking=True, store=True)