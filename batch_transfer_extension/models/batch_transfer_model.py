from odoo import api, fields, models


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'
    _description = "Batch Transfer"
    _order = "name desc"
    edespatch_date = fields.Datetime(string="Real Departure Date", store=True)
    situation = fields.Selection(
        [("to_be_planned", "To Be Planned"),
         ("on_the_way", "On The Way"),
         ("arrived", "Arrived")],
        string="Situation",
        store=True,
        inverse='_inverse_situation'
    )
    customer_ids = fields.Many2many(
        'res.partner',
        'batch_customer_rel',  # Bu bir ilişki tablosudur
        'batch_id',  # Bu, bu modeldeki alanı temsil eder
        'partner_id',  # Bu, ilişkilendirilmekte olan modeldeki alanı temsil eder
        string='Customers'
    )
    vendor_ids = fields.Many2many(
        'res.partner',
        'batch_vendor_rel',  # Bu da başka bir ilişki tablosudur
        'batch_id',  # Bu, bu modeldeki alanı temsil eder
        'partner_id',  # Bu, ilişkilendirilmekte olan modeldeki alanı temsil eder
        string='Vendors'
    )
    project_ids = fields.Many2many('project.project', string='Projects', compute='_compute_projects', store=True)
    purchase_count = fields.Integer(string='Purchases', compute='_compute_purchase_count')
    scheduled_date = fields.Datetime(string='Scheduled Date')
    arrival_date = fields.Date(string='Arrival Date')
    # shipping_type = fields.Selection([
    #   ('air', 'Airline'),
    #  ('road', 'Highway'),
    # ('sea', 'Seaway')
    # ], string='Shipping Type')
    vehicle_type_id = fields.Many2one('vehicle.type', string='Araç Türü')
    airtag_url = fields.Char(string='Airtag URL', compute='_compute_airtag_url', store=True)  # Hesaplanmış URL alanı
    transportation_code = fields.Char(
        string='Transportation Code',
        inverse='_inverse_transportation_code'
    )
    import_decleration_number = fields.Char(string='Custom Decleration No', inverse='_inverse_import_decleration_number', store=True)
    edespatch_carrier_id = fields.Many2one('res.partner', string='Carrier Partner', domain=[('industry_id.id', '=', 139)], inverse='_inverse_edespatch_carrier_id')
    transport_type = fields.Selection([
        ('airtransport', 'Air Transport'),
        ('roadtransport', 'Road Transport'),
        ('railtransport', 'Rail Transport'),
        ('maritimetransport', 'Maritime Transport'),
    ], string='Transport Type',  default="roadtransport", inverse='_inverse_transport_type')
    vehicle_id = fields.Char(string='Vehicle Id', inverse='_inverse_vehicle_id')
    transport_equipment_id = fields.Char(string='Transport Equipment "Trailer" Plate Id', inverse='_inverse_transport_equipment_id')
    rail_car_id = fields.Char(string='Rail Car Id', inverse='_inverse_rail_car_id')
    maritimetransport = fields.Boolean(string='Maritime Transport', inverse='_inverse_maritimetransport_fields')
    vessel_name = fields.Char(string='Vessel Name', inverse='_inverse_maritimetransport_fields')
    radio_call_sign_id = fields.Char(string='Radio Call Sign ID', inverse='_inverse_maritimetransport_fields')
    ships_requirements = fields.Text(string='Ships Requirements', inverse='_inverse_maritimetransport_fields')
    gross_tonnage_measure = fields.Float(string='Gross Tonnage Measure', inverse='_inverse_maritimetransport_fields')
    net_tonnage_measure = fields.Float(string='Net Tonnage Measure', inverse='_inverse_maritimetransport_fields')
    registry_cert_doc_ref = fields.Char(string='Registry Certificate Document Reference', inverse='_inverse_maritimetransport_fields')
    registry_port_location = fields.Char(string='Registry Port Location', inverse='_inverse_maritimetransport_fields')
    edespatch_delivery_type = fields.Selection(
        [
            ("edespatch", "E-Despatch"),
            ("printed", "Printed")
        ],
        compute='_compute_edespatch_delivery_type',
        inverse='_inverse_edespatch_delivery_type',
        store=True,
        readonly=False
    )
    driver_ids = fields.Many2many(
        'res.partner',
        'batch_driver_rel',
        'batch_id',
        'partner_id',  
        string='Drivers',
        inverse='_inverse_driver_ids',
        store=True, 
    )

    @api.depends('picking_ids.edespatch_carrier_id')
    def _inverse_edespatch_carrier_id(self):
        for batch in self:
            batch.picking_ids.write({'edespatch_carrier_id': batch.edespatch_carrier_id.id})

    @api.depends('picking_ids.transportation_code')
    def _inverse_transportation_code(self):
        for batch in self:
            batch.picking_ids.write({'transportation_code': batch.transportation_code})

    def _inverse_situation(self):
        for batch in self:
            batch.picking_ids.write({'situation': batch.situation})
    
    # transport_type için inverse fonksiyon
    @api.depends('picking_ids.transport_type')
    def _inverse_transport_type(self):
        for batch in self:
            batch.picking_ids.write({'transport_type': batch.transport_type})

    # vehicle_id için inverse fonksiyon
    @api.depends('picking_ids.vehicle_id')
    def _inverse_vehicle_id(self):
        for batch in self:
            batch.picking_ids.write({'vehicle_id': batch.vehicle_id})

    # transport_equipment_id için inverse fonksiyon
    @api.depends('picking_ids.transport_equipment_id')
    def _inverse_transport_equipment_id(self):
        for batch in self:
            batch.picking_ids.write({'transport_equipment_id': batch.transport_equipment_id})

    # rail_car_id için inverse fonksiyon
    @api.depends('picking_ids.rail_car_id')
    def _inverse_rail_car_id(self):
        for batch in self:
            batch.picking_ids.write({'rail_car_id': batch.rail_car_id})

    # vessel_name ve diğer maritimetransport alanları için inverse fonksiyonlar
    @api.depends('picking_ids.vessel_name', 'picking_ids.radio_call_sign_id', 
                 'picking_ids.ships_requirements', 'picking_ids.gross_tonnage_measure', 
                 'picking_ids.net_tonnage_measure', 'picking_ids.registry_cert_doc_ref', 
                 'picking_ids.registry_port_location')
    def _inverse_maritimetransport_fields(self):
        for batch in self:
            batch.picking_ids.write({
                'vessel_name': batch.vessel_name,
                'radio_call_sign_id': batch.radio_call_sign_id,
                'ships_requirements': batch.ships_requirements,
                'gross_tonnage_measure': batch.gross_tonnage_measure,
                'net_tonnage_measure': batch.net_tonnage_measure,
                'registry_cert_doc_ref': batch.registry_cert_doc_ref,
                'registry_port_location': batch.registry_port_location
            })

    @api.depends('picking_ids.project_transfer')
    def _compute_projects(self):
        for record in self:
            # Her bir picking kaydındaki project_transfer alanını topla
            projects = record.picking_ids.mapped('project_transfer')
            # Many2many alanına bu projelerin ID'lerini ata
            project_ids = projects.ids if projects else []
            record.project_ids = [(6, 0, project_ids)]

    def action_show_purchases(self):
        self.ensure_one()
        purchase_ids = []

        # Batch transferin adı ile eşleşen purchase'ları bul
        purchases = self.env['purchase.order'].search([('project_purchase', '=', self.name)])

        for purchase in purchases:
            purchase_ids.append(purchase.id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchases',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', purchase_ids)],
            'context': {'create': False},
        }

    def _compute_purchase_count(self):
        for batch in self:
            purchases = self.env['purchase.order'].search([
                ('project_purchase', '=', batch.name)
            ])
            batch.purchase_count = len(purchases)

    @api.depends('transportation_code')
    def _compute_airtag_url(self):
        base_url = "https://portal-test.yenaengineering.nl/transfers/"
        for record in self:
            if record.transportation_code:
                record.airtag_url = base_url + record.transportation_code
            else:
                record.airtag_url = False

    @api.onchange('edespatch_date', 'situation', 'arrival_date')
    def _onchange_transfer_related_fields(self):
        for batch in self:
            edespatch_dates = {'edespatch_date': batch.edespatch_date}
            arrival_dates = {'arrival_date': batch.arrival_date}
            situation = {'situation': batch.situation}
            for transfer in batch.picking_ids:
                transfer.write(edespatch_dates)
                transfer.write(situation)
                transfer.write(arrival_dates)

    @api.depends('picking_ids')
    def _compute_edespatch_delivery_type(self):
        for batch in self:
            # Eğer batch transferde edespatch_delivery_type ayarlanmışsa, ilgili transferlerde de güncelle
            edespatch_delivery_type = batch.edespatch_delivery_type
            if edespatch_delivery_type:
                batch.picking_ids.write({'edespatch_delivery_type': edespatch_delivery_type})
    def _inverse_edespatch_delivery_type(self):
        for batch in self:
            # Burada, batch üzerindeki edespatch_delivery_type değerini
            # ilişkili picking_ids kayıtlarına yazabilirsiniz.
            edespatch_delivery_type = batch.edespatch_delivery_type
            batch.picking_ids.write({'edespatch_delivery_type': edespatch_delivery_type})

    def _inverse_import_decleration_number(self):
        for batch in self:
            # Batch modelindeki import_decleration_number değeri değiştiğinde, bu değeri tüm ilişkili picking kayıtlarına yaz.
            if batch.import_decleration_number:
                batch.picking_ids.write({'import_decleration_number': batch.import_decleration_number})

    @api.depends('picking_ids.driver_ids')
    def _inverse_driver_ids(self):
        for batch in self:
            # Batch üzerindeki driver_ids değerlerini ilişkili picking_ids kayıtlarına yaz
            driver_ids = batch.driver_ids.ids
            batch.picking_ids.write({'driver_ids': [(6, 0, driver_ids)]})


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    project_ids = fields.Many2many('project.project', string='Projects', compute='_compute_project_transfer', store=True)

    @api.depends('picking_id.project_transfer')
    def _compute_project_transfer(self):
        for record in self:
            record.project_ids = record.picking_id.project_transfer

class Picking(models.Model):
    _inherit = 'stock.picking'
    edespatch_date = fields.Datetime(related='batch_id.edespatch_date', store=True, readonly=False)
    project_transfer = fields.Many2many("project.project", string="Project Number", store=True)
    effective_date = fields.Date(string="Effective Date", store=True)
    arrival_date = fields.Date(related="batch_id.arrival_date", string='Arrival Date' ,store=True, readonly=False)
