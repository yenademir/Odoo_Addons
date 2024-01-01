from odoo import api, fields, models

class TimeSheet(models.Model):
    _inherit = 'account.analytic.line'
    planned_hours = fields.Float(
        string='Hours Planned',
        related="task_id.planned_hours",
        readonly=False
    )


    @api.onchange('planned_hours')
    def _onchange_planned_hours(self):
        for line in self:
            if line.task_id:
                line.task_id.write({'planned_hours': line.planned_hours})