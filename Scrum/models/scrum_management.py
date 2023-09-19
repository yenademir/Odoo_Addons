from odoo import api, fields, models

class Scrum(models.Model):
    _name = 'scrum.project'

    name = fields.Char(string='Name', required=True)
    team = fields.Char(string='Team')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    estimated_story_point = fields.Float(string='Estimated Story Points', compute='_compute_estimated_story_point', store=True, readonly=True)
    result_story_point = fields.Float(string='Result Story Points', compute='_compute_result_story_point', store=True)
    line_ids = fields.One2many('scrum.line', 'scrum_project_id', string='Scrum Lines')

    @api.depends('line_ids.story_point')
    def _compute_estimated_story_point(self):
        for record in self:
            record.estimated_story_point = sum(line.story_point for line in record.line_ids)

class ScrumLine(models.Model):
    _name = 'scrum.line'
    _description = 'Scrum Line'

    scrum_project_id = fields.Many2one('scrum.project', string='Scrum Project', required=True, ondelete='cascade')
    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    task_id = fields.Many2one(
        'project.task', 'Task', readonly=False, index=True,
        domain="[('project_id', '=?', project_id)]")
    user_ids = fields.Many2many(related='task_id.user_ids', string="Users", readonly=True)
    story_point = fields.Float(related='task_id.story_point', string='Story Point', readonly=True)
    date_deadline = fields.Date(related='task_id.date_deadline', string='Deadline', readonly=True)
    stage_id = fields.Many2one(related='task_id.stage_id', string='Stage')

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            return {'domain': {'task_id': [('project_id', '=', self.project_id.id)]}}
        return {'domain': {'task_id': []}}

    @api.onchange('task_id')
    def _onchange_task_id(self):
        pass

class Task(models.Model):
    _inherit = 'project.task'

    story_point = fields.Float(string='Story Point')
    scrum_project_id = fields.Many2many('scrum.project', string='Scrum Project')  # Many2many olarak değiştirildi

    @api.model
    def create(self, vals):
        task = super(Task, self).create(vals)
        if 'scrum_project_id' in vals:
            for scrum_project_id in vals['scrum_project_id'][0][2]:
                self.env['scrum.line'].create({
                    'scrum_project_id': scrum_project_id,
                    'project_id': task.project_id.id,
                    'task_id': task.id,
                })
        return task

    def write(self, vals):
        result = super(Task, self).write(vals)
        if 'scrum_project_id' in vals:  # Many2many olarak değiştirildi
            for task in self:
                scrum_lines = self.env['scrum.line'].search([('task_id', '=', task.id)])
                scrum_lines.unlink()  # İlgili tüm scrum.line kayıtlarını sil
                for scrum_project_id in vals['scrum_project_id'][0][2]:
                    self.env['scrum.line'].create({
                        'scrum_project_id': scrum_project_id,
                        'project_id': task.project_id.id,
                        'task_id': task.id,
                    })
        return result
