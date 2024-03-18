from odoo import models, fields, api

class ProjectCompareLineTrtoBv(models.Model):
    _name = 'project.compare.line.tr.to.bv'
    _description = 'Project Order Comparison Line TR to BV'

    project_id = fields.Many2one('project.project', string='Project')
    product_id = fields.Many2one('product.product', string='Product')
    yena_bv_sale_weight = fields.Float(string='Yena BV Sale Weight (kg)')
    yena_tr_purchase_weight = fields.Float(string='Yena TR Purchase Weight (kg)')
    yena_bv_sale_qty = fields.Float(string='Yena BV Sale Quantity')
    yena_tr_purchase_qty = fields.Float(string='Yena TR Purchase Quantity')
    
class ProjectCompareLineBvtoTr(models.Model):
    _name = 'project.compare.line.bv.to.tr'
    _description = 'Project Order Comparison Line Bv to TR'

    project_id = fields.Many2one('project.project', string='Project')
    product_id = fields.Many2one('product.product', string='Product')
    yena_bv_purchase_qty = fields.Float(string='Yena BV Purchase Quantity')
    yena_tr_sale_qty = fields.Float(string='Yena TR Sale Quantity')
    yena_bv_purchase_weight = fields.Float(string='Yena BV Purchase Weight (kg)')
    yena_tr_sale_weight = fields.Float(string='Yena TR Sale Weight (kg)')

