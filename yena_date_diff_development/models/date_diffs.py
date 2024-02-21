from odoo import api,models,fields
from datetime import datetime

class SaleOrder(models.Model):
    _inherit="sale.order"
    
    delivery_date_diff = fields.Float(string='YENA Delivery Performance', readonly=True, store="True", compute="_compute_delivery_date_diff")

    @api.depends('commitment_date', 'picking_ids.arrival_date')
    def _compute_delivery_date_diff(self):
        for order in self:
            order.delivery_date_diff = False
            if order.commitment_date:
                commitment_datetime = fields.Datetime.from_string(order.commitment_date)
                commitment_timestamp = datetime.timestamp(commitment_datetime)

                # Kökeni bu sipariş olan ve durumu 'done' olan picking kayıtlarını filtrele
                picking_records = self.env['stock.picking'].search([('origin', '=', order.name), ('state', '=', 'done')])
                
                # Filtrelenmiş picking kayıtlarından varış tarihlerini al
                arrival_dates = picking_records.mapped('arrival_date')
                filtered_datetimes = [fields.Datetime.from_string(arrival) for arrival in arrival_dates if arrival]
                
                if filtered_datetimes:
                    latest_arrival_date = max(filtered_datetimes)
                    latest_arrival_timestamp = datetime.timestamp(latest_arrival_date)
                    
                    diff_seconds = latest_arrival_timestamp - commitment_timestamp
                    diff_days = diff_seconds / (24 * 3600)

                    order.delivery_date_diff = diff_days
                
    

class PurchaseOrder(models.Model):
    _inherit="purchase.order"
    
    delivery_date_diff = fields.Float(string='Delivery Performance', readonly=True, store="True", compute="_compute_delivery_date_diff")
    
    @api.depends('delivery_date', 'picking_ids.edespatch_date')
    def _compute_delivery_date_diff(self):
        for order in self:
            # Varsayılan değeri False olarak ayarla
            order.delivery_date_diff = False
            if order.delivery_date:
                delivery_datetime = datetime.combine(fields.Date.from_string(order.delivery_date), datetime.min.time())
                delivery_timestamp = datetime.timestamp(delivery_datetime)

                picking_records = self.env['stock.picking'].search([('origin', '=', order.name), ('state', '=', 'done')])
                edespatch_datetimes = [fields.Datetime.from_string(record.edespatch_date) for record in picking_records if record.edespatch_date]

                if edespatch_datetimes:
                    latest_edespatch_datetime = max(edespatch_datetimes)
                    latest_effective_timestamp = datetime.timestamp(latest_edespatch_datetime)

                    diff_seconds = latest_effective_timestamp - delivery_timestamp
                    diff_days = diff_seconds / (24 * 3600)

                    order.delivery_date_diff = diff_days
                    

class BatchTransfer(models.Model):
    _inherit = 'stock.picking.batch'
    transit_time = fields.Float(string='Transit Time', readonly=True, store="True", compute="_compute_transit_time")

    @api.depends('picking_ids.arrival_date', 'picking_ids.edespatch_date')
    def _compute_transit_time(self):
        for batch in self:
            batch.transit_time = False  # Varsayılan değer
            # İlgili stock.picking kayıtlarını bul
            picking_records = batch.mapped('picking_ids').filtered(lambda p: p.origin)
            if picking_records:
                transit_times = []
                for record in picking_records:
                    if record.arrival_date and record.edespatch_date:
                        arrival_datetime = fields.Datetime.from_string(record.arrival_date)
                        edespatch_datetime = fields.Datetime.from_string(record.edespatch_date)
                        transit_seconds = (arrival_datetime - edespatch_datetime).total_seconds()
                        transit_days = transit_seconds / (24 * 3600)
                        transit_times.append(transit_days)

                if transit_times:
                    batch.transit_time = max(transit_times)
