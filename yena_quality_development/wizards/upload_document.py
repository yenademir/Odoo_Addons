from odoo import models, fields, api
from odoo.exceptions import ValidationError
import requests
import base64
import logging
_logger = logging.getLogger(__name__)

class DocumentUploadWizard(models.Model):
    _name = 'document.upload.wizard'
    _description = 'Document Upload Wizard'
 
    certificate_line_ids = fields.One2many(
        'document.upload.wizard.line', 'wizard_id', string='Certificate Lines'
    )

    measurement_report_ids = fields.One2many(
        'document.upload.wizard.measurement.report', 'wizard_id', string='Measurement Reports'
    )

    galvanize_ids = fields.One2many(
        'document.upload.wizard.galvanize', 'wizard_id', string='Galvanize'
    )

    packaging_ids = fields.One2many(
        'document.upload.wizard.packaging', 'wizard_id', string='Packaging'
    )

    purchase_name = fields.Many2one('purchase.order', string="Purchase Name")
    project_number = fields.Many2one('project.project', string="Project Number")
    product_id = fields.Many2one('product.product', string='Pose Nr.')
    notes = fields.Html(string="Notes")

    line_ids = fields.One2many('document.upload.wizard.line', 'wizard_id', string='Lines')
    all_lot_numbers_filled = fields.Boolean(string='All Lot Numbers Filled', compute='_compute_all_lot_numbers_filled')
    
    def write(self, vals):
        result = super(DocumentUploadWizard, self).write(vals)

        # project_number için olan mevcut kodunuz...
        if 'project_number' in vals:
            project_number_id = vals['project_number']
            for wizard in self:
                wizard.certificate_line_ids.write({'project_number': project_number_id})
                # Diğer bağlı one2many alanları için de benzer işlem yapılabilir

        return result

    @api.depends('line_ids.lot_number')
    def _compute_all_lot_numbers_filled(self):
        for record in self:
            record.all_lot_numbers_filled = all(line.lot_number for line in record.line_ids)

    

    def button_generate_lot_sequence(self):
        self.ensure_one()
        
        lines = self.certificate_line_ids
        for line in lines:
            line.generate_lot_sequence()
        return {
            'name': 'Document Upload Wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'document.upload.wizard',
            'target': 'new',
            'res_id': self.id,
        }
    
class DocumentUploadWizardLine(models.Model):
    _name = 'document.upload.wizard.line'
    _description = 'Document Upload Wizard Line'

    wizard_id = fields.Many2one('document.upload.wizard', string='Wizard')
    required_document = fields.Char(string='Required Document')
    uploaded_document = fields.Char(string='Doc.')
    dimension = fields.Char(string="Dimension")
    is_uploaded = fields.Boolean(string='Yüklemeden Devam Et')
    upload_document = fields.Binary(string='Upload Document')
    lot_number = fields.Char(string="1.Lot Nr")
    project_number = fields.Many2one('project.project', string="Project Number")
    purchase_name = fields.Many2one(
        'purchase.order', 
        string="Order Reference", 
        related='wizard_id.purchase_name',
    )
    product_id = fields.Many2one(
        'product.product', 
        string="Pose No",
        related='wizard_id.product_id',
        )
    customer_id = fields.Many2one(
        'res.partner', 
        string="Customer",
        related='project_number.partner_id',
        )
    supplier_id =fields.Many2one(
        'res.partner', 
        string="Supplier",
        related='purchase_name.partner_id',        
        )
    manufacturer = fields.Char(string="Manufacturer")
    certificate_number = fields.Char(string="Cert. Nr.")
    heat_number = fields.Char(string="Heat Nr.")
    standart = fields.Char(string="Std.")

    material_certificate_id = fields.Many2one(
        'material.certificate', string='Material Certificate'
    )


    def generate_lot_sequence(self):
    sequence_code = 'document.upload.wizard.line.lot.number'
    for record in self:
        if not record.lot_number:
            sequence_number = self.env['ir.sequence'].next_by_code(sequence_code)
            record.lot_number = sequence_number
                
    @api.model_create_multi
    def create(self, vals_list):
        records = super(DocumentUploadWizardLine, self).create(vals_list)
        for record in records:
            if record.wizard_id and record.wizard_id.project_number:
                # Ebeveyn wizard'dan project_number'ı al ve bu kayda ata
                record.project_number = record.wizard_id.project_number.id
        return records
    
    def filename_extract_from_binary_field(self):
        if self.upload_document:
            # Odoo, binary alanlarda dosya adını 'filename;' önekini kullanarak saklar
            file_info = self.upload_document.decode().split(';')[0]
            file_name = file_info.split('=')[-1] if '=' in file_info else 'unknown_file'
            return file_name
        return 'unknown_file'
    
    @api.onchange('upload_document')
    def onchange_upload_document(self):
        if self.upload_document:
            # Dosya yükleme işlemi
            success = self.upload_to_cdn()
            if success:
                # Yükleme başarılıysa 'upload_document' alanını boşalt
                self.upload_document = False


    def upload_to_cdn(self):
        file_data = self.upload_document
        if file_data:
            api_url = "https://portal-test.yenaengineering.nl/api/qualitydocuments"
            file_name = self.required_document if self.required_document else "certificate_file"

            files = {
                'quality_documents': (file_name, base64.b64decode(file_data), 'application/octet-stream')
            }
            data = {'purchase': self.wizard_id.purchase_name}

            response = requests.post(api_url, files=files, data=data)
            if response.status_code == 201:
                result = response.json()
                certificate_url = result['data']['certificate_url']

                # Google Drive viewer URL'si ile birleştir
                viewer_url = "https://drive.google.com/viewerng/viewer?embedded=true&url=" + certificate_url
                self.uploaded_document = viewer_url

                return True 
            return False 
        
class DocumentUploadWizardMeasurementReport(models.Model):
    _name = 'document.upload.wizard.measurement.report'
    _description = 'Document Upload Wizard Measurement Report'

    wizard_id = fields.Many2one('document.upload.wizard', string='Wizard')
    name = fields.Char(string='Name')
    upload_document = fields.Binary(string='Upload Document')
    is_uploaded = fields.Boolean(string='Yüklemeden Devam Et')
    uploaded_document = fields.Char(string='Uploaded Document')
    product_id = fields.Many2one(
        'product.product', 
        string="Pose No",
        related='wizard_id.product_id',
        )

    @api.onchange('upload_document')
    def onchange_upload_document(self):
        if self.upload_document:
            # Dosya yükleme işlemi
            success = self.upload_to_cdn()
            if success:
                # Yükleme başarılıysa 'upload_document' alanını boşalt
                self.upload_document = False

    def upload_to_cdn(self):
        file_data = self.upload_document
        if file_data:
            api_url = "https://portal-test.yenaengineering.nl/api/qualitydocuments"
            
            product_name = self.product_id.name if self.product_id else ''
            file_name = "{} {}".format(product_name, self.name or 'unknown_file').strip()
            
            files = {
                'quality_documents': (file_name, base64.b64decode(file_data), 'application/octet-stream')
            }
            data = {'purchase': self.wizard_id.purchase_name.name}

            response = requests.post(api_url, files=files, data=data)
            if response.status_code == 201:
                result = response.json()
                certificate_url = result['data']['certificate_url']

                # Google Drive viewer URL'si ile birleştir
                viewer_url = "https://drive.google.com/viewerng/viewer?embedded=true&url=" + certificate_url
                self.uploaded_document = viewer_url

                return True  # Başarı durumunu belirt
            return False  # Başarısızlık durumunu belirt
        
class DocumentUploadWizardGalvanize(models.Model):
    _name = 'document.upload.wizard.galvanize'
    _description = 'Document Upload Wizard Galvanize'

    wizard_id = fields.Many2one('document.upload.wizard', string='Wizard')
    name = fields.Char(string='Name')
    upload_document = fields.Binary(string='Upload Document')
    is_uploaded = fields.Boolean(string='Yüklemeden Devam Et')
    uploaded_document = fields.Char(string='Uploaded Document')
    product_id = fields.Many2one(
        'product.product', 
        string="Pose No",
        related='wizard_id.product_id',
        )
    
    def filename_extract_from_binary_field(self):
        if self.upload_document:
            # Odoo, binary alanlarda dosya adını 'filename;' önekini kullanarak saklar
            file_info = self.upload_document.decode().split(';')[0]
            file_name = file_info.split('=')[-1] if '=' in file_info else 'unknown_file'
            return file_name
        return 'unknown_file'

    @api.onchange('upload_document')
    def onchange_upload_document(self):
        if self.upload_document:
            # Dosya yükleme işlemi
            success = self.upload_to_cdn()
            if success:
                # Yükleme başarılıysa 'upload_document' alanını boşalt
                self.upload_document = False

    def upload_to_cdn(self):
        file_data = self.upload_document
        if file_data:
            api_url = "https://portal-test.yenaengineering.nl/api/qualitydocuments"
            
            # Dosya adını al
            product_name = self.product_id.name if self.product_id else ''
            file_name = "{} {}".format(product_name, self.name or 'unknown_file').strip()

            files = {
                'quality_documents': (file_name, base64.b64decode(file_data), 'application/octet-stream')
            }
            data = {'purchase': self.wizard_id.purchase_name.name}

            response = requests.post(api_url, files=files, data=data)
            if response.status_code == 201:
                result = response.json()
                certificate_url = result['data']['certificate_url']

                # Google Drive viewer URL'si ile birleştir
                viewer_url = "https://drive.google.com/viewerng/viewer?embedded=true&url=" + certificate_url
                self.uploaded_document = viewer_url

                return True  # Başarı durumunu belirt
            return False  # Başarısızlık durumunu belirt

class DocumentUploadWizardPackaging(models.Model):
    _name = 'document.upload.wizard.packaging'
    _description = 'Document Upload Wizard Packaging'

    wizard_id = fields.Many2one('document.upload.wizard', string='Wizard')
    name = fields.Char(string='Name')
    upload_document = fields.Binary(string='Upload Document')
    is_uploaded = fields.Boolean(string='Yüklemeden Devam Et')
    uploaded_document = fields.Char(string='Uploaded Document')
    product_id = fields.Many2one(
        'product.product', 
        string="Pose No",
        related='wizard_id.product_id',
        )
    
    def filename_extract_from_binary_field(self):
        if self.upload_document:
            # Odoo, binary alanlarda dosya adını 'filename;' önekini kullanarak saklar
            file_info = self.upload_document.decode().split(';')[0]
            file_name = file_info.split('=')[-1] if '=' in file_info else 'unknown_file'
            return file_name
        return 'unknown_file'

    @api.onchange('upload_document')
    def onchange_upload_document(self):
        if self.upload_document:
            # Dosya yükleme işlemi
            success = self.upload_to_cdn()
            if success:
                # Yükleme başarılıysa 'upload_document' alanını boşalt
                self.upload_document = False

    def upload_to_cdn(self):
        file_data = self.upload_document
        if file_data:
            api_url = "https://portal-test.yenaengineering.nl/api/qualitydocuments"
            
            # Dosya adını al
            product_name = self.product_id.name if self.product_id else ''
            file_name = "{} {}".format(product_name, self.name or 'unknown_file').strip()
            
            files = {
                'quality_documents': (file_name, base64.b64decode(file_data), 'application/octet-stream')
            }
            data = {'purchase': self.wizard_id.purchase_name.name}

            response = requests.post(api_url, files=files, data=data)
            if response.status_code == 201:
                result = response.json()
                certificate_url = result['data']['certificate_url']

                # Google Drive viewer URL'si ile birleştir
                viewer_url = "https://drive.google.com/viewerng/viewer?embedded=true&url=" + certificate_url
                self.uploaded_document = viewer_url

                return True  # Başarı durumunu belirt
            return False  # Başarısızlık durumunu belirt

