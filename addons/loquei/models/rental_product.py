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

class RentalOrder(models.Model):
    _name = 'rental.order'
    _description = 'Rental Order'

    customer_id = fields.Many2one('res.partner', string='Customer')
    rental_product_id = fields.Many2one('rental.product', string='Rental Product')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')
    status = fields.Selection([
        ('new', 'New'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='new', string='Status')

    @api.depends('rental_product_id', 'start_date', 'end_date')
    def _compute_total_price(self):
        for record in self:
            if record.start_date and record.end_date:
                duration = (record.end_date - record.start_date).days + 1
                if duration < 0:
                    record.total_price = 0
                else:
                    record.total_price = duration * record.rental_product_id.rental_price

    @api.constrains('start_date', 'end_date')
    def _check_rental_dates(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError("End date must be after the start date.")
            if record.start_date < fields.Date.today():
                raise ValidationError("Start date cannot be in the past.")



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    rental_start_date = fields.Date(string="Início da Locação")
    rental_end_date = fields.Date(string="Fim da Locação")
