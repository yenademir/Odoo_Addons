from odoo import api, fields, models

class TimeSheet(models.Model):
    _inherit = 'account.analytic.line'
    planned_hours = fields.Float(
        string='Hours Planned',
        readonly=False,
        store=True
    )
