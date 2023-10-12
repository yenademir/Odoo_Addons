from odoo import api, models
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def action_send_data_to_web(self):

        url = "https://portal-test.yenaengineering.nl/api/inspectionplans"
        headers = {
            "Content-Type": "application/json"
        }

        data = []

        active_ids = self.env.context.get('active_ids', [])
        selected_records = self.browse(active_ids)

        for record in selected_records:

            data.append({
                'vendor_odooid': record.partner_id.id,
                'vendor_name': record.partner_id.name,
                'customer_odooid': record.product_id.x_studio_customer.id,
                'customer_name': record.product_id.x_studio_customer.name,
                'project_number': record.account_analytic_id.name,
                'product_odooid': record.product_id.id,
                'product_name': record.product_id.name,
                'order_id': record.order_id.id,
                'order_number': record.order_id.name,
                'quantity': record.product_qty,
                'delivery_date': record.x_required_delivery_date.isoformat(),
                'status': "Draft",
                'state': "Open"
            })

        #_logger.info("Data: %s", json.dumps(data))
        response = requests.post(url, headers=headers, data=json.dumps(data))

        #_logger.info("Status Code: %s", response.status_code)
        #_logger.info("Response: %s", response.text)

        #if response.status_code != 201:
        #    _logger.warning("There was an issue with the POST request!")
