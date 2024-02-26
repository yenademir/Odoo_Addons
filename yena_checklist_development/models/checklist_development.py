from odoo import api, fields, models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
        
    project_docs = fields.Boolean(string="Are the required certifications and documents requested by the project available?")
    is_supllied = fields.Boolean(string="Can this supplier supply this raw material? Is it suitable for basic processing?")
    drawing_activities = fields.Boolean(string="Are there any design activities to be carried out within the scope of the project? If so, please specify the deadline?")
    equipments_capability = fields.Boolean(string="Are the supplier's machinery and equipment sufficient for the project?")
    external_outsource = fields.Boolean(string="Will the supplier use external resources? If yes, for which operations?")
    measurement_equipment_supplier = fields.Boolean(string="Are the supplier's measurement equipment sufficient?")
    measurement_equipment_yena = fields.Boolean(string="Are Yena KK team's measurement instruments sufficient?", help="(dwg or step may be requested if required)")
    mold_or_fixture = fields.Boolean(string="Will a mold or fixture be made?")
    before_project = fields.Boolean(string="Is there a need for training for any operational steps by YENA or the supplier before the project?")
    transfer_condition = fields.Boolean(string="Has it been confirmed with the customer for shipment conditions and packaging methods?")
    wpqr_approval = fields.Boolean(string="Is the WPQR (Welding Procedure Qualification Record) sufficient?")
    welder_cert = fields.Boolean(string="Is the scope of the welder's certification sufficient and are the durations valid until the end of the project?")
    test_info = fields.Boolean(string="Are destructive or non-destructive tests required within the scope of the project?")
    ndt_information = fields.Boolean(string="Will external NDT (Non-Destructive Testing) service be required?")
    supplier_checklist = fields.Boolean(string="Are qualified personnel available for the activities to be carried out? Is it necessary? (supplier)")
    yena_checklist = fields.Boolean(string="Are qualified personnel available for the activities to be carried out? Is it necessary? (YENA)")
    hole_information = fields.Boolean(string="If there is a coating process, are the hole diameters, locations, and numbers sufficient?")
    is_info_shared = fields.Boolean(string="Has it been shared with the supplier that sharp edges, laser cutting traces, and welding burrs should be removed before painting or coating; the material surface should not be oily, dirty, or rusty?")
    is_revision_actual = fields.Boolean(string="Are the revisions up to date?")
    potential_nonconformity = fields.Boolean(string="Are there any potential non-conformities? If yes, what are they and how can they be prevented?")
    kickoff_meeting = fields.Boolean(string="Has a Kick-Off Meeting with the customer been held?")


class SaleOrder(models.Model):
    _inherit = "sale.order"
    

    communicated_details_with_customer = fields.Boolean(string="Were details communicated with the customer?")
    customer_notes_entered = fields.Boolean(string="Have customer notes been entered as Log Notes?")
    order_quantities_requested = fields.Boolean(string="Were order quantities, target prices, photos of the product in use or in its finished state, and packaging photos requested/received?")
    material_list_issued = fields.Boolean(string="Has the Material List been issued/created?")
    surface_treatment_specified = fields.Boolean(string="Is the surface treatment specified?")
    weights_clear = fields.Boolean(string="Are the weights clear?")
    manufacturing_processes_clear = fields.Boolean(string="Are the manufacturing processes clear?")
    drawings_sufficient = fields.Boolean(string="Are the drawings sufficient?")
    materials_measurement_info_sufficient = fields.Boolean(string="Are materials, measurement information, welding information, and tolerances in the drawings of all parts sufficient?")
    raw_materials_supplied = fields.Boolean(string="Can raw materials be supplied? Are they suitable for processing in basic processes?")
    surface_treatment_info_clear = fields.Boolean(string="Is surface treatment information clear?")
    dies_or_fixtures_made = fields.Boolean(string="Will dies or fixtures be made?")
    kickoff_meeting_made = fields.Boolean(string="Has a Kick-Off Meeting with the customer been made?")
