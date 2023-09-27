from odoo import models

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        result = super(MailComposeMessage, self).action_send_mail()
        if self._context.get('default_model') == 'call.for.vendors.line' and self._context.get('default_res_id'):
            order = self.env['purchase.order'].browse(self._context['default_res_id'])
            order.portal_status = 'revision_requested'
        return result