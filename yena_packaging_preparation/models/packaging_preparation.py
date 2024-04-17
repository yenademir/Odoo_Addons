from odoo import models, fields, api
import requests
from io import BytesIO
from datetime import datetime
from collections import defaultdict
import re
import math

class PackagingPreparation(models.Model):
    _name = 'packaging.preparation'
    _description = 'Packaging Preparation'
    _order = 'pallet_no'

    name = fields.Char('Name')
    batch_id = fields.Many2one('stock.picking.batch', string='Batch Reference')
    customer_reference = fields.Char('Customer Reference')
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Text('Description')
    origin = fields.Char('Origin')
    package_quantity = fields.Float('Quantity', compute='_compute_total_net_weight', store=True)
    unit_of_measure = fields.Many2one('uom.uom', string='Unit of Measure')
    unit_net_weight = fields.Float('Unit Net Weight')
    total_net_weight = fields.Float('Total Net Weight')
    gross_weight = fields.Float('Tare Weight')
    total_gross_weight = fields.Float('Total Gross Weight', compute='_compute_total_gross_weight', store=True)
    package_no = fields.Char('Package Number')
    width = fields.Float('Width')
    length = fields.Float('Length')
    height = fields.Float('Height')
    stackable = fields.Boolean('Stackable')
    pallet_no = fields.Integer('Pallet Number')
    purchase_order_line_id = fields.Many2one('purchase.order.line', string="Purchase Order Line")

    @api.depends('gross_weight', 'total_net_weight')
    def _compute_total_gross_weight(self):
        for record in self:
            record.total_gross_weight = record.gross_weight + record.total_net_weight
    
    @api.depends('package_quantity', 'unit_net_weight')
    def _compute_total_net_weight(self):
        for record in self:
            record.total_net_weight = record.package_quantity * record.unit_net_weight

class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    packaging_preparation_ids = fields.One2many(
        comodel_name='packaging.preparation',
        inverse_name='batch_id',
        string='Packaging Preparations'
    )

    def delete_packaging_preparations(self):
        for batch in self:
            preparations_to_delete = batch.packaging_preparation_ids
            preparations_to_delete.unlink()

    def create_packaging_preparations(self):
        PackagingPreparation = self.env['packaging.preparation']
        for batch in self:
            pallet_no = 1
            no_package_data = []  # Paket bilgisi olmayan kayıtlar için geçici liste

            for line in batch.move_line_ids:
                purchase_order_line = line.move_id.purchase_line_id
                if line.package_quantity <= 0 or line.package_quantity is False:
                    # Transfer edilen toplam adeti kullanarak tek bir kayıt oluştur
                    vals = {
                            'name': line.product_id.name,
                            'batch_id': batch.id,
                            'customer_reference': purchase_order_line.order_id.customer_reference,
                            'product_id': line.product_id.id,
                            'package_quantity': line.qty_done,
                            'description': line.product_id.description_sale,
                            'origin' : line.product_id.origin_country_id.name,
                            'unit_of_measure': line.product_uom_id.id,
                            'unit_net_weight': line.product_id.weight, 
                            'total_net_weight': line.product_id.weight * line.qty_done,
                            'package_no': 1,
                            'gross_weight': line.gross_weight,
                            'width': line.width,
                            'length': line.length,
                            'height': line.height,
                            'stackable': line.stackable,
                            'pallet_no': pallet_no,
                            'purchase_order_line_id': purchase_order_line.id if purchase_order_line else False,
                        }
                    no_package_data.append(vals)

                else:
                    # Tam paketler ve kalan miktar için kayıtlar oluştur
                    full_packages = int(line.qty_done / line.package_quantity)
                    for _ in range(full_packages):
                        vals = {
                            'name': line.product_id.name,
                            'batch_id': batch.id,
                            'customer_reference': purchase_order_line.order_id.customer_reference,
                            'product_id': line.product_id.id,
                            'package_quantity': line.package_quantity,
                            'description': line.product_id.description_sale,
                            'origin' : line.product_id.origin_country_id.name,
                            'unit_of_measure': line.product_uom_id.id,
                            'unit_net_weight': line.product_id.weight, 
                            'total_net_weight': line.product_id.weight * line.package_quantity,
                            'package_no': 1,
                            'gross_weight': line.gross_weight,
                            'width': line.width,
                            'length': line.length,
                            'height': line.height,
                            'stackable': line.stackable,
                            'pallet_no': pallet_no,
                            'purchase_order_line_id': purchase_order_line.id if purchase_order_line else False,
                        }
                        PackagingPreparation.create(vals)
                        pallet_no += 1

                    remaining_qty = line.qty_done % line.package_quantity
                    if remaining_qty > 0:
                        vals = {
                            'name': line.product_id.name,
                            'batch_id': batch.id,
                            'customer_reference': purchase_order_line.order_id.customer_reference,
                            'product_id': line.product_id.id,
                            'package_quantity': remaining_qty,
                            'description': line.product_id.description_sale,
                            'origin' : line.product_id.origin_country_id.name,
                            'unit_of_measure': line.product_uom_id.id,
                            'unit_net_weight': line.product_id.weight, 
                            'total_net_weight': line.product_id.weight * line.package_quantity,
                            'package_no': 1,
                            'gross_weight': line.gross_weight,
                            'width': line.width,
                            'length': line.length,
                            'height': line.height,
                            'stackable': line.stackable,
                            'pallet_no': pallet_no,
                            'purchase_order_line_id': purchase_order_line.id if purchase_order_line else False,
                        }
                        PackagingPreparation.create(vals)
                        pallet_no += 1

            for vals in no_package_data:
                PackagingPreparation.create(vals)
                pallet_no += 1

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    package_quantity = fields.Float(
        string='Package Quantity',
        related='product_id.packaging_ids.qty',
        store=True,
        
    )
    length = fields.Integer(
        string='Length',
        related='product_id.packaging_ids.length',
        store=True,
        readonly=True
    )
    width = fields.Integer(
        string='Width',
        related='product_id.packaging_ids.width',
        store=True,
        readonly=True
    )
    height = fields.Integer(
        string='Height',
        related='product_id.packaging_ids.height',
        store=True,
        readonly=True
    )
    stackable = fields.Boolean(
        string='Stackable',
        related='product_id.packaging_ids.stackable',
        store=True,
        readonly=True
    )
    customer_reference = fields.Char(
        string='Customer Reference',
        related='picking_id.purchase_id.customer_reference',
        store=True,
        readonly=True
    )
    gross_weight = fields.Float(
        string='Tare Weight',
        related='product_id.packaging_ids.gross_weight',
        store=True,
    )

class PackagingType(models.Model):
    _name = 'type.packaging'
    _description = 'Type of Packaging'

    name = fields.Char(string='Name')

class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    length = fields.Integer('Length')
    width = fields.Integer('Width')
    height = fields.Integer('Height')
    stackable = fields.Boolean('Stackable')
    gross_weight = fields.Float('Tare Weight')
    type = fields.Many2one('type.packaging', string='Type')

class PackagingPreparationReportXlsx(models.AbstractModel):
    _name = 'report.yena_packaging_preparation.report_xlsx'
    _inherit = 'report.report_xlsx.abstract'


    def add_headers(self,sheet, batches, merge_format14, merge_format14left, merge_format10, merge_format18,row_line,header_format):
        
        for batch in batches:

            customer_references = set(line.customer_reference for line in batch.move_line_ids if line.customer_reference)
            despatch_date = batch.edespatch_date if batch.edespatch_date else ''
            if despatch_date:
                despatch_date = datetime.strftime(despatch_date, '%d-%m-%Y')
            project_nos = set(project.name for project in batch.project_ids)
            project_text = 'Project No(s) # ' + ', '.join(project_nos)       
            transportation_code = batch.transportation_code if batch.transportation_code else ''
            shipment_info_text = f'Shipment Number: {transportation_code} / Shipment Date: {despatch_date}'
            po_text = 'PO(s) # ' + ', '.join(customer_references)

            sheet.merge_range('A1:C9', 'PACKING LIST', merge_format14)
            sheet.merge_range('A10:D10', po_text, merge_format14left)
            sheet.merge_range('A11:D11', project_text, merge_format14left)
            sheet.merge_range('A12:D12', shipment_info_text, merge_format14left)
            sheet.merge_range('F1:I1', 'İRSALİYE NO / WAY BILL NO :', merge_format10)
            sheet.merge_range('F2:I2', 'İHRACATÇI /SHIPPER:', merge_format10)
            sheet.merge_range('F3:I9', 'YENA DEMİR ÇELİK SAN. TİC.LTD.ŞTİ.\nOsmanağa Mah. Rıhtım Caddesi\nNo:8/5 34714 \nKadıköy/İstanbul', merge_format18)
            sheet.merge_range('F10:I11', 'ÜRÜN MENŞEE : TÜRKİYE \nORIGIN OF THE MATERIAL : TÜRKİYE', merge_format10)
            sheet.merge_range('J1:N1', 'FATURA / INVOICE :' , merge_format10)
            sheet.merge_range('J2:N2', 'ALICI / RECEIVER:' , merge_format10)
            sheet.merge_range('J3:N9', 'YENA ENGINEERING B.V. \nWTC ROTTERDAM BEURSPLEIN 37\n3011 AA\nROTERDAM/ NETHERLANDS' , merge_format18)
            
            url = 'https://yenastorage.blob.core.windows.net/odoo-container/YENA_logo.png'
            response = requests.get(url)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                sheet.insert_image('A1:D8', 'YENA_logo.png', {'image_data': image_data, 'x_scale': 0.3, 'y_scale': 0.3})
                
            headers = [
                'PALLET NO', 'ORDER NO', 'POSE', 'Antlaşma No:\nO.A NO:',
                'MIKTARI\nQUANTITY', 'BİRİM\nUNIT', 'NET AĞIRLIK (KG)\nNET WEIGHT (KG)',
                'TOPLAM NET AĞIRLIK (KG)\nTOTAL NET WEIGHT (KG)',
                'DARA AĞIRLIK (KG)\nTARE WEİGHT (KG)', 'BRÜT AĞIRLIK (KG)\nGROSS WEİGHT (KG)',
                'EN (MM)\nWIDTH (MM)', 'BOY (MM)\nLENGTH (MM)', 'YÜKSEKLİK (MM)\nHEIGHT (MM)', 'STACKABLE',
            ]
            
            for col, header in enumerate(headers):
                sheet.write(row_line, col, header, header_format)
                
            column_widths = [6, 9, 25, 25, 15.5, 10, 6.50, 16, 23, 16.5, 17.5, 24, 12.5, 12.5, 12.5, 13.5, 12]
            for i, width in enumerate(column_widths):
                sheet.set_column(i, i, width)

    def generate_xlsx_report(self, workbook, data, batches):
        centered_format = workbook.add_format({
            'align': 'center', 
            'valign': 'vcenter', 
            'size': 13,
            'border': 1,
            })
        centered_format_bg = workbook.add_format({
            'align': 'center', 
            'valign': 'vcenter', 
            'size': 13,
            'bg_color': '#ededed',
            'border': 1,
            })
        merge_format18 = workbook.add_format({
            'text_wrap': True,
            'align': 'left',
            'valign': 'vcenter',
            'bold': True,
            'size': 18
        })
        merge_format14left = workbook.add_format({
            'text_wrap': True,
            'align': 'left',
            'valign': 'vcenter',
            'bold': True,
            'size': 14,
            'bg_color': '#ededed',
            'border': 1,
        })
        merge_format14 = workbook.add_format({
            'align': 'center',
            'valign': 'vbottom',
            'bold': True,
            'size': 14
        })
        merge_format10 = workbook.add_format({
            'size': 10
        })
        header_format = workbook.add_format({
            'bg_color': '#d9d9d9',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'bold': True, 
        })

        for batch in batches:
            sheet = workbook.add_worksheet('ALL')
            sheet.fit_to_pages(1, 1)
            sheet.set_landscape()
            row = 12 
            row_line=row 
            self.add_headers(sheet, batches, merge_format14, merge_format14left, merge_format10, merge_format18,row_line,header_format)

            pallet_data = {}
            
            for line in batch.packaging_preparation_ids:
                pallet_no = line.pallet_no
                if pallet_no not in pallet_data:
                    pallet_data[pallet_no] = {
                        'lines': [],
                        'unit_net_weight': 0,
                        'total_net_weight': 0,
                        'gross_weight': 0,
                        'total_gross_weight': 0,
                    }
                pallet_data[pallet_no]['lines'].append(line)
                pallet_data[pallet_no]['unit_net_weight'] += line.unit_net_weight
                pallet_data[pallet_no]['total_net_weight'] += line.total_net_weight
                pallet_data[pallet_no]['gross_weight'] += line.gross_weight
                pallet_data[pallet_no]['total_gross_weight'] += line.total_gross_weight

            

            for pallet_no, data in pallet_data.items():
                start_row = row + 1  
                all_stackable = True 
                max_volume = 0  
                max_dimensions = {} 
                for line in data['lines']:
                    row += 1
                    if not line.stackable:
                        all_stackable = False
                    volume = line.width * line.length * line.height
                    if volume > max_volume:
                        max_volume = volume
                        max_dimensions = {
                            'width': line.width,
                            'length': line.length,
                            'height': line.height,}
                    sheet.write(row, 0, line.pallet_no, centered_format)
                    sheet.write(row, 1, line.customer_reference or '', centered_format)
                    sheet.write(row, 2, line.product_id.display_name, centered_format)
                    partner_ref = line.purchase_order_line_id.blanket_order_line.order_id.partner_ref if line.purchase_order_line_id.blanket_order_line.order_id.partner_ref else '-'
                    sheet.write(row, 3, partner_ref, centered_format)
                    sheet.write(row, 4, line.package_quantity, centered_format)
                    sheet.write(row, 5, line.unit_of_measure.name, centered_format)
                    sheet.write(row, 6, line.unit_net_weight, centered_format)
                    sheet.write(row, 7, line.total_net_weight, centered_format)
                    sheet.write(row, 8, line.gross_weight, centered_format)
                    sheet.write(row, 9, line.total_gross_weight, centered_format)
                    sheet.write(row, 10, line.width, centered_format)
                    sheet.write(row, 11, line.length, centered_format)
                    sheet.write(row, 12, line.height, centered_format)
                    sheet.write(row, 13, '✓' if line.stackable else '×', centered_format)

                total_row = row + 1 
                sheet.write(total_row, 7, sum(data['total_net_weight'] for data in pallet_data.values()), centered_format_bg)
                sheet.write(total_row, 8, sum(data['gross_weight'] for data in pallet_data.values()), centered_format_bg)
                sheet.write(total_row, 9, sum(data['total_gross_weight'] for data in pallet_data.values()), centered_format_bg)

                end_row = row  
                stackable_value = '✓' if all_stackable else '×'
                if len(data['lines']) > 1:
                    first_line = data['lines'][0]
                    sheet.merge_range(start_row, 0, end_row, 0, first_line.pallet_no, centered_format)
                    sheet.merge_range(start_row, 7, end_row, 7, data['total_net_weight'], centered_format)
                    sheet.merge_range(start_row, 8, end_row, 8, data['gross_weight'], centered_format)
                    sheet.merge_range(start_row, 9, end_row, 9, data['total_gross_weight'], centered_format)
                    sheet.merge_range(start_row, 10, row, 10, max_dimensions.get('width', ''), centered_format)
                    sheet.merge_range(start_row, 11, row, 11, max_dimensions.get('length', ''), centered_format)
                    sheet.merge_range(start_row, 12, row, 12, max_dimensions.get('height', ''), centered_format)
                    sheet.merge_range(start_row, 13, row, 13, stackable_value, centered_format)

        pallet_data = {}
        for line in batch.packaging_preparation_ids:
            pallet_no = line.pallet_no
            if pallet_no not in pallet_data:
                pallet_data[pallet_no] = {'lines': [], 'unit_net_weight': 0, 'total_net_weight': 0,
                                        'gross_weight': 0, 'total_gross_weight': 0, 'max_volume': 0,
                                        'max_dimensions': {'width': 0, 'length': 0, 'height': 0}}
            pallet_data[pallet_no]['lines'].append(line)
            volume = line.width * line.length * line.height
            if volume > pallet_data[pallet_no]['max_volume']:
                pallet_data[pallet_no]['max_volume'] = volume
                pallet_data[pallet_no]['max_dimensions'] = {'width': line.width, 'length': line.length, 'height': line.height}
            pallet_data[pallet_no]['unit_net_weight'] += line.unit_net_weight
            pallet_data[pallet_no]['total_net_weight'] += line.total_net_weight
            pallet_data[pallet_no]['gross_weight'] += line.gross_weight
            pallet_data[pallet_no]['total_gross_weight'] += line.total_gross_weight

        for pallet_no, pallet_info in pallet_data.items():
            sheet_name = '{}'.format(pallet_no)
            sheet = workbook.add_worksheet(sheet_name[:31])
            sheet.fit_to_pages(1, 1)
            sheet.set_landscape()
            row_line = 12
            self.add_headers(sheet, batches, merge_format14, merge_format14left, merge_format10, merge_format18,row_line,header_format)
           
           
            
            maxdms = {'width': 0, 'length': 0, 'height': 0}
            for data_line in pallet_info['lines']:
                volume = data_line.width * data_line.length * data_line.height
                if volume > (maxdms['width'] * maxdms['length'] * maxdms['height']):
                    maxdms = {'width': data_line.width, 'length': data_line.length, 'height': data_line.height}
                    
            if pallet_info['lines']:
                first_line = pallet_info['lines'][0]
            row_line += 1  
            total_net_weight_sum_line = 0
            gross_weight_sum_line = 0
            total_gross_weight_sum_line = 0
            
            for data_line in pallet_info['lines']:
                total_net_weight_sum_line += data_line.total_net_weight
                gross_weight_sum_line += data_line.gross_weight
                total_gross_weight_sum_line += data_line.total_gross_weight
                sheet.write(row_line, 0, data_line.pallet_no, centered_format)
                sheet.write(row_line, 1, data_line.customer_reference or '', centered_format)
                sheet.write(row_line, 2, data_line.product_id.display_name, centered_format)
                partner_ref = data_line.purchase_order_line_id.blanket_order_line.order_id.partner_ref if data_line.purchase_order_line_id.blanket_order_line.order_id.partner_ref else '-'
                sheet.write(row_line, 3, partner_ref, centered_format)
                sheet.write(row_line, 4, data_line.package_quantity, centered_format)
                sheet.write(row_line, 5, data_line.unit_of_measure.name, centered_format)
                sheet.write(row_line, 6, data_line.unit_net_weight, centered_format)
                sheet.write(row_line, 7, data_line.total_net_weight, centered_format)
                sheet.write(row_line, 8, data_line.gross_weight, centered_format)
                sheet.write(row_line, 9, data_line.total_gross_weight, centered_format)
                sheet.write(row_line, 10, data_line.width, centered_format)
                sheet.write(row_line, 11, data_line.length, centered_format)
                sheet.write(row_line, 12, data_line.height, centered_format)
                sheet.write(row_line, 13, '✓' if data_line.stackable else '×', centered_format)
                row_line += 1

            total_row = row_line
            sheet.write(total_row, 7, total_net_weight_sum_line, centered_format_bg)
            sheet.write(total_row, 8, gross_weight_sum_line, centered_format_bg)
            sheet.write(total_row, 9, total_gross_weight_sum_line, centered_format_bg) 

            if len(pallet_info['lines']) > 1:
                start_row = 13  # İlk satır numarası
                end_row = row_line - 1  # Son satır numarası

                sheet.merge_range(start_row, 0, end_row, 0, first_line.pallet_no, centered_format)
                sheet.merge_range(start_row, 7, end_row, 7, total_net_weight_sum_line, centered_format)
                sheet.merge_range(start_row, 8, end_row, 8, gross_weight_sum_line, centered_format)
                sheet.merge_range(start_row, 9, end_row, 9, total_gross_weight_sum_line, centered_format)
                sheet.merge_range(start_row, 10, end_row, 10, maxdms['width'], centered_format)
                sheet.merge_range(start_row, 11, end_row, 11, maxdms['length'], centered_format)
                sheet.merge_range(start_row, 12, end_row, 12, maxdms['height'], centered_format)
                sheet.merge_range(start_row, 13, end_row, 13, stackable_value, centered_format)


