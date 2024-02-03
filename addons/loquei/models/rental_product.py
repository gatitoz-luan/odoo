from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RentalProduct(models.Model):
    _name = 'rental.product'
    _description = 'Product for Rent'

    product_id = fields.Many2one('product.template', string='Product')
    rental_price = fields.Float(string='Rental Price per Day')

    @api.constrains('rental_price')
    def _check_rental_price(self):
        for record in self:
            if record.rental_price < 0:
                raise ValidationError("The rental price cannot be negative.")
        

