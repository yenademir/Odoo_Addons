from odoo import models, fields, api
import requests
import base64
from io import BytesIO
from datetime import datetime



class PackagingPreparation(models.Model):
    _name = 'packaging.preparation'
    _description = 'Packaging Preparation'

    name = fields.Char('Name')
    batch_id = fields.Many2one('stock.picking.batch', string='Batch Reference')
    customer_reference = fields.Char('Customer Reference')
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Text('Description')
    origin = fields.Char('Origin')
    package_quantity = fields.Float('Quantity')
    unit_of_measure = fields.Many2one('uom.uom', string='Unit of Measure')
    unit_net_weight = fields.Float('Unit Net Weight')
    total_net_weight = fields.Float('Total Net Weight')
    gross_weight = fields.Float('Gross Weight')
    total_gross_weight = fields.Float('Total Gross Weight')
    package_no = fields.Char('Package Number')
    width = fields.Float('Width')
    length = fields.Float('Length')
    height = fields.Float('Height')
    stackable = fields.Boolean('Stackable')
    pallet_no = fields.Integer('Pallet Number')

    @api.onchange('gross_weight')
    def _onchange_gross_weight(self):
        for record in self:
            record.total_gross_weight = record.gross_weight + record.total_net_weight

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
                # Eğer package_quantity tanımlı ve 0'dan büyükse
                if line.package_quantity <= 0 or line.package_quantity is False:
                    # Transfer edilen toplam adeti kullanarak tek bir kayıt oluştur
                    vals = {
                            'name': line.product_id.name,
                            'batch_id': batch.id,
                            'customer_reference': line.customer_reference,
                            'product_id': line.product_id.id,
                            'package_quantity': line.product_uom_qty,
                            'description': line.product_id.description_sale,
                            'origin' : line.product_id.origin_country_id.name,
                            'unit_of_measure': line.product_uom_id.id,
                            'unit_net_weight': line.product_id.weight, 
                            'total_net_weight': line.product_id.weight * line.product_uom_qty,
                            'package_no': 1,
                            'width': line.width,
                            'length': line.length,
                            'height': line.height,
                            'stackable': line.stackable,
                            'pallet_no': pallet_no,
                        }
                    no_package_data.append(vals)

                else:
                    # Tam paketler ve kalan miktar için kayıtlar oluştur
                    full_packages = int(line.product_uom_qty / line.package_quantity)
                    for _ in range(full_packages):
                        vals = {
                            'name': line.product_id.name,
                            'batch_id': batch.id,
                            'customer_reference': line.customer_reference,
                            'product_id': line.product_id.id,
                            'package_quantity': line.package_quantity,
                            'description': line.product_id.description_sale,
                            'origin' : line.product_id.origin_country_id.name,
                            'unit_of_measure': line.product_uom_id.id,
                            'unit_net_weight': line.product_id.weight, 
                            'total_net_weight': line.product_id.weight * line.package_quantity,
                            'package_no': 1,
                            'width': line.width,
                            'length': line.length,
                            'height': line.height,
                            'stackable': line.stackable,
                            'pallet_no': pallet_no,
                        }
                        PackagingPreparation.create(vals)
                        pallet_no += 1

                    remaining_qty = line.product_uom_qty % line.package_quantity
                    if remaining_qty > 0:
                        vals = {
                            'name': line.product_id.name,
                            'batch_id': batch.id,
                            'customer_reference': line.customer_reference,
                            'product_id': line.product_id.id,
                            'package_quantity': remaining_qty,
                            'description': line.product_id.description_sale,
                            'origin' : line.product_id.origin_country_id.name,
                            'unit_of_measure': line.product_uom_id.id,
                            'unit_net_weight': line.product_id.weight, 
                            'total_net_weight': line.product_id.weight * line.package_quantity,
                            'package_no': 1,
                            'width': line.width,
                            'length': line.length,
                            'height': line.height,
                            'stackable': line.stackable,
                            'pallet_no': pallet_no,
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
        readonly=True 
    )
    length = fields.Integer(
        string='Length',
        related='product_id.packaging_ids.package_type_id.packaging_length',
        store=True,
        readonly=True
    )
    width = fields.Integer(
        string='Width',
        related='product_id.packaging_ids.package_type_id.width',
        store=True,
        readonly=True
    )
    height = fields.Integer(
        string='Height',
        related='product_id.packaging_ids.package_type_id.height',
        store=True,
        readonly=True
    )
    stackable = fields.Boolean(
        string='Stackable',
        related='product_id.packaging_ids.package_type_id.stackable',
        store=True,
        readonly=True
    )
    customer_reference = fields.Char(
        string='Customer Reference',
        related='picking_id.purchase_id.customer_reference',
        store=True,
        readonly=True
    )

class PackagingPreparationReportXlsx(models.AbstractModel):
    _name = 'report.yena_packaging_preparation.report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, batches):
        bold_format = workbook.add_format({'bold': True})
        wrap_format = workbook.add_format({'text_wrap': True, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'size': 10})
        centered_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'size': 13})
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
            'size': 14
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

        for batch in batches:
            sheet = workbook.add_worksheet('Batch %s' % batch.name)

            # PO(s) # için müşteri referanslarını topla
            customer_references = set(line.customer_reference for line in batch.move_line_ids if line.customer_reference)
            po_text = 'PO(s) # ' + ', '.join(customer_references)

            # Project No(s) # için proje numaralarını topla
            project_nos = set(project.name for project in batch.project_ids)
            project_text = 'Project No(s) # ' + ', '.join(project_nos)

            transportation_code = batch.transportation_code if batch.transportation_code else ''
            despatch_date = batch.edespatch_date if batch.edespatch_date else ''
            
            # Tarih formatını ayarla (eğer despatch_date varsa)
            if despatch_date:
                despatch_date = datetime.strftime(despatch_date, '%Y-%m-%d')

            shipment_info_text = f'Shipment Number: {transportation_code} / Shipment Date: {despatch_date}'

            # Sütun genişliklerini ayarla
            column_widths = [6, 9, 14.5, 54, 15.5, 10, 6.50, 16, 23, 16.5, 17.5, 24, 12.5, 12.5, 12.5, 13.5, 12]
            for i, width in enumerate(column_widths):
                sheet.set_column(i, i, width)

            url = 'https://yenastorage.blob.core.windows.net/odoo-container/YENA_logo.png'
            response = requests.get(url)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                sheet.insert_image('A1:D8', 'YENA_logo.png', {'image_data': image_data, 'x_scale': 0.3, 'y_scale': 0.3})

            
            # İlk 9 satırı ve A - E hücrelerini birleştir
            sheet.merge_range('A1:C9', 'PACKING LIST', merge_format14)
            sheet.merge_range('A10:C10', po_text, merge_format14left)
            sheet.merge_range('A11:C11', project_text, merge_format14left)
            sheet.merge_range('A12:C12', shipment_info_text, merge_format14left)
            sheet.merge_range('F1:K1', 'İRSALİYE NO / WAY BILL NO :', merge_format10)
            sheet.merge_range('F2:K2', 'İHRACATÇI /SHIPPER:', merge_format10)
            sheet.merge_range('F3:K9', 'YENA DEMİR ÇELİK SAN. TİC.LTD.ŞTİ.\nÖrnek Mahallesi, Ercüment Batanay Sokak.\nNo:14A, A2 Blok, Kat:32, D:270 34704\nAtaşehir/İstanbul', merge_format18)
            sheet.merge_range('L1:Q1', 'FATURA / INVOICE :' , merge_format10)
            sheet.merge_range('L2:Q2', 'ALICI / RECEIVER:' , merge_format10)
            sheet.merge_range('L3:Q9', 'YENA ENGINEERING B.V. WTC ROTTERDAM BEURSPLEIN 37\n3011 AA\nROTERDAM/ NETHERLANDS' , merge_format18)

            # Başlıkları ekle
            headers = [
                'S.NO', 'ORDER NO', 'POSE', 'AÇIKLAMA\nEXPLANATION', 'ÜRÜN MENŞEİ\nORIGIN OF MATERIAL',
                'MIKTARI\nQUANTITY', 'BİRİM\nUNIT', 'NET AĞIRLIK (KG)\nNET WEIGHT (KG)',
                'TOPLAM NET AĞIRLIK (KG)\nTOTAL NET WEIGHT (KG)', 'KAP ADETİ\nPACKAGE QUANTITY',
                'BRÜT AĞIRLIK (KG)\nTARE WEİGHT (KG)', 'BRÜT AĞIRLIK (KG)\nGROSS WEİGHT (KG)',
                'EN (MM)\nWIDTH (MM)', 'BOY (MM)\nLENGTH (MM)', 'YÜKSEKLİK (MM)\nHEIGHT (MM)', 'STACKABLE', 'PALLET NO'
            ]
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
            row = 12  # 13. satırdan başla (0-indexed)

            # Başlık satırını yaz ve kalın biçimi uygula
            for col, header in enumerate(headers):
                sheet.write(row, col, header, wrap_format)

            for pallet_no, data in pallet_data.items():
                start_row = row + 1  # Grup için başlangıç satırı
                for line in data['lines']:
                    row += 1

                    # S.NO
                    sheet.write(row, 0, row - 12, centered_format)
                    # ORDER NO (Customer Reference)
                    sheet.write(row, 1, line.customer_reference or '', centered_format)
                    # Drawing Number (Product)
                    sheet.write(row, 2, line.product_id.display_name, centered_format)
                    # Product Description (product_id.description)
                    sheet.write(row, 3, line.product_id.description, centered_format)
                    # Origin (product_id.origin_country_id)
                    sheet.write(row, 4, line.product_id.origin_country_id.name, centered_format)
                    # Quantity (Package Quantity)
                    sheet.write(row, 5, line.package_quantity, centered_format)
                    # UNIT (Unit of Measure)
                    sheet.write(row, 6, line.unit_of_measure.name, centered_format)
                    # Net(kg) (Unit Net Weight)
                    sheet.write(row, 7, line.unit_net_weight, centered_format)
                    # Net(kg) (Total Net Weight)
                    sheet.write(row, 8, line.total_net_weight, centered_format)
                    # Paket Adeti (Statik 1)
                    sheet.write(row, 9, '1', centered_format)
                    # Brüt(kg) (Gross Weight)
                    sheet.write(row, 10, line.gross_weight, centered_format)
                    # Brüt(kg) (Total Gross Weight)
                    sheet.write(row, 11, line.total_gross_weight, centered_format)
                    # Package Width (EN (MT) WIDTH)
                    sheet.write(row, 12, line.width, centered_format)
                    # Package Length (EN (MT) LENGTH)
                    sheet.write(row, 13, line.length, centered_format)
                    # Package Height (EN (MT) HEIGTH)
                    sheet.write(row, 14, line.height, centered_format)
                    # STACKABLE
                    sheet.write(row, 15, 'Yes' if line.stackable else 'No', centered_format)
                    # Package Number (Pallet Number)
                    sheet.write(row, 16, line.pallet_no, centered_format)

                end_row = row  # Grup için bitiş satırı
                if len(data['lines']) > 1:
                    # İlk satırı al ve birleştir
                    first_line = data['lines'][0]
                    sheet.merge_range(start_row, 7, end_row, 7, data['unit_net_weight'], centered_format)
                    sheet.merge_range(start_row, 8, end_row, 8, data['total_net_weight'], centered_format)
                    sheet.merge_range(start_row, 9, end_row, 9, '1', centered_format)
                    sheet.merge_range(start_row, 10, end_row, 10, data['gross_weight'], centered_format)
                    sheet.merge_range(start_row, 11, end_row, 11, data['total_gross_weight'], centered_format)
                    sheet.merge_range(start_row, 12, end_row, 12, '', centered_format)
                    sheet.merge_range(start_row, 13, end_row, 13, '', centered_format)
                    sheet.merge_range(start_row, 14, end_row, 14, '', centered_format)
                    sheet.merge_range(start_row, 15, end_row, 15, first_line.stackable, centered_format)
                    sheet.merge_range(start_row, 16, end_row, 16, first_line.pallet_no, centered_format)
