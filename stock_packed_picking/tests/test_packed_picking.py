from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPackedPicking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_product = cls.env["product.product"]
        cls.location_1 = cls.env.ref("stock.warehouse0")
        cls.location_2 = cls.env.ref("stock.location_order")
        cls.product_1 = product_product.create(
            {"name": "Packed Thing 1", "type": "product"}
        )
        cls.product_2 = product_product.create(
            {"name": "Packed Thing 2", "type": "product"}
        )
        cls.product_3 = product_product.create(
            {"name": "Packed Thing 3", "type": "product"}
        )
        cls.operation_type = cls.env.ref("stock.picking_type_out")

    def test_packed_picking(self):
        # Test package creation without additional options
        # such as create_lots and set_ready.
        picking = (
            self.env["stock.pack.products"]
            .create(
                {
                    "operation_type_id": self.operation_type.id,
                    "package_name": "Test Package",
                    "location_id": self.location_1.id,
                    "location_dest_id": self.location_2.id,
                    "line_ids": [
                        (0, 0, {"product_id": self.product_1.id, "qty_done": 1}),
                        (0, 0, {"product_id": self.product_2.id, "qty_done": 2}),
                        (0, 0, {"product_id": self.product_3.id, "qty_done": 3}),
                    ],
                }
            )
            .action_pack()
        )
        # Nested move lines must have a value in the "result_package_id" field
        move_line_packages = picking.move_line_ids.mapped("result_package_id")
        self.assertTrue(
            all(move_line_packages),
            "Not all move lines have a value in the 'result_package_id' field.",
        )
        # The name of result package must be "Test Package"
        self.assertTrue(
            all(move_line_packages.mapped(lambda x: x.name == "Test Package")),
            "Not all move lines have the 'Test Package' name.",
        )

        # Test package creation with 'create_lots' option on.
        picking = (
            self.env["stock.pack.products"]
            .create(
                {
                    "operation_type_id": self.operation_type.id,
                    "location_id": self.location_1.id,
                    "location_dest_id": self.location_2.id,
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product_1.id,
                                "serial": "Test Serial 1",
                                "qty_done": 1,
                            },
                        ),
                        (0, 0, {"product_id": self.product_2.id, "qty_done": 2}),
                        (0, 0, {"product_id": self.product_3.id, "qty_done": 3}),
                    ],
                    "create_lots": True,
                }
            )
            .action_pack()
        )
        # Nested move lines must have a value in the "lot_id" field
        self.assertTrue(
            all(picking.move_line_ids.mapped("lot_id")),
            "Not all move lines have a value in the 'lot_id' field.",
        )
        # First move line must contain lot_name = "Test Serial 1"
        self.assertEqual(
            picking.move_line_ids[0].lot_id.name,
            "Test Serial 1",
            "First move line lot_name isn't equal to 'Test Serial 1'",
        )

        # Test package creation with 'set_ready' option on.
        picking = (
            self.env["stock.pack.products"]
            .create(
                {
                    "operation_type_id": self.operation_type.id,
                    "location_id": self.location_1.id,
                    "location_dest_id": self.location_2.id,
                    "line_ids": [
                        (0, 0, {"product_id": self.product_1.id, "qty_done": 1}),
                        (0, 0, {"product_id": self.product_2.id, "qty_done": 2}),
                        (0, 0, {"product_id": self.product_3.id, "qty_done": 3}),
                    ],
                    "set_ready": True,
                }
            )
            .action_pack()
        )
        # Picking state could be "assigned" (Ready) or "confirmed" (Waiting)
        # in this case
        self.assertTrue(
            picking.state in ("assigned", "confirmed"),
            "Picking state isn't 'Ready' or 'Waiting'",
        )
