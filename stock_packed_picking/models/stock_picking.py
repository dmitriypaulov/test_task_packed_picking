from odoo import Command, api, models


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def _create_packed_picking(
        self,
        operation_type,
        stock_move_data,
        owner=None,
        location=None,
        location_dest_id=None,
        package_name=None,
        create_lots=False,
        set_ready=False,
    ):
        """
        Create a picking and put its product into a a package.

        This is equal to the following sequence:
        - Create a new picking
        - Assign an owner
        - Add products and set qty_done
        - Mark as "Todo"
        - Put in pack

        Args:
        operation_type (stock.picking.type): Operation type
        stock_move_data (List of tuples): [(product_id, qty_done, serial)]
        - (Integer) product_id: id of the product
        - (float) qty_done: quantity done
        - (Char, optional) serial: serial number to assign.
        Default lot names will be used if is None or == False
        Used only if 'create_lots==True'
        owner (res.partner, optional): Owner of the product
        location (stock.location, optional): Source location if differs from the
        operation type one
        location_dest (stock.location, optional): Destination location if differs
        from the operation type one
        package_name (Char, optional): Name to be assigned to the package. Default
        name will be used if not provided.
        set_ready (bool, optional): Try to set picking to the "Ready" state.

        Returns:
            stock.picking: Created picking
        """
        picking_vals = {
            "picking_type_id": operation_type.id,
            "owner_id": owner.id if owner else False,
        }
        if location:
            picking_vals["location_id"] = location.id
        if location_dest_id:
            picking_vals["location_dest_id"] = location_dest_id.id
        picking = self.env["stock.picking"].create(picking_vals)
        picking.write(
            {
                "move_ids": [
                    Command.create(
                        {
                            "product_id": move[0],
                            "location_id": picking.location_id.id,
                            "location_dest_id": picking.location_dest_id.id,
                            "name": self.env["product.product"].browse(move[0]).name,
                            "move_line_ids": [
                                Command.create(
                                    {
                                        "picking_id": picking.id,
                                        "product_id": move[0],
                                        "qty_done": move[1],
                                    }
                                )
                            ],
                        }
                    )
                    for move in stock_move_data
                ]
            }
        )

        if create_lots:
            lot_vals = []
            for move_line, move_vals in zip(
                picking.move_line_ids, stock_move_data, strict=False
            ):
                vals = {
                    "product_id": move_line.product_id.id,
                    "company_id": move_line.company_id.id,
                }
                serial = move_vals[2] if len(move_vals) > 2 else False
                if serial:
                    vals["name"] = serial
                lot_vals.append(vals)
            lots = self.env["stock.lot"].create(lot_vals)
            for move_line, lot in zip(picking.move_line_ids, lots, strict=False):
                move_line.lot_id = lot

        if set_ready:
            picking.action_confirm()
        package = picking.action_put_in_pack()
        if package_name:
            package.name = package_name
        return picking
