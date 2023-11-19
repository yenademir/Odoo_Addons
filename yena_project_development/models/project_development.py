from odoo import models,fields,api

class Project(models.Model):
    _inherit='project.project'

    sales_count=fields.Integer(string="Sales", compute="_compute_sales_count")
    purchase_count = fields.Integer(string='Purchases', compute='_compute_purchase_count')
    delivery_count=fields.Integer(string="Delivery Count",compute="_compute_delivery_count")
    #delivery inventory 
    

    def action_show_sales(self):
        self.ensure_one()
        sale_ids = []

        # Batch transferin adı ile eşleşen purchase'ları bul
        sales = self.env['sale.order'].search([('project_sales', '=', self.name)])

        for sale in sales:
            sale_ids.append(sale.id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('id', 'in', sale_ids)],
            'context': {'create': True},
        }
    
    def action_show_purchases(self):
        self.ensure_one()
        purchase_ids = []

        # Batch transferin adı ile eşleşen purchase'ları bul
        sales = self.env['purchase.order'].search([('project_purchase', '=', self.name)])

        for sale in sales:
            purchase_ids.append(sale.id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchases',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', purchase_ids)],
            'context': {'create': True},
        }

    def action_show_transfers(self):
        self.ensure_one()
        transfer_ids = []

        # Batch transferin adı ile eşleşen purchase'ları bul
        sales = self.env['stock.picking'].search([('project_transfer', '=', self.name)])

        for sale in sales:
            transfer_ids.append(sale.id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', transfer_ids)],
            'context': {'create': False},
        }
    

    def _compute_purchase_count(self):
         for project in self:
             purchases = self.env['purchase.order'].search([
                 ('project_purchase', '=', project.name)
             ])
             project.purchase_count = len(purchases)

    def _compute_sales_count(self):
         for project in self:
             sales = self.env['sale.order'].search([
                 ('project_sales', '=', project.name)
             ])
             project.sales_count = len(sales)

    def _compute_delivery_count(self):
         for project in self:
             deliveries = self.env['stock.picking'].search([
                 ('project_transfer', '=', project.name)
             ])
             project.delivery_count = len(deliveries)