from odoo import fields, models


class PackProductsLine(models.TransientModel):
    _name = "stock.pack.products.line"
    _description = "Pack Products Line"

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
    )
    qty_done = fields.Float(
        string="Quantity Done",
        required=True,
    )
    serial = fields.Char()
    pack_products_id = fields.Many2one(
        comodel_name="stock.pack.products",
    )
