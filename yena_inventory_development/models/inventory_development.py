from odoo import api, fields, models
import requests
import base64
from io import BytesIO

class Picking(models.Model):
    _inherit = 'stock.picking'

    arrive_date = fields.Date(string="Arrive Date")
    project_transfer = fields.Many2one("project.project", string="Project Number")
    situation = fields.Selection([
        ("to_be_planned", "To be planned"),
        ("on_the_way", "On the way"),
        ("arrived", "Arrived")
    ], string="Situation")
    transportation_code = fields.Char(string="Transportation Code")
    sale_id=fields.Many2one("sale.order",string="Sale Order")
    purchase_id=fields.Many2one("purchase.order",string="Purchase Order")
    sequence_code = fields.Char(string='Sequence Code', related='picking_type_id.sequence_code', store=True)
    logistic_company = fields.Char (string="Logistic Company")
    delivery_performance_supplier = fields.Integer(compute='_compute_despatch_date_difference', string='S-Delivery Performance', store=True, readonly=True)
    delivery_performance_customer = fields.Integer(compute='_compute_arrival_date_difference', string='C-Delivery Performance', store=True, readonly=True)
    
    @api.model
    def compute_days_difference(self, scheduled_date, comparison_date):
        if not scheduled_date or not comparison_date:
            return 0
 
        diff = scheduled_date - comparison_date
        days = diff.days
 
        return days
 
    @api.depends('scheduled_date', 'edespatch_date')
    def _compute_despatch_date_difference(self):
        for record in self:
            despatch_date = fields.Datetime.from_string(record.edespatch_date) if record.edespatch_date else None
            scheduled_date_diff = fields.Datetime.from_string(record.scheduled_date) if record.scheduled_date else None
            record.delivery_performance_supplier = self.compute_days_difference(scheduled_date_diff, despatch_date)
 
    @api.depends('scheduled_date', 'arrival_date')
    def _compute_arrival_date_difference(self):
        for record in self:
            arrival_date = fields.Datetime.from_string(record.arrival_date) if record.arrival_date else None
            scheduled_date_diff = fields.Datetime.from_string(record.scheduled_date) if record.scheduled_date else None
            record.delivery_performance_customer = self.compute_days_difference(scheduled_date_diff, arrival_date)
            
    @api.model
    def create(self, vals):
        self._update_scheduled_date(vals)
        return super(Picking, self).create(vals)

    def write(self, vals):
        self._update_scheduled_date(vals)
        return super(Picking, self).write(vals)

    def _update_scheduled_date(self, vals):
        for record in self:
            picking_type = record.env['stock.picking.type'].browse(vals.get('picking_type_id', record.picking_type_id.id))

            if picking_type.sequence_code == 'IN':  # Receipts
                purchase_order = record.env['purchase.order'].search([('name', '=', record.origin)], limit=1)
                if purchase_order:
                    vals['scheduled_date'] = purchase_order.delivery_date
            elif picking_type.sequence_code == 'OUT':  # Delivery Orders
                sale_order = record.env['sale.order'].search([('name', '=', record.origin)], limit=1)
                if sale_order:
                    vals['scheduled_date'] = sale_order.commitment_date

    def default_get(self, fields_list):
        defaults = super(Picking, self).default_get(fields_list)

        if self.env.user.company_id.id == 1 and self.env.context.get('default_picking_type_id'):
            picking_type = self.env['stock.picking.type'].browse(self.env.context['default_picking_type_id'])
            if picking_type.sequence_code == 'OUT':
                defaults['edespatch_delivery_type'] = 'edespatch'

        return defaults

    
