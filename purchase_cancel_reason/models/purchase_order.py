from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    cancel_reason_id = fields.Many2one(
        'purchase.cancel.reason', string='Cancel Reason')

    def button_cancel(self):
        return {
            'name': 'Add Reason',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cancel.order.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