class PackagingDeliveryReportXlsx(models.AbstractModel):
    _name = 'report.yena_packaging_delivery_note.report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
 
    def generate_xlsx_report(self, workbook, data, batches):
        centered_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'size': 14,
            'border': 1,
        })
        header_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'size': 140,
            'valign': 'vcenter',
            'text_wrap': True,
            'bold': True, 
            'color':'red',
        })
        merge_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'size': 14,
            'border': 1,
            'bold': True,
        })
        warning_format = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'size': 30,
            'border': 1,
            'bold': True,
            'font_color': 'red',
        })
        sheet = workbook.add_worksheet('Delivery Note')
        sheet.merge_range('A1:K20', 'DELIVERY\nNOTE', header_format)
        url = 'https://yenastorage.blob.core.windows.net/odoo-container/YENA_logo.png'
        response = requests.get(url)
        
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            sheet.insert_image('C21', 'YENA_logo.png', {'image_data': image_data, 'x_scale': 0.3, 'y_scale': 0.3})
 
        blanket_order_line_exists = any(
            line.purchase_order_line_id.blanket_order_line for batch in batches for line in batch.packaging_preparation_ids
        )
 
        headers = ['Purchase Order No', 'Drawing Number', 'Quantity','Number of Euro-Pallets','Ayrı(1) Birleşik(0)','Total Quantity']
        column_widths = [20, 30, 15, 20,15,15]
 
        if blanket_order_line_exists:
            headers.insert(1, 'Outline Agreement No')
            column_widths.insert(1, 25)
 
        start_col = 2
 
        for i, width in enumerate(column_widths):
            sheet.set_column(start_col + i, start_col + i, width)
 
        row = 30
        for col, header in enumerate(headers):
            sheet.write(row, start_col + col, header, centered_format)
        row += 1
        grouped_data = defaultdict(list)
        hs_codes = set()
        pallet_prep_ids = {} 
        pallet_unique_no_dict = {}
        for batch in batches:
            total_quantity=0
            for prep in batch.packaging_preparation_ids:
                blanket_order_line = str(prep.purchase_order_line_id.blanket_order_line) if prep.purchase_order_line_id.blanket_order_line else ""
                customer_reference = str(prep.customer_reference) if prep.customer_reference else ""
                pallet_no = prep.pallet_no if isinstance(prep.pallet_no, int) else 0
                if pallet_no not in pallet_prep_ids:
                    pallet_prep_ids[pallet_no] = []
                pallet_prep_ids[pallet_no].append(prep.id)
                key = (blanket_order_line,customer_reference, str(pallet_no))  
                grouped_data[key].append(prep)
 
        sorted_keys = sorted(grouped_data.keys(), key=lambda x: x[1])
        unique_pallet_nos=set()
        for pallet_no, prep_ids in pallet_prep_ids.items():
            if len(prep_ids) > 1:
                for prep_id in prep_ids:
                    pallet_unique_no_dict[prep_id] = 0
            else:
                pallet_unique_no_dict[prep_ids[0]] = 1
                
            unique_pallet_nos.add(pallet_no)

        for key in sorted_keys:
            preparations = grouped_data[key]
            start_row = row
            for prep in preparations:
                total_quantity+=prep.package_quantity

                pallet_unique_no = pallet_unique_no_dict.get(prep.id, 1)

                if blanket_order_line_exists:
                    blanket_order_line = prep.purchase_order_line_id.blanket_order_line.partnet_ref if prep.purchase_order_line_id.blanket_order_line else ""
                    sheet.write(row, 2, prep.customer_reference or '', centered_format)
                    sheet.write(row, 3, blanket_order_line or '', centered_format)
                    sheet.write(row, 4, prep.product_id.display_name or '', centered_format)
                    sheet.write(row, 5, prep.package_quantity or 0, centered_format)
                    sheet.write(row, 6, prep.pallet_no, centered_format)
                    sheet.write(row, 7,  pallet_unique_no,centered_format)
                    row += 1
                else:
                    sheet.write(row, 2, prep.customer_reference or '', centered_format)
                    sheet.write(row, 3, prep.product_id.display_name or '', centered_format)
                    sheet.write(row, 4, prep.package_quantity or 0, centered_format)

                    sheet.write(row, 5, prep.pallet_no, centered_format)
                    sheet.write(row,6 ,  pallet_unique_no,centered_format)
                    row += 1
            
            #end_row = row - 1
            # if start_row != end_row:
            #     sheet.merge_range(start_row, 5, end_row, 5, 1, merge_format)
        
        if blanket_order_line_exists:
            sheet.write(row, 5, 'Total Pallets:', merge_format)
            sheet.write(row, 6, len(unique_pallet_nos), merge_format)
            sheet.write('I32',total_quantity,merge_format)
            sheet.write('C30', 'Number Of Pallets aynı ürün ve customer reference için birleştirilip adedi güncellenmeli', warning_format)
        else:
            sheet.write(row, 4, 'Total Pallets:', merge_format)
            sheet.write(row, 5, len(unique_pallet_nos), merge_format)
            sheet.write('H32',total_quantity,merge_format)
            sheet.write('C30', 'Number Of Pallets aynı ürün ve customer reference için birleştirilip adedi güncellenmeli', warning_format)
        

        
