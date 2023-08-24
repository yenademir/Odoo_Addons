from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_send_account_sales(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            # Burada kullandığınız e-posta şablonunun ID'sini alın
            template_id = ir_model_data._xmlid_lookup('contact_send_mail.email_template_balance_letter')[2]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'res.partner',
            'active_model': 'res.partner',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True,
        }

        data = {'ids': self.ids}  
        
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'data': data,
        }
