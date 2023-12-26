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
    ):
        """
        Prepare values for stock.picking record.
        Is a part of packed picking creation functionality.
        See also '_create_packed_picking' method.

        Args:
        stock_move_data (List of tuples): [(product_id, qty_done, serial)]
        - (Integer) product_id: id of the product
        - (float) qty_done: quantity done
        - (Char, optional) serial: serial number to assign
        operation_type (stock.picking.type): Operation type
        owner (res.partner, optional): Owner of the product
        location (stock.location, optional): Source location if differs from the
        operation type one
        location_dest (stock.location, optional): Destination location if differs
        from the operation type one

        Returns:
        dict: Prepared stock.picking values
        """
        location = location or operation_type.default_location_src_id
        location_dest_id = location_dest_id or operation_type.default_location_dest_id
        vals = {
            "picking_type_id": operation_type.id,
            "owner_id": owner.id if owner else False,
            "move_line_ids": [
                Command.create(
                    self._prepare_stock_move_line_vals(
                        product_id=move_vals[0],
                        qty_done=move_vals[1],
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
    def _prepare_stock_move_line_vals(
        self,
        product_id,
        qty_done,
    ):
        """
        Prepare values for stock.move.line record.
        Is a part of packed picking creation functionality.
        See also '_create_packed_picking' method.

        Args:
        product_id (Integer): ID of product.product record.
        qty_done (Float): Quantity done.

        Returns:
        dict: Prepared stock.move.line values
        """
        return {
            "product_id": product_id,
            "qty_done": qty_done,
        }

    @api.model
    def _prepare_stock_lot_vals(
        self,
        move_line,
        serial=None,
    ):
        """
        Prepare values for stock.lot record.
        Is a part of packed picking creation functionality.
        See also '_create_packed_picking' method.

        Args:
        move_line (Record: stock.move.line): Move line record
        serial (Char, optional): Serial number to assign.
        If empty, system will generate serial number automatically.

        Returns:
        dict: Prepared stock.lot values
        """
        vals = {
            "product_id": move_line.product_id.id,
            "company_id": move_line.company_id.id,
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
            )
        )

        if create_lots:
            lots = self.env["stock.lot"].create(
                [
                    self._prepare_stock_lot_vals(
                        move_line=m_line, serial=vals[2] if len(vals) > 2 else False
                    )
                    for m_line, vals in zip(
                        picking.move_line_ids, stock_move_data, strict=False
                    )
                ]
            )
            for m_line, lot in zip(picking.move_line_ids, lots, strict=False):
                m_line.lot_id = lot

        if set_ready:
            picking.action_confirm()

        package = picking.action_put_in_pack()

        if package_name:
            package.name = package_name

        return picking
