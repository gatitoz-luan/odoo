from odoo import models, fields, api


class RentalProduct(models.Model):
    _name = 'rental.product'
    _description = 'Product for Rent'

    product_id = fields.Many2one('product.template', string='Product')
    rental_price = fields.Float(string='Rental Price per Day')

class RentalOrder(models.Model):
    _name = 'rental.order'
    _description = 'Rental Order'

    customer_id = fields.Many2one('res.partner', string='Customer')
    rental_product_id = fields.Many2one('rental.product', string='Rental Product')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')

    @api.depends('rental_product_id', 'start_date', 'end_date')
    def _compute_total_price(self):
        for record in self:
            if record.start_date and record.end_date:
                duration = (record.end_date - record.start_date).days + 1
                record.total_price = duration * record.rental_product_id.rental_price
