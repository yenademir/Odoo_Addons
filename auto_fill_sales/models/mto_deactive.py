from odoo import models, api

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    def _run_buy(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        # Belirli bir şirket için satın alma işlemlerini engelle
        if self.env.company.id == 1:
            return
        super()._run_buy(product_id, product_qty, product_uom, location_id, name, origin, values)
