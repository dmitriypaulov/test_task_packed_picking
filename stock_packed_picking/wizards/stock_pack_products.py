from odoo import _, fields, models


class PackProducts(models.TransientModel):
    _name = "stock.pack.products"
    _description = "Pack Products"

    package_name = fields.Char(string="Package Name")
    operation_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Operation Type",
        required=True,
    )
    owner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Owner",
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Location",
    )
    location_dest_id = fields.Many2one(
        comodel_name="stock.location",
        string="Location Destination"
    )
    create_lots = fields.Boolean(
        string="Create Lots",
        help=_(
            "If checked, system will create lots "
            "for the products automatically."
        )
    )
    set_ready = fields.Boolean(
        string="Set Ready",
        help=_(
            "If checked, system will try to "
            "set picking to the 'Ready' state."
        )
    )
    line_ids = fields.One2many(
        comodel_name="stock.pack.products.line",
        inverse_name="pack_products_id",
        string="Lines",
        required=True,
    )

    def action_pack(self):
        self.ensure_one()
        picking = self.env["stock.picking"]._create_packed_picking(
            operation_type=self.operation_type_id,
            stock_move_data=[
                (line.product_id.id, line.qty_done, line.serial)
                for line in self.line_ids
            ],
            owner=self.owner_id,
            location=self.location_id,
            location_dest_id=self.location_dest_id,
            package_name=self.package_name,
            create_lots=self.create_lots,
            set_ready=self.set_ready,
        )
        if self.env.context.get("go_to_picking", False):
            return {
                "type": "ir.actions.act_window",
                "name": "Packed Picking",
                "res_model": "stock.picking",
                "res_id": picking.id,
                "view_mode": "form",
            }
        return picking