class StockMove(models.Model):
    _inherit = "stock.move"

    arrive_date = fields.Date(related="picking_id.arrive_date", string="Arrive Date")
    project_transfer = fields.Many2one(related="picking_id.project_transfer", string="Project Number")
    situation = fields.Selection(related="picking_id.situation", string="Situation")
    transportation_code = fields.Char(related="picking_id.transportation_code", string="Transportation Code")
    batch_id = fields.Many2one('stock.picking.batch', string='Batch', related='picking_id.batch_id', store=True, readonly=True)
    edespatch_delivery_type = fields.Selection(related="picking_id.edespatch_delivery_type", string="Delivery Type")
    scheduled_date = fields.Datetime(related='picking_id.scheduled_date', store=True, readonly=True)
    arrival_date = fields.Date(related='picking_id.arrival_date', store=True, readonly=True)
    purchase_id=fields.Many2one(related='picking_id.purchase_id',string="Purchase Order")
    edespatch_date=fields.Datetime(related='picking_id.edespatch_date',string="Purchase Order")
    airtag_url = fields.Char(string='Airtag Link', related='picking_id.batch_id.airtag_url', store=True, readonly=True)
    vehicle_type_id = fields.Many2one(string='Vehicle Type', related='picking_id.batch_id.vehicle_type_id', store=True, readonly=True)

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
 
    stackable = fields.Boolean(
        string='Stackable',
        related='product_id.packaging_ids.package_type_id.stackable',
        store=True,
        readonly=True
    )
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    coating = fields.Selection([
        ("hot_dip_galvanized", "Hot Dip Galvanized"),
        ("electrogalvanized", "Electrogalvanized"),
        ("centrifugal_galvanise", "Centrifugal galvanise"),
        ("electrostatic_powder_coating_red", "Electrostatic powder coating Red"),
        ("epoxy_coating", "Epoxy Coating"),
        ("uncoated", "Uncoated"),
        ("electrostatic_powder_coating_black", "Electrostatic powder coating Black"),
        ("shop_primer", "Shop Primer")
    ], string="Coating")
    material = fields.Many2many('product.yena_material', string="Material")
    min_order_qty = fields.Char(string="Min. Order Quantity")
    customer = fields.Many2one('res.partner', domain=[('is_company', '=', True)], string="Customer")
    technical_drawing = fields.Binary(string='Technical Drawing')
    technical_drawing_filename = fields.Char()
    technical_drawing_url = fields.Char(string='Technical Drawing URL', readonly=True)
    technical_drawing_revision = fields.Char(string='Technical Drawing Revision')
    technical_drawing_link = fields.Html(string='Technical Drawing Link', compute="_compute_technical_drawing_link")
    manufacturing_instructions = fields.Many2many('ir.attachment', 'manufacturing_instruction_rel', 'product_id', 'attachment_id', string='Standart Operation Procedure')
    packaging_instructions = fields.Many2many('ir.attachment', 'packaging_instruction_rel', 'product_id', 'attachment_id', string='Packaging Instructions')
    packaging_images = fields.Many2many('ir.attachment', 'packaging_image_rel', 'product_id', 'attachment_id', string='Packaging Photos')
    origin_country_id = fields.Many2one("res.country", string="Origin")
    hs_code_description = fields.Char(string="HS Code Description", store=True)
    description_sale_en = fields.Char(string="Sale Description English", store=True)

    @api.onchange('categ_id', 'customer')
    def _onchange_hs_code(self):
        hs_code_record = self.env['yena.hscode'].search([
            ('category', '=', self.categ_id.id),
            ('industry', '=', self.customer.industry_id.id),
        ], limit=1)
        self.hs_code = hs_code_record.name if hs_code_record else False

    @api.onchange('hs_code')
    def _onchange_hs_code_details(self):
        if self.hs_code:
            hs_code_record = self.env['yena.hscode'].search([('name', '=', self.hs_code)], limit=1)
            if hs_code_record:
                self.description = hs_code_record.product_description
                self.description_sale = hs_code_record.customs_description_tr
                self.description_sale_en = hs_code_record.customs_description_en
                self.hs_code_description = hs_code_record.example_description
            else:
                # Eğer eşleşen bir hs_code kaydı yoksa, açıklamaları boşalt
                self.description = ''
                self.description_sale = ''
                self.description_sale_en = ''
                self.hs_code_description = ''
        else:
            # Eğer hs_code boşsa, açıklamaları boşalt
            self.description = ''
            self.description_sale = ''
            self.description_sale_en = ''
            self.hs_code_description = ''

    @api.model
    def default_get(self, fields_list):
        res = super(ProductTemplate, self).default_get(fields_list)

        # standard_price default değeri ayarlama
        if 'standard_price' not in res:
            res['standard_price'] = 1.0

        # MTO rota ayarlama
        mto_route_id = 1  # "MTO" rotasının ID'si linkteki web#id'den bulunacak
        if 'route_ids' not in res:
            res['route_ids'] = [(4, mto_route_id)]
        else:
            res['route_ids'].append((4, mto_route_id))

        # Varsayılan satıcı ayarlama
        if 'default_seller' in self._context:
            seller_id = self.env['res.partner'].browse(self._context['default_seller'])
            if 'seller_ids' in res:
                res['seller_ids'].append((0, 0, {'name': seller_id.id}))
            else:
                res['seller_ids'] = [(0, 0, {'name': seller_id.id})]
        if 'default_seller' in self._context:
            seller_id = self.env['res.partner'].browse(self._context['default_seller'])
            # İlk satır için veriler
            first_line = {
                'name': 219,
                'currency_id': 1,
                'company_id': 2,
            }
            # İkinci satır için veriler
            second_line = {
                'name': 94654,
                'currency_id': 1,
                'company_id': 1,
            }
            # Eğer seller_ids anahtarı zaten varsa bu satırları ekle, yoksa yeni bir liste oluştur
            if 'seller_ids' in res:
                res['seller_ids'].extend([(0, 0, first_line), (0, 0, second_line)])
            else:
                res['seller_ids'] = [(0, 0, first_line), (0, 0, second_line)]

        return res

    def _post_technical_drawing(self, drawing, filename, product_id, product_name):
        try:
            url = 'https://portal-test.yenaengineering.nl/api/technicaldrawings'
            file_data = BytesIO(base64.b64decode(drawing))
            files = {'technical_drawing': (filename, file_data)}
            data = {
                'odooid': product_id,
                'product_name': product_name,
                'original_filename': filename  # Orijinal dosya adını burada gönderin
            }
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()  # Check for errors
            return response.json()['data']['technical_drawing_url']
        except Exception as e:
            raise

    @api.depends('technical_drawing_url')
    def _compute_technical_drawing_link(self):
        for record in self:
            if record.technical_drawing_url:
                file_name = record.technical_drawing_url.split('/')[-1]
                link = '<a href="{}">{}</a>'.format(record.technical_drawing_url, file_name)
                record.technical_drawing_link = link
            else:
                record.technical_drawing_link = False

    def _check_technical_drawing(self, old_revision=None, old_drawing_url=None):
        if self.technical_drawing:
            drawing_url = self._post_technical_drawing(
                self.technical_drawing,
                self.technical_drawing_filename,
                self.id,
                self.name
            )

            # Teknik çizimin URL'sini güncelle ve technical_drawing alanını boşalt
            self.write({
                'technical_drawing_url': drawing_url,
                'technical_drawing': False
            })

            # old_revision = old_revision or "yok"
            # old_drawing_url = old_drawing_url or "yok"
            #
            # # Chatter'a mesaj ekliyoruz
            # body = ("""
            #         <p>Teknik Çizim {} revizyonu ile güncellenmiştir.</p>
            #         <p>Dosya: <a href="{}">{}</a></p>
            #         <p>Eski Revizyon: {}</p>
            #         <p>Eski Teknik Çizim: <a href="{}">{}</a></p>
            #         """).format(self.technical_drawing_revision, drawing_url, drawing_url, old_revision,
            #                     old_drawing_url, old_drawing_url)
            #
            # self.message_post(body=body)

    class PackageTypes(models.Model):
        _inherit = "stock.package.type"

        gross_weight = fields.Float(string="Gross Weight")
        net_weight = fields.Float(string="Net Weight")
        stackable = fields.Boolean(string="Stackable")

    class PurchaseOrderLine(models.Model):
        _inherit = 'purchase.order.line'

        coating = fields.Selection(related="product_id.coating", string="Coating", readonly=True)
        unit_weight = fields.Float(related="product_id.weight", string="Unit Weight", readonly=True)
        product_category = fields.Many2one('product.category', related="product_id.categ_id", string="Product Category")
        product_type = fields.Selection(related='product_id.detailed_type', string='Product Type', store=True)
        totalweight = fields.Float(string="Total Weight", readonly=True, compute="_compute_total_weight")
        pricekg = fields.Float(string="KG Price", readonly=True, compute="_compute_pricekg")

        @api.depends('unit_weight', 'product_qty')
        def _compute_total_weight(self):
            for record in self:
                record.totalweight = record.unit_weight * record.product_qty

        @api.depends('price_subtotal', 'totalweight')
        def _compute_pricekg(self):
            for record in self:
                if record.totalweight != 0:
                    record.pricekg = record.price_subtotal / record.totalweight
                else:
                    record.pricekg = 0

    class SaleOrderLine(models.Model):
        _inherit = 'sale.order.line'

        product_type = fields.Selection(related='product_id.detailed_type', string='Product Type', store=True)
        product_category = fields.Many2one('product.category', related="product_id.categ_id", string="Product Category")
        totalweight = fields.Float(string='Total Weight', compute='_compute_total_weight', store=True, readonly=True)
        coating = fields.Selection(related="product_id.coating", string="Coating", readonly=True)
        pricekg = fields.Float(compute='_compute_pricekg', string='KG Price', readonly=True, store=True)
        unit_weight = fields.Float(related="product_id.weight", string="Unit Weight", readonly=True)

        @api.depends('unit_weight', 'product_uom_qty')
        def _compute_total_weight(self):
            for record in self:
                record.totalweight = record.unit_weight * record.product_uom_qty

        @api.depends('price_subtotal', 'totalweight')
        def _compute_pricekg(self):
            for record in self:
                if record.totalweight != 0:
                    record.pricekg = record.price_subtotal / record.totalweight
                else:
                    record.pricekg = 0