class Project(models.Model):
    _inherit = 'project.project'

    comparison_lines_tr_to_bv = fields.One2many(
        comodel_name='project.compare.line.tr.to.bv', 
        inverse_name='project_id', 
        string='Order Comparison Lines'
    )
    
    comparison_lines_bv_to_tr = fields.One2many(
        comodel_name='project.compare.line.bv.to.tr', 
        inverse_name='project_id', 
        string='Order Comparison Lines'
    )

    def compare_orders_tr_to_bv(self):
        self.ensure_one()
   
        bv_sale_orders = self.env['sale.order'].search([('project_sales', '=', self.id),
                                                    ('state', 'in', ['sale', 'done']),
                                                    ('company_id', '=', 2)])
        tr_purchase_orders = self.env['purchase.order'].search([('project_purchase', '=', self.id),
                                                            ('state', 'in', ['purchase', 'done']),
                                                            ('company_id', '=', 1)])
        existing_lines = {line.product_id.id: line for line in self.comparison_lines_tr_to_bv}

        product_data = {}

        for order in bv_sale_orders:
            for line in order.order_line:
                product = line.product_id
                if product.detailed_type == 'product':
                    key = product.id
                    if key not in product_data:
                        product_data[key] = {
                            'yena_bv_sale_qty': 0,
                            'yena_bv_sale_weight': 0,
                            'yena_tr_purchase_qty': 0,
                            'yena_tr_purchase_weight': 0,
                        }
                    qty = line.product_uom_qty
                    weight = qty * product.weight
                    product_data[key]['yena_bv_sale_qty'] += qty
                    product_data[key]['yena_bv_sale_weight'] += weight

        for order in tr_purchase_orders:
            for line in order.order_line:
                product = line.product_id
                if product.detailed_type == 'product':
                    key = product.id
                    if key not in product_data:
                        product_data[key] = {
                            'yena_bv_sale_qty': 0,
                            'yena_bv_sale_weight': 0,
                            'yena_tr_purchase_qty': 0,
                            'yena_tr_purchase_weight': 0,
                        }
                    qty = line.product_qty
                    weight = qty * product.weight
                    product_data[key]['yena_tr_purchase_qty'] += qty
                    product_data[key]['yena_tr_purchase_weight'] += weight

        comparison_lines_tr_to_bv = []
        existing_line_ids = []
        for product_id, data in product_data.items():
            if product_id in existing_lines:
                comparison_lines_tr_to_bv.append((3, existing_lines[product_id].id))

            if product_id in existing_lines:
                existing_lines[product_id].write({
                
                'product_id': product_id,
                'yena_bv_sale_qty': data['yena_bv_sale_qty'],
                'yena_tr_purchase_qty': data['yena_tr_purchase_qty'],
                'yena_bv_sale_weight': data['yena_bv_sale_weight'],
                'yena_tr_purchase_weight': data['yena_tr_purchase_weight']})
                existing_line_ids.append(existing_lines[product_id].id)
            else:
                
                line = self.env['project.compare.line.tr.to.bv'].create({
                'project_id': self.id,
                'product_id': product_id,
                'yena_bv_sale_qty': data['yena_bv_sale_qty'],
                'yena_tr_purchase_qty': data['yena_tr_purchase_qty'],
                'yena_bv_sale_weight': data['yena_bv_sale_weight'],
                'yena_tr_purchase_weight': data['yena_tr_purchase_weight']})
                existing_line_ids.append(line.id)

        self.comparison_lines_tr_to_bv = [(6, 0, existing_line_ids)]

    def compare_orders_bv_to_tr(self):
        self.ensure_one()
        # Yena BV için alış siparişleri
        bv_purchase_orders = self.env['purchase.order'].search([('project_purchase', '=', self.id),
                                                                ('state', 'in', ['purchase', 'done']),
                                                                ('company_id', '=', 2)])
        # Yena TR için satış siparişleri
        tr_sale_orders = self.env['sale.order'].search([('project_sales', '=', self.id),
                                                        ('state', 'in', ['sale', 'done']),
                                                        ('company_id', '=', 1)])
        existing_lines = {line.product_id.id: line for line in self.comparison_lines_bv_to_tr}

        product_data = {}

        for order in bv_purchase_orders:
            for line in order.order_line:
                product = line.product_id
                if product.detailed_type == 'product':
                    key = product.id
                    if key not in product_data:
                        product_data[key] = {
                            'yena_bv_purchase_qty': 0,
                            'yena_bv_purchase_weight': 0,
                            'yena_tr_sale_qty': 0,  
                            'yena_tr_sale_weight': 0
                        }
                    qty = line.product_qty
                    weight = qty * product.weight
                    product_data[key]['yena_bv_purchase_qty'] += qty
                    product_data[key]['yena_bv_purchase_weight'] += weight

        for order in tr_sale_orders:
            for line in order.order_line:
                product = line.product_id
                if product.detailed_type == 'product':
                    key = product.id
                    if key not in product_data:
                        product_data[key] = {
                            'yena_bv_purchase_qty': 0,
                            'yena_bv_purchase_weight': 0,
                            'yena_tr_sale_qty': 0,
                            'yena_tr_sale_weight': 0,
                        }
                    qty = line.product_uom_qty
                    weight = qty * product.weight
                    product_data[key]['yena_tr_sale_qty'] += qty
                    product_data[key]['yena_tr_sale_weight'] += weight

        comparison_lines_bv_to_tr = []
        existing_line_ids = []
        for product_id, data in product_data.items():

            if product_id in existing_lines:
                comparison_lines_bv_to_tr.append((3, existing_lines[product_id].id))

            if product_id in existing_lines:
                existing_lines[product_id].write({
                
                'product_id': product_id,
                'yena_bv_purchase_qty': data['yena_bv_purchase_qty'],
                'yena_tr_sale_qty': data['yena_tr_sale_qty'],
                'yena_tr_sale_weight': data['yena_tr_sale_weight'],
                'yena_bv_purchase_weight': data['yena_bv_purchase_weight']})
                existing_line_ids.append(existing_lines[product_id].id)
            else:
                line = self.env['project.compare.line.bv.to.tr'].create({
                'project_id': self.id,
                'product_id': product_id,
                'yena_bv_purchase_qty': data['yena_bv_purchase_qty'],
                'yena_tr_sale_qty': data['yena_tr_sale_qty'],
                'yena_tr_sale_weight': data['yena_tr_sale_weight'],
                'yena_bv_purchase_weight': data['yena_bv_purchase_weight']})
                existing_line_ids.append(line.id)

        self.comparison_lines_bv_to_tr = [(6, 0, existing_line_ids)]
        
    def hide_equal_qty_products(self):
        for record in self:
            comparison_lines_tr_to_bv = record.comparison_lines_tr_to_bv.filtered(lambda l: l.yena_bv_sale_qty == l.yena_tr_purchase_qty)
            comparison_lines_bv_to_tr = record.comparison_lines_bv_to_tr.filtered(lambda l: l.yena_bv_purchase_qty == l.yena_tr_sale_qty)
            
            for line in comparison_lines_tr_to_bv:
                line.unlink()
            
            for line in comparison_lines_bv_to_tr:
                line.unlink()
        
    def show_equal_qty_products(self):
        for record in self:
            record.compare_orders_bv_to_tr()
            record.compare_orders_tr_to_bv()
        
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_id = fields.Many2one(
        'project.project', 
        string='Project',
        help='Select a project for this purchase order.'
    )

    @api.model
    def create(self, vals):
        record = super(PurchaseOrder, self).create(vals)
        project = record.project_purchase
        if project:
            project.compare_orders_bv_to_tr()
            project.compare_orders_tr_to_bv()
        return record

    def write(self, vals):
        result = super(PurchaseOrder, self).write(vals)
        
        for record in self:
            project = record.project_purchase
            if project:
                project.compare_orders_bv_to_tr()
                project.compare_orders_tr_to_bv()
        return result

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        record = super(SaleOrder, self).create(vals)
        project = record.project_sales
        if project:
            project.compare_orders_bv_to_tr()
            project.compare_orders_tr_to_bv()
        return record

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        
        for record in self:
            project = record.project_sales
            if project:
                project.compare_orders_bv_to_tr()
                project.compare_orders_tr_to_bv()
        return result