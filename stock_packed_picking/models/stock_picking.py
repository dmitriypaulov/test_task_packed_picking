from odoo import Command, api, models


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def _prepare_stock_picking_vals(
        self,
        stock_move_data,
        operation_type,
        owner=None,
        location=None,
        location_dest_id=None,
        create_lots=False,
    ):
        vals = {
            "picking_type_id": operation_type.id,
            "owner_id": owner.id if owner else False,
            "move_ids": [
                Command.create(
                    self._prepare_stock_move_vals(
                        product_id=move_vals[0],
                        qty_done=move_vals[1],
                        serial=move_vals[2] if len(move_vals) > 2 else None,
                        location=location,
                        location_dest_id=location_dest_id,
                        create_lots=create_lots,
                    )
                )
                for move_vals in stock_move_data
            ],
        }
        if location:
            vals["location_id"] = location.id
        if location_dest_id:
            vals["location_dest_id"] = location_dest_id.id
        return vals

    @api.model
    def _prepare_stock_move_vals(
        self,
        product_id,
        qty_done,
        serial=None,
        location=None,
        location_dest_id=None,
        create_lots=False,
    ):
        vals = {
            "product_id": product_id,
            "name": self.env["product.product"].browse(product_id).name,
            "move_line_ids": [
                Command.create(
                    {
                        "product_id": product_id,
                        "qty_done": qty_done,
                        "lot_id": Command.create(
                            self._prepare_stock_lot_vals(
                                product_id=product_id,
                                serial=serial,
                            )
                        )
                        if create_lots
                        else False,
                    }
                )
            ],
        }
        if location:
            vals["location_id"] = location.id
        if location_dest_id:
            vals["location_dest_id"] = location_dest_id.id
        return vals

    @api.model
    def _prepare_stock_lot_vals(
        self,
        product_id,
        serial=None,
    ):
        vals = {
            "product_id": product_id,
        }
        if serial:
            vals["name"] = serial
        return vals

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
        picking = self.env["stock.picking"].create(
            self._prepare_stock_picking_vals(
                stock_move_data=stock_move_data,
                operation_type=operation_type,
                owner=owner,
                location=location,
                location_dest_id=location_dest_id,
                create_lots=create_lots,
            )
        )

        if set_ready:
            picking.action_confirm()

        package = picking.action_put_in_pack()

        if package_name:
            package.name = package_name

        return picking
