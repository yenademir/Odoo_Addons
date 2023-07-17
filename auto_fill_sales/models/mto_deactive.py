from odoo import models

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_confirm(self, merge=True, merge_into=False):
        # 'YENA DEMİR ÇELİK' şirketi aktifken,
        # '_action_confirm' metodu hiçbir şey yapmaz ve hemen çıkar.
        # Bu, bir satış siparişi onaylandığında otomatik satınalma siparişi oluşturmayı engeller.
        if self.env.company.id == 1:
            return self

        # 'YENA DEMİR ÇELİK' şirketi aktif değilken,
        # '_action_confirm' metodu normal şekilde çalışır.
        return super()._action_confirm(merge=merge, merge_into=merge_into)
