from odoo import api, models

class IrAttachmentInherit(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def check(self, mode, values=None):
        # Portal kullanıcısı kontrolü ve sadece okuma izni istendiğinde
        if mode == 'read' and self.env.user.has_group('base.group_portal'):
            return True
        # Diğer durumlarda orijinal kontrolü çalıştır
        return super(IrAttachmentInherit, self).check(mode, values)