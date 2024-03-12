from odoo import models, fields, api

class MaterialCertificate(models.Model):
    _name = 'material.certificate'
    _description = 'Material Certificate'
    
    name = fields.Char('Name', compute="_compute_name")
    material_type = fields.Selection([
    ('sheet', 'Sheet'),
    ('pipe', 'Pipe'),
    ('box', 'Box'),
    ('square', 'Square'),
    ('bracket', 'Bracket'),
    ('flat', 'Flat'),
    ('billet', 'Billet'),
    ], string="Material Type")
    material_thickness = fields.Float(string="Thickness")
    material_width = fields.Float(string="Width")
    material_length = fields.Float(string="Length")
    material_grade = fields.Char(string="Grade", required=True)
    material_outer_diameter=fields.Float(string="Outer Diameter")
    material_wall=fields.Float(string="Wall")
    material_height=fields.Float(string="Height")
    material_diameter=fields.Float(string="Diameter")
    
    @api.depends('material_grade', 'material_thickness', 'material_width', 'material_length',
                 "material_outer_diameter","material_wall","material_diameter","material_height")
    def _compute_name(self):
        
        def sheet_name(rec):
            return f"{rec.material_thickness}mm x {rec.material_width}mm x {rec.material_length}mm"
        def pipe_name(rec):
            return f"{rec.material_outer_diameter}Ø mm x {rec.material_wall}mm x {rec.material_length}mm"
        def square_name(rec):
            return f"{rec.material_width}mm x{rec.material_length}mm"
        def box_name(rec):
            return f"{rec.material_thickness}mm x {rec.material_height}mm x {rec.material_width}mm x{rec.material_length}mm"
        def bracket_name(rec):
            return f"{rec.material_thickness}mm x {rec.material_height}mm x {rec.material_width}mm x{rec.material_length}mm"
        def flat_name(rec):
            return f"{rec.material_thickness}mm x {rec.material_width}mm x {rec.material_length}mm"
        def billet_name(rec):
            return f"{rec.material_diameter}Ø mm x{rec.material_length}mm"
        
        
        name_generator = {
        'sheet': sheet_name,
        'pipe': pipe_name,
        'square':square_name,
        'box':box_name,
        'bracket':bracket_name,
        'flat':flat_name,
        'billet':billet_name,
        }    
        for record in self:
            name = f"{record.material_grade}, "
            generator = name_generator.get(record.material_type)
            if generator:
                name += generator(record)
            else:
                name += "Please enter the measurements."
            record.name = name

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    material_certificate = fields.Many2many(
        'material.certificate',
        string = 'Sub Part Materials'
    )
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def write(self, vals):
        result = super(PurchaseOrder, self).write(vals)
        if 'project_purchase' in vals: 
            project_purchase_id = vals['project_purchase']
            # İlgili tüm DocumentUploadWizard kayıtlarını bul ve güncelle
            for order in self:
                for line in order.order_line:
                    if line.wizard_id:
                        # project_purchase alanı güncellendiğinde wizard'ın project_number alanını güncelle
                        line.wizard_id.write({'project_number': project_purchase_id})
        return result

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
 
    material_certificate_id = fields.Many2many(
        'material.certificate',
        string='Material Certificate'
    )
    wizard_id = fields.Many2one('document.upload.wizard', string="Document Upload Wizard")

    material_certificate_status = fields.Selection([
        ('not_ok', 'Eksik Belge'),
        ('conditional_acceptance', 'Şartlı Kabul'),
        ('done', 'Tamamlandı'),
    ], string="Material Certificate", compute='_compute_material_certificate_status', store=True)

    measurement_report_status = fields.Selection([
        ('not_ok', 'Eksik Belge'),
        ('conditional_acceptance', 'Şartlı Kabul'),
        ('done', 'Tamamlandı'),
    ], string="Measurement Report", compute='_compute_measurement_report_status', store=True)

    galvanize_status = fields.Selection([
        ('not_ok', 'Eksik Belge'),
        ('conditional_acceptance', 'Şartlı Kabul'),
        ('done', 'Tamamlandı'),
    ], string="Galvanize", compute='_compute_galvanize_status', store=True)

    packaging_status = fields.Selection([
        ('not_ok', 'Eksik Belge'),
        ('conditional_acceptance', 'Şartlı Kabul'),
        ('done', 'Tamamlandı'),
    ], string="Packaging", compute='_compute_packaging_status', store=True)

    quality_status = fields.Selection([
        ('not_ok', 'Eksik Belge'),
        ('conditional_acceptance', 'Şartlı Kabul'),
        ('done', 'Tamamlandı'),
    ], string="Quality Status", compute='_compute_quality_status', store=True)

    @api.depends('wizard_id.certificate_line_ids.uploaded_document', 'wizard_id.certificate_line_ids.is_uploaded')
    def _compute_material_certificate_status(self):
        for record in self:
            if record.wizard_id:
                lines = record.wizard_id.certificate_line_ids
                any_uploaded = any(line.uploaded_document for line in lines)
                all_uploaded = all(line.uploaded_document for line in lines)
                any_is_uploaded = any(line.is_uploaded for line in lines)
                any_line_empty = any(not (line.uploaded_document or line.is_uploaded) for line in lines)

                if any_line_empty:  # Öncelikle herhangi bir satır boş mu diye kontrol et
                    record.material_certificate_status = 'not_ok'
                elif all_uploaded:
                    record.material_certificate_status = 'done'
                elif any_uploaded or any_is_uploaded:
                    record.material_certificate_status = 'conditional_acceptance'


    @api.depends('wizard_id.measurement_report_ids.uploaded_document', 'wizard_id.measurement_report_ids.is_uploaded')
    def _compute_measurement_report_status(self):
        for record in self:
            if record.wizard_id:
                lines = record.wizard_id.measurement_report_ids
                any_uploaded = any(line.uploaded_document for line in lines)
                all_uploaded = all(line.uploaded_document for line in lines)
                any_is_uploaded = any(line.is_uploaded for line in lines)
                any_line_empty = any(not (line.uploaded_document or line.is_uploaded) for line in lines)

                if any_line_empty:  # Öncelikle herhangi bir satır boş mu diye kontrol et
                    record.measurement_report_status = 'not_ok'
                elif all_uploaded:
                    record.measurement_report_status = 'done'
                elif any_uploaded or any_is_uploaded:
                    record.measurement_report_status = 'conditional_acceptance'
    
    @api.depends('wizard_id.galvanize_ids.uploaded_document', 'wizard_id.galvanize_ids.is_uploaded')
    def _compute_galvanize_status(self):
        for record in self:
            if record.wizard_id:
                lines = record.wizard_id.galvanize_ids
                any_uploaded = any(line.uploaded_document for line in lines)
                all_uploaded = all(line.uploaded_document for line in lines)
                any_is_uploaded = any(line.is_uploaded for line in lines)
                any_line_empty = any(not (line.uploaded_document or line.is_uploaded) for line in lines)

                if any_line_empty:  # Öncelikle herhangi bir satır boş mu diye kontrol et
                    record.galvanize_status = 'not_ok'
                elif all_uploaded:
                    record.galvanize_status = 'done'
                elif any_uploaded or any_is_uploaded:
                    record.galvanize_status = 'conditional_acceptance'

    @api.depends('wizard_id.packaging_ids.uploaded_document', 'wizard_id.packaging_ids.is_uploaded')
    def _compute_packaging_status(self):
        for record in self:
            if record.wizard_id:
                lines = record.wizard_id.packaging_ids
                any_uploaded = any(line.uploaded_document for line in lines)
                all_uploaded = all(line.uploaded_document for line in lines)
                any_is_uploaded = any(line.is_uploaded for line in lines)
                any_line_empty = any(not (line.uploaded_document or line.is_uploaded) for line in lines)

                if any_line_empty:  # Öncelikle herhangi bir satır boş mu diye kontrol et
                    record.packaging_status = 'not_ok'
                elif all_uploaded:
                    record.packaging_status = 'done'
                elif any_uploaded or any_is_uploaded:
                    record.packaging_status = 'conditional_acceptance'
                    
    @api.depends('material_certificate_status', 'measurement_report_status', 'galvanize_status', 'packaging_status')
    def _compute_quality_status(self):
        for record in self:
            statuses = [
                record.material_certificate_status,
                record.measurement_report_status,
                record.galvanize_status,
                record.packaging_status
            ]

            if 'not_ok' in statuses:
                record.quality_status = 'not_ok'
            elif all(status == 'done' for status in statuses):
                record.quality_status = 'done'
            elif any(status == 'conditional_acceptance' for status in statuses):
                record.quality_status = 'conditional_acceptance'
            else:
                record.quality_status = False


    def open_document_upload_wizard(self):
        certificate_ids = self.filtered(lambda line: line.product_id and line.product_id.material_certificate).mapped('product_id.material_certificate').ids
        wizard = self.wizard_id

        # Sertifikalar için veri alın
        certificates_data = self.env['material.certificate'].browse(certificate_ids)
        project_number_id = self.order_id.project_purchase.id  # Proje numarasını al
        certificate_line_values = []
        for cert in certificates_data:
            certificate_line_values.append((0, 0, {
                'material_certificate_id': cert.id,
                'required_document': cert.name,
                'is_uploaded': False,
                'project_number': project_number_id,
            }))

        if wizard and wizard.exists():
            # Mevcut wizard için sertifika bilgilerini güncelle
            existing_certificate_ids = [line.material_certificate_id.id for line in wizard.certificate_line_ids]
            new_certificate_ids = [cert[2]['material_certificate_id'] for cert in certificate_line_values if cert[2]['material_certificate_id'] not in existing_certificate_ids]

            if new_certificate_ids:
                for cert_id in new_certificate_ids:
                    self.env['document.upload.wizard.line'].create({
                        'wizard_id': wizard.id,
                        'material_certificate_id': cert_id,
                        'required_document': self.env['material.certificate'].browse(cert_id).name,
                        'is_uploaded': False,
                        'project_number': project_number_id
                    })
            else:
                # Mevcut satırlar için project_number alanını güncelle
                for line in wizard.certificate_line_ids:
                    line.project_number = project_number_id

        else:
            measurement_report_values = [(0, 0, {
                'name': 'Ölçü Boyut Kontrol',
                'is_uploaded': False
            })]

            galvanize_values = [(0, 0, {
                'name': 'Galvanizing / Painting / Coating',
                'is_uploaded': False
            })]

            packaging_values = [(0, 0, {
                'name': 'Paketleme',
                'is_uploaded': False
            })]
            
            project_number_id = self.order_id.project_purchase.id
            wizard = self.env['document.upload.wizard'].create({
                'certificate_line_ids': certificate_line_values,
                'measurement_report_ids': measurement_report_values,
                'galvanize_ids': galvanize_values,
                'packaging_ids': packaging_values,
                'purchase_name': self.order_id.id,
                'project_number': project_number_id,
                'product_id': self.product_id.id,

            })
            self.wizard_id = wizard.id

        return {
            'name': 'Document Upload Wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'document.upload.wizard',
            'target': 'new',
            'context': {
                'default_certificate_ids': certificate_ids,
                'active_id': self.id,
                'default_purchase_name': self.order_id.id,
                'default_project_number': project_number_id,
                'default_product_id': self.product_id.id,
            },
            'res_id': self.wizard_id.id,
        }
