from odoo import models, fields, api


class CancelOrderWizard(models.TransientModel):
    _name = 'cancel.order.wizard'
    _description = 'Cancel Order Wizard'

    cancel_reason_id = fields.Many2one(
        'purchase.cancel.reason', string='Cancel Reason', required=True)

    def action_cancel_order(self):
        self.ensure_one()
        order = self.env['purchase.order'].browse(
            self.env.context.get('active_id'))
        order.cancel_reason_id = self.cancel_reason_id
        order.button_cancel()
        order.state = 'cancel'
