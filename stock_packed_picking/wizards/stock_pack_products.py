from odoo import fields, models


class PackProducts(models.TransientModel):
    _name = "stock.pack.products"
    _description = "Pack Products"

    package_name = fields.Char()
    operation_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        required=True,
    )
    owner_id = fields.Many2one(
        comodel_name="res.partner",
    )
    location_id = fields.Many2one(
        "stock.location",
    )
    location_dest_id = fields.Many2one(
        "stock.location",
        string="Location Destination",
    )
    create_lots = fields.Boolean(
        help="If checked, system will create lots for the products automatically.",
    )
    set_ready = fields.Boolean(
        help="If checked, system will try to set picking to the 'Ready' state.",
    )
    line_ids = fields.One2many(
        comodel_name="stock.pack.products.line",
        inverse_name="pack_products_id",
        required=True,
    )

    def action_pack(self):
        """
        Create a packed picking with the given products.
        This method is a wrapper for '_create_packed_picking' method
        of stock.picking model.

        See its docstring for more details:
        stock_packed_picking/models/stock_picking.py

        Returns:
            if context key 'go_to_picking' is True
                dict: Window action with created picking as a target
            if context key 'go_to_picking' is False
                stock.picking: Created packed picking
        """
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