class PackagingCustomsReportXlsx(models.AbstractModel):
    _name = 'report.yena_packaging_customs.report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, batches):
        centered_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'size': 11,
            'border':1,
            'font':'Times New Roman',
            
        })
        merge_format10 = workbook.add_format({
            'size': 11,
            'font':'Times New Roman',
            'text_wrap':True
        })
        merge_format11 = workbook.add_format({
            'size': 11,
            'bold': True,
            'font':'Times New Roman',
            'text_wrap':True,
        })
        merge_format12 = workbook.add_format({
            'size': 12,
            'bold': True,
            'font':'Times New Roman',
            'text_wrap':True,
        })
        header_format = workbook.add_format({
            'size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'bold': True,
            'font':'Times New Roman',
            'text_wrap':True,
        })
        border_format1 = workbook.add_format({
             'top': 2
             })
        border_format2 = workbook.add_format({
             'bottom': 2
             })
        
        def clean_html(raw_html):
            cleanr = re.compile('<.*?>') 
            cleantext = re.sub(cleanr, '', raw_html) 
            return cleantext  
                        
        sheet = workbook.add_worksheet('Packing List')
        headers = ['No','Description', 'Number of Packages', 'Net Weight', 'Gross Weight']
        column_widths = [4,15, 22, 14, 15]
        start_col = 1        

        for i, width in enumerate(column_widths):
            sheet.set_column(start_col -1 + i, start_col -1 + i, width)       
        row = 16
        
        for col, header in enumerate(headers):
            sheet.write(row, start_col -1 + col, header, centered_format)
        url = 'https://yenastorage.blob.core.windows.net/odoo-container/YENA_logo.png'
        response = requests.get(url)

        if response.status_code == 200:
            image_data = BytesIO(response.content)
            sheet.insert_image('A3:K6', 'YENA_logo.png', {'image_data': image_data, 'x_scale': 0.18, 'y_scale': 0.18})
        row += 1
        
        for batch in batches:      
            hs_codes = set()
            product_descriptions = set()
            total_net_weight = 0.0
            total_gross_weight = 0.0
            
            for line in batch.packaging_preparation_ids:
                total_net_weight += line.total_net_weight
                total_gross_weight += line.total_gross_weight
                
                hs_code = line.product_id.hs_code
                if hs_code:
                    hs_codes.add(hs_code)
                product_description = line.product_id.description_sale
                
                if product_description:
                    cleaned_description=clean_html(product_description)
                    product_descriptions.add(cleaned_description)
            
            unique_pallet_nos = {line.pallet_no for line in batch.packaging_preparation_ids}
            unique_pallet_no_count = len(unique_pallet_nos)
            date_now = datetime.today().strftime('%d-%m-%Y')
           
            invoice_no = batch.transportation_code
            sheet.merge_range('C8:D8', "Packing List", header_format)
            sheet.write('E8', date_now, header_format)
            sheet.merge_range('A9:E9', '', border_format1)
            sheet.merge_range('A10:B10', "Customer:", merge_format11)
            sheet.merge_range('C10:D10', "YENA ENGINEERING B.V.", merge_format10)
            sheet.merge_range('A11:E11', "World Trade Center Rotterdam Beursplein 37 3011 AA Rotterdam/Netherlands", merge_format10)
            sheet.merge_range('A12:C12', "Post Address: Postbus 30223 3001 DE Rotterdam", merge_format10)
            sheet.merge_range('A13:C13', "Gebruikersnaam: NL0053992813", merge_format10)
            sheet.merge_range('A14:C14', "EORI NUMBER: NL858751355", merge_format10)
            sheet.merge_range('A16:B16', "Order/Invoice No:", merge_format11)
            sheet.merge_range('C16:D16', invoice_no, merge_format10)

            sheet.write(row, start_col-1, '1', centered_format)
            sheet.write(row, start_col, 'Truck/Road', centered_format)
            sheet.write(row, start_col + 1, unique_pallet_no_count, centered_format)
            sheet.write(row, start_col + 2, total_net_weight, centered_format)
            sheet.write(row, start_col + 3, total_gross_weight, centered_format)
            
            row += 2
            sheet.merge_range(row, start_col-1, row, start_col, "HS Codes: ", merge_format11)
            sheet.merge_range(row, start_col + 1, row, start_col + 2, ', '.join(hs_codes), merge_format10)
            
            row += 1
            sheet.merge_range(row, start_col-1, row+1, start_col , 'Description of Products', merge_format11)
            sheet.merge_range(row, start_col + 1, row+1, start_col + 3, ', '.join(product_descriptions), merge_format10)
            
            row += 2
            sheet.merge_range(row, start_col-1, row, start_col, "Country of Origin", merge_format11)
            sheet.merge_range(row, start_col + 1, row, start_col + 2, "Turkey", merge_format10)
            row+=2
            
            pallet_count_by_customer = {}

        for customer in batch.customer_ids:
            customer_name = customer.name
            address = f"{customer.street}, {customer.city}, {customer.state_id.name if customer.state_id else ''}, {customer.zip}, {customer.country_id.name if customer.country_id else ''}"
            pallet_count = len({line.pallet_no for line in batch.packaging_preparation_ids if line.product_id.customer.name == customer.name})
            pallet_count_by_customer[customer_name] = pallet_count
            
            row += 1
            sheet.merge_range(row, start_col - 1, row+1, start_col+3, f"Delivery Address: {customer_name}, {address}", merge_format11)
            row += 2          
            sheet.merge_range(row, start_col - 1, row, start_col+3 , f"Number of Packages: {pallet_count}", merge_format11)
            row += 3  
            
        sheet.merge_range(row, 0, row, 4, '', border_format2)
        row+=1
        sheet.merge_range(row, 0, row, 4, "YENA DEMİR ÇELİK SAN. VE TİC. LTD ŞTİ", merge_format12)
        row+=1
        sheet.merge_range(row,0,row, 4, "Osmanağa Mah. Rıhtım Caddesi No:8/5 34714 Kadıköy/İstanbul +90 (216) 999 76 64 ", merge_format10)
                
            
class PackagingBillOfLadingReportXlsx(models.AbstractModel):
    _name = 'report.yena_packaging_bill_of_lading.report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, batches):
      
        merge_format10 = workbook.add_format({
            'size': 11,
            'font':'Times New Roman',
            'text_wrap':True,
            'align': 'left',
            'valign': 'vcenter',
            'border':1,

        })
        merge_format11 = workbook.add_format({
            'size': 11,
            'bold': True,
            'font':'Times New Roman',
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap':True,
        })
        merge_format12 = workbook.add_format({
            'size': 12,
            'bold': True,
            'font':'Times New Roman',
            'text_wrap':True,
            'align': 'left',
            'valign': 'vcenter',
            'border':1,
        })
        bottom_text = workbook.add_format({
            'size': 12,
            'bold': True,
            'font':'Times New Roman',
            'text_wrap':True,
            'align': 'left',
            'valign': 'vcenter',   
        })
        header_format = workbook.add_format({
            'size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'bold': True,
            'font':'Times New Roman',
            'text_wrap':True,
        })
        border_format1 = workbook.add_format({
             'top': 2
             })
        border_format2 = workbook.add_format({
             'bottom': 2
             })
        
        def clean_html(raw_html):
            cleanr = re.compile('<.*?>') 
            cleantext = re.sub(cleanr, '', raw_html)
            return cleantext     
         
        sheet = workbook.add_worksheet('Konşimento Talimatı')
        merge_format10.set_text_wrap()

        column_widths = [5,15, 22, 14, 15]
        start_col = 1        
        for i, width in enumerate(column_widths):
            sheet.set_column(start_col -1 + i, start_col -1 + i, width)       
        row = 16
        
        url = 'https://yenastorage.blob.core.windows.net/odoo-container/YENA_logo.png'
        response = requests.get(url)
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            sheet.insert_image('A3:K5', 'YENA_logo.png', {'image_data': image_data, 'x_scale': 0.18, 'y_scale': 0.18})
        row += 1
        
        for batch in batches:
           
            product_descriptions = set()
            total_net_weight = 0.0
            total_gross_weight = 0.0
            volume_by_pallet = {}
            total_pallet_count = 0
            customer_pallet_counts = []
            final_addresses = {}
            pallet_count_by_customer_and_volume = {}
            unique_pallet_nos=set()
 
            for line in batch.packaging_preparation_ids:
                total_net_weight += line.total_net_weight
                total_gross_weight += line.total_gross_weight
                formatted_total_net_weight=f"{total_net_weight:.2f}"
                formatted_total_gross_weight=f"{total_gross_weight:.2f}"
                volume = line.width * line.length * line.height
                pallet_no = line.pallet_no
               
                if pallet_no in volume_by_pallet:
                    if volume > volume_by_pallet[pallet_no]['volume']:
                        volume_by_pallet[pallet_no] = {'volume': volume, 'width': line.width, 'length': line.length, 'height': line.height}
                else:
                    volume_by_pallet[pallet_no] = {'volume': volume, 'width': line.width, 'length': line.length, 'height': line.height}
                product_stackable = line.stackable
                product_description = line.product_id.description_sale
 
                if product_description:
                    cleaned_description=clean_html(product_description)
                    product_descriptions.add(cleaned_description)
           
            address_lines = []
            address_headers=[]
            for index,receiveFrom in enumerate(batch.vendor_ids,start=1):
                vendor_name=receiveFrom.name
                receive_address = f"{receiveFrom.street}, {receiveFrom.city}, " \
                                f"{receiveFrom.state_id.name if receiveFrom.state_id else ''}, " \
                                f"{receiveFrom.zip}, {receiveFrom.country_id.name if receiveFrom.country_id else ''}"
                address_headers.append(f"Alım Adresi {index}")
                address_lines.append(f"{vendor_name}, {receive_address}")
 
            for index,customer in enumerate(batch.customer_ids,start=1):
                customer_name = customer.name
                delivery_address = f"{customer.street}, {customer.city}, " \
                                f"{customer.state_id.name if customer.state_id else ''}, " \
                                f"{customer.zip}, {customer.country_id.name if customer.country_id else ''}"
                final_address = f"Teslim Adresi {index}"
                final_addresses[customer.name] = final_address
                address_headers.append(final_address)
               
                address_lines.append(f"{customer_name}, {delivery_address}")
 
                volume_by_pallet_customer_specific = {}
                stackable_by_pallet_customer_specific = {}
 
                for line in [l for l in batch.packaging_preparation_ids if l.product_id.customer.name == customer_name]:
                    volume = line.width * line.length * line.height
                    pallet_no = line.pallet_no
                    unique_pallet_nos.add(pallet_no)
 
                    if pallet_no in volume_by_pallet_customer_specific:
                        if volume > volume_by_pallet_customer_specific[pallet_no]['volume']:
                            volume_by_pallet_customer_specific[pallet_no] = {'volume': volume, 'width': line.width, 'length': line.length, 'height': line.height}
                        stackable_by_pallet_customer_specific[pallet_no] = stackable_by_pallet_customer_specific.get(pallet_no, True) and line.stackable
                    else:
                        stackable_by_pallet_customer_specific[pallet_no] = line.stackable
                        volume_by_pallet_customer_specific[pallet_no] = {'volume': volume, 'width': line.width, 'length': line.length, 'height': line.height}
 
                    if customer_name not in pallet_count_by_customer_and_volume:
                        pallet_count_by_customer_and_volume[customer_name] = {}
                       
                    if (pallet_no, volume) not in pallet_count_by_customer_and_volume[customer_name]:
                        pallet_count_by_customer_and_volume[customer_name][(pallet_no, volume)] = 1
                    else:
                        pallet_count_by_customer_and_volume[customer_name][(pallet_no, volume)] += 1
                       
                for customer_name, pallet_infos in pallet_count_by_customer_and_volume.items():
                    for (pallet_no, expected_volume), count in pallet_infos.items():
                        final_address = final_addresses.get(customer_name, '')
                        if not final_address:
                            continue
                        if pallet_no in volume_by_pallet_customer_specific:
                            data = volume_by_pallet_customer_specific[pallet_no]
                            calculated_volume = data['width'] * data['length'] * data['height']
                            if calculated_volume == expected_volume:
                                volume_text = f"{data['width']}x{data['length']}x{data['height']}mm"
                                stackable_text = "İstiflenebilir" if stackable_by_pallet_customer_specific[pallet_no] else "İstiflenemez"
                                customer_pallet_counts.append((final_address, f"{count} Kap, {volume_text}, {stackable_text}"))
                    
            date_now = datetime.today().strftime('%d-%m-%Y')
            vehicle_type = batch.vehicle_type_id.name if batch.vehicle_type_id.name else ".............."
            logistic_company = batch.logistic_company.name if batch.logistic_company.name else ".............."
            if batch.edespatch_date:
                edespatch_date_str = batch.edespatch_date.strftime('%d-%m-%Y')
                
            
            sheet.merge_range('C7:D7', "Konşimento Talimatı", header_format)
            sheet.write('E7', date_now, header_format)
            sheet.merge_range('A8:F8', '', border_format1)
            row=8
            sheet.merge_range(row, 0, row+2, 1, "Alıcı Firma:", merge_format12)
            sheet.merge_range(row, 2, row+2, 5, "YENA ENGINEERING B.V.\nWorld Trade Center Rotterdam Beursplein 37 3011 AA Rotterdam/Netherlands", merge_format10)
            row+=3
            sheet.merge_range(row, 0, row+2, 1, "Gönderen Firma:", merge_format12)
            sheet.merge_range(row, 2, row+2, 5, "YENA DEMİR ÇELİK SAN. VE TİC. LTD ŞTİ\nOsmanağa Mah. Rıhtım Caddesi No:8/5 34714 Kadıköy/İstanbul", merge_format10)
            row+=3
            sheet.merge_range(row, 0, row+2, 1, "Varış Gümrüğü", merge_format12)
            sheet.merge_range(row, 2, row+2, 5, f"{logistic_company} tarafından (Gümrük işlemleri Hollanda'da yapılmalıdır.)", merge_format10)
            row+=3      
            
            
            
            for header, detail in zip(address_headers, address_lines):
                sheet.merge_range(row, 0, row+1, 1, header, merge_format12)
                sheet.merge_range(row, 2, row+1, 5, detail, merge_format10)
                row += 2
            
            sheet.merge_range(row, 0, row+2, 1,'Araç Talebi',merge_format12)
            sheet.merge_range(row, 2, row+2, 5,vehicle_type,merge_format10)
            row+=3     
            
            sheet.merge_range(row, 0, row+2, 1, 'Description of Products', merge_format12)
            sheet.merge_range(row, 2, row+2, 5 ,', '.join(product_descriptions), merge_format10)
            row+=3      
            
            addresses = {}
            for address, info in customer_pallet_counts:
                if address not in addresses:
                    addresses[address] = []
                addresses[address].append(info)

            
            for address, infos in addresses.items():
                start_row = row
                for info in infos:
                    sheet.merge_range(row, 2,row,5, info, merge_format10)  
                    row += 1
                end_row = start_row + len(infos) - 1
                sheet.merge_range(start_row, 0, end_row, 1, f"Kap Adedi ve Ebadı\n{address}", merge_format12)
            
            sheet.merge_range(row, 0, row+2, 1, "AMBALAJLANMA", merge_format12)
            sheet.merge_range(row, 2, row+2, 5, len(unique_pallet_nos), merge_format10)
            row+=3      
            
            sheet.merge_range(row, 0, row+2, 1, "Yükleme Tarihi", merge_format12)
            sheet.merge_range(row, 2, row+2, 5, edespatch_date_str, merge_format10)
            row+=3     
            
            sheet.merge_range(row, 0, row+2, 1, "Net/Brüt Ağırlık", merge_format12)
            sheet.merge_range(row, 2, row+2, 5, f"Net Ağırlık: {formatted_total_net_weight}KG\nBrüt Ağırlık: {formatted_total_gross_weight}KG", merge_format10)
            row+=3    
           
            sheet.merge_range(row, 0, row+2, 1, "Malzemenin Teslim Şekli", merge_format12)
            sheet.merge_range(row, 2, row+2, 5,"DAP,NETHERLANDS" , merge_format10)
            row+=3      
            
            sheet.merge_range(row, 0, row+2, 1, "Gümrükçü Firma", merge_format12)
            sheet.merge_range(row, 2, row+2, 5,"TÜRKİYE GÜMRÜK: MAVİPORT" , merge_format10)
            row+=5      
            
            sheet.merge_range(row, 0, row, 5, '', border_format2)
            row+=1
            sheet.merge_range(row, 0, row, 5, "YENA DEMİR ÇELİK SAN. VE TİC. LTD ŞTİ", bottom_text)
            row+=1
            sheet.merge_range(row,0,row, 5, "Osmanağa Mah. Rıhtım Caddesi No:8/5 34714 Kadıköy/İstanbul +90 (216) 999 76 64 ", merge_format11)

                        
class PackagingProposalFormReportXlsx(models.AbstractModel):
    _name = 'report.yena_packaging_transportation_request.report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, batches):
        merge_format11 = workbook.add_format({
            'size': 11,
            'bold': True,
            'font':'Times New Roman',
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap':True,
        })
        bottom_text = workbook.add_format({
            'size': 12,
            'bold': True,
            'font':'Times New Roman',
            'text_wrap':True,
            'align': 'left',
            'valign': 'vcenter',
        })
        border_format2 = workbook.add_format({
             'bottom': 2
             })
        merge_format10 = workbook.add_format({
            'size': 11,
            'font':'Times New Roman',
            'text_wrap':True,
            'align': 'left',
            'valign': 'vcenter',
            'border':1,
        })
        merge_format12 = workbook.add_format({
            'size': 12,
            'bold': True,
            'font':'Times New Roman',
            'text_wrap':True,
            'align': 'left',
            'valign': 'vcenter',
            'border':1,
        })
        header_format = workbook.add_format({
            'size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'bold': True,
            'font':'Times New Roman',
            'text_wrap':True,
            'border':1,
        })
        black_format = workbook.add_format({'bg_color': 'black'})
        green_format = workbook.add_format({
        'bg_color': 'green',
        'font':'Times New Roman',
        'size': 11,
        'align': 'center',
        'valign': 'vcenter',
        'bold': True,
        })

        sheet = workbook.add_worksheet('Proposal Form')
        merge_format10.set_text_wrap()     
        row = 1
 
        row += 1
        
        for batch in batches:
            product_info_by_vendor = {}
            address_lines = []
            final_addresses = {}
            
            total_gross_weight=0
            total_net_weight=0

            if batch.arrival_date:
                arrival_date_str = batch.arrival_date.strftime('%d-%m-%Y')
            if batch.scheduled_date:
                scheduled_date_str = batch.scheduled_date.strftime('%d-%m-%Y')
            sheet.merge_range(row, 0, row, 8, "LOJİSTİK TEKLİF TALEBİ FORMATI", header_format)
            row+=1
            for index, customer in enumerate(batch.customer_ids, start=1):
                customer_name = customer.name
                delivery_address = f"{customer.name}, {customer.street}, {customer.city}, " \
                                    f"{customer.state_id.name if customer.state_id else ''}, " \
                                    f"{customer.zip}, {customer.country_id.name if customer.country_id else ''}"
                final_address = f"Teslim Adresi {index}"
                final_addresses[customer.name] = final_address
                address_lines.append(f"{final_address}: {delivery_address}")

                sheet.merge_range(row, 0, row+1, 1, f"Teslim Adresi {index} ", merge_format12)
                sheet.merge_range(row, 2, row+1, 8, delivery_address, merge_format10)
                row += 2
                sheet.merge_range(row, 0, row, 1, f"Teslim Tarihi {index} ", merge_format12)
                sheet.merge_range(row, 2, row, 8, arrival_date_str, merge_format10)
                row += 1
                
            sheet.merge_range(row, 0, row, 8, "", black_format)
            row += 1
            
            for line in batch.packaging_preparation_ids:
                product_key = f"{line.product_id}_{line.width}_{line.length}_{line.height}_{line.total_gross_weight}_{line.total_net_weight}_{line.stackable}_{line.pallet_no}"
                matching_transfers = batch.picking_ids.filtered(lambda p: line.product_id in p.move_lines.mapped('product_id'))

                for transfer in matching_transfers:
                    if transfer.partner_id:
                        vendor_name = transfer.partner_id.name
                        address_key = f"{vendor_name}_{transfer.partner_id.city}"
                        
                        if address_key not in product_info_by_vendor:
                            product_info_by_vendor[address_key] = {
                                'vendor_name': vendor_name,
                                'address': f"{transfer.partner_id.name}, {transfer.partner_id.street}, {transfer.partner_id.city}, "
                                        f"{transfer.partner_id.state_id.name if transfer.partner_id.state_id else ''}, "
                                        f"{transfer.partner_id.zip}, {transfer.partner_id.country_id.name if transfer.partner_id.country_id else ''}",
                                'products': {}
                            }

                        product_info = product_info_by_vendor[address_key]['products'].get(product_key, {
                            'volume': line.width * line.length * line.height,
                            'pallet_no': line.pallet_no,
                            'width': line.width,
                            'length': line.length,
                            'height': line.height,
                            'stackable': line.stackable,
                            'gross_weight': line.total_gross_weight,
                            'net_weight': line.total_net_weight,
                           
                        })


                        product_info_by_vendor[address_key]['products'][product_key] = product_info
                        
            address_counter = 1
            for address_key, vendor_info in product_info_by_vendor.items():
                total_gross_weight = 0
                total_net_weight = 0
                total_pallet = 0
                stackable_count = 0
                non_stackable_count = 0
                
                pallet_groups = defaultdict(list)
                
                for product_key, product in vendor_info['products'].items():
                    pallet_groups[product['pallet_no']].append(product)
                
                pallet_infos = []
                
                for pallet_number, products in pallet_groups.items():
                    largest_product = max(products, key=lambda p: p['width'] * p['length'] * p['height'])
                    
                    
                    total_gross_weight += largest_product['gross_weight']
                    total_net_weight += largest_product['net_weight']
                    
                    stackable_states = {p['stackable'] for p in products}
                    need_to_check = len(stackable_states) > 1
                    
                    if largest_product['stackable']:
                        stackable_count += 1
                    else:
                        non_stackable_count += 1
                    
                    volume_text = f"{largest_product['width']}x{largest_product['length']}x{largest_product['height']}mm"
                    stackable_text = "İstiflenebilir" if largest_product['stackable'] else "İstiflenemez"
                    check_text = " KONTROL ET" if need_to_check else ""
                    pallet_info = f"1 Kap, {volume_text}, {stackable_text}{check_text}"      
                    pallet_infos.append(pallet_info)
                
                total_pallet = len(pallet_groups)
                summary_text = f"{stackable_count} kap istiflenebilir, {non_stackable_count} kap istiflenemez"


                formatted_gross_weight=f"{total_gross_weight:.2f}"
                formatted_net_weight=f"{total_net_weight:.2f}"
                
                sheet.merge_range(row, 0, row + 1, 1, f"Alım Adresi {address_counter}", merge_format12)
                sheet.merge_range(row, 2, row + 1, 8, vendor_info['address'], merge_format10)
                row += 2
                sheet.merge_range(row, 0, row , 1, f"Alım Tarihi {address_counter}", merge_format12)
                sheet.merge_range(row, 2, row , 8, scheduled_date_str, merge_format10)
                row += 1
                sheet.merge_range(row, 0, row, 1, "Toplam Net KG", merge_format12)
                sheet.merge_range(row, 2, row, 8, str(formatted_net_weight) + " kg", merge_format10)
                row += 1
                sheet.merge_range(row, 0, row, 1, "Toplam Brüt KG", merge_format12)
                sheet.merge_range(row, 2, row, 8, str(formatted_gross_weight) + " kg", merge_format10)
                row += 1
                sheet.merge_range(row, 0, row, 1, "Toplam Kap Adedi ", merge_format12)
                sheet.merge_range(row, 2, row, 8, total_pallet, merge_format10)
                row += 1
                
                all_pallet_infos = "\n".join(pallet_infos) 
                

                all_pallet_infos_len = len(pallet_infos) * 1.2
                rounded_result = int(math.ceil(all_pallet_infos_len))
                
                sheet.merge_range(row, 0, row + rounded_result, 1, "Kap Ölçüleri", merge_format12)
                sheet.merge_range(row, 2, row + rounded_result, 8, all_pallet_infos, merge_format10)
                row += rounded_result+1
                sheet.merge_range(row, 0, row +1, 1, "İstiflenme Durumları", merge_format12)
                sheet.merge_range(row, 2, row +1, 8, summary_text, merge_format10)
                row+=2
                
                sheet.merge_range(row, 0, row, 8, "", black_format)
                row += 1
                
                address_counter += 1
                
            sheet.merge_range(row, 0, row+1 , 1, "Tercih edilen bir gümrük noktası var mı?", merge_format12)
            sheet.merge_range(row, 2, row+1, 4, "Evet", green_format)
            sheet.merge_range(row, 5, row+1 , 8, "Hayır", merge_format10)
            row+=2
            sheet.merge_range(row, 0, row +1, 1, "Varsa neresi?", merge_format12)
            sheet.merge_range(row, 2, row +1, 8, "Venlo", merge_format10)
            row+=2
            sheet.merge_range(row, 0, row, 8, "", black_format)
            row+=1
            sheet.merge_range(row, 0, row +1, 1, "Ek Not", merge_format12)
            sheet.merge_range(row, 2, row +1, 8, "", merge_format10)
            row+=2
            sheet.merge_range(row, 0, row, 8, '', border_format2)
            row+=1
            sheet.merge_range(row, 0, row, 8, "YENA DEMİR ÇELİK SAN. VE TİC. LTD ŞTİ", bottom_text)
            row+=1
            sheet.merge_range(row,0,row, 8, "Osmanağa Mah. Rıhtım Caddesi No:8/5 34714 Kadıköy/İstanbul +90 (216) 999 76 64 ", merge_format11)
