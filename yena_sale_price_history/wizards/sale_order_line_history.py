from odoo import api, fields, models

class SaleOrderLinePriceHistory(models.TransientModel):
    _name = "sale.order.line.price.history"
    _description = "Sale order line price history"

    @api.model
    def _default_partner_id(self):
        line_id = self.env.context.get("active_id")
        line = self.env["sale.order.line"].browse(line_id)
        return line.order_partner_id.id if line else False
    
    sale_order_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Sale order line",
        default=lambda self: self.env.context.get("active_id"),
    )
    product_id = fields.Many2one(related="sale_order_line_id.product_id")
    partner_id = fields.Many2one(
            comodel_name="res.partner",
            string="Customer",
            default=_default_partner_id,
        )
    line_ids = fields.One2many(
        comodel_name="sale.order.line.price.history.line",
        inverse_name="history_id",
        string="History lines",
        
        readonly=True,
    )
    include_quotations = fields.Boolean(
        help="Include quotations lines in the sale history", default=True,string="Include Quatations"
    )
    include_losts = fields.Boolean(
        help="Include lost quatation lines in the sale history", default=True, string="Include Losts"
    )
    include_commercial_partner = fields.Boolean(
        string="Include commercial entity",
        default=True,
        help="Include commercial entity and its contacts in the sale history",
    )

    @api.onchange("partner_id", "include_quotations", "include_commercial_partner", "include_losts")
    def _onchange_partner_id(self):
        self.line_ids = False
        states = ["sale", "done"]
        if self.include_quotations:
            states += ["draft", "sent"]
        if self.include_losts:
            states += ["cancel"]

        domain = [
            ("product_id", "=", self.product_id.id),
            ("state", "in", states),
        ]
        if self.partner_id:
            if self.include_commercial_partner:
                domain += [
                    (
                        "order_partner_id",
                        "child_of",
                        self.partner_id.commercial_partner_id.ids,
                    )
                ]
            else:
                domain += [("order_partner_id", "child_of", self.partner_id.ids)]
        vals = []
        order_lines = self.env["sale.order.line"].search(domain)
        for order_line in order_lines:
            vals.append( 
                (0,False,
                    {
                        "sale_order_line_id": order_line.id,
                        "history_sale_order_line_id": self.sale_order_line_id.id,
                    },
                ) 
            )
        
        self.line_ids = vals

class SaleOrderLinePriceHistoryLine(models.TransientModel):
    _name = "sale.order.line.price.history.line"
    _description = "Sale order line price history line"

    state=fields.Selection(string="Status", readonly=True , related="order_id.state")

    blanket_order_line = fields.Many2one(
        comodel_name="sale.blanket.order.line",
        related="sale_order_line_id.blanket_order_line",
        string="Blanket Order Line",
        readonly=True,
    )
    history_id = fields.Many2one(
        comodel_name="sale.order.line.price.history",
        string="History",
    )
    history_sale_order_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="history sale order line",
    )
    sale_order_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Sale order line",
    )
    order_id = fields.Many2one(related="sale_order_line_id.order_id")
    partner_id = fields.Many2one(related="sale_order_line_id.order_partner_id")
    sale_order_date_order = fields.Datetime(
        related="sale_order_line_id.order_id.date_order",
    )
    product_qty = fields.Float(related="sale_order_line_id.product_qty")
    product_uom = fields.Many2one(related="sale_order_line_id.product_uom")
    price_unit = fields.Float(related="sale_order_line_id.price_unit")
    def _prepare_sale_order_line_vals(self):
        self.ensure_one()
        return {"price_unit": self.price_unit}

    def action_set_price(self):
        self.ensure_one()
        active_id = self.env.context.get("active_id")
        order_line = self.env["sale.order.line"].browse(active_id)
        vals = self._prepare_sale_order_line_vals()
        order_line.write(vals)