from odoo import api, fields, models, _


class QuotationCancelReason(models.Model):
    _name = "purchase.cancel.reason"
    _description = "Purchase Cancel Reason"

    name = fields.Char(string='Cancel Reason',
                       help="For adding the reason for quotation cancellation.")
