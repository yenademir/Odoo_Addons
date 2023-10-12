import requests
import json
from datetime import datetime, timedelta
import pytz
from odoo import api, models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    app_status = fields.Selection([('control', 'Control'), ('done', 'Done')], string="App Status")

    def action_control(self):
        self.app_status = 'control'

        # Send the data to the endpoint
        url = "https://portal-test.yenaengineering.nl/api/InitiateByProcess"
        headers = {
            "Content-Type": "application/json"
        }
        product_data = [{"id": line.product_id.id, "name": line.product_id.name} for line in self.order_line]

        # Get current time in UTC+3
        now_utc = datetime.now(pytz.timezone('UTC'))
        now_utc_plus_3 = now_utc + timedelta(hours=3)
        timestamp_utc_plus_3 = now_utc_plus_3.isoformat()

        data = {
            "order_id": self.id,
            "order_number": self.name,
            "project_number": self.x_project_purchase.name,
            "vendor_name": self.partner_id.name,
            "vendor_id": self.partner_id.id,
            "customer_name": self.order_line.product_id.x_customer.name,
            "customer_id": self.order_line.product_id.x_customer.id,
            "creator_name": self.user_id.name,
            "work_type": "Order",
            "state": "Order",
            "status": self.state,
            "creation_date": timestamp_utc_plus_3,
            "ControlForms": product_data
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))
        return True


