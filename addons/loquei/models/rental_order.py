# rental_order.py

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class RentalOrder(models.Model):
    _name = 'rental.order'
    _description = 'Rental Order'

    customer_id = fields.Many2one('res.partner', string='Customer')
    rental_product_id = fields.Many2one('product.product', string='Rental Product')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    total_price = fields.Float(compute='_compute_total_price', string='Total Price')

    # Campos adicionais para exibição
    start_date_display = fields.Char(string='Start Date (dd/mm/yyyy)', compute='_compute_date_display')
    end_date_display = fields.Char(string='End Date (dd/mm/yyyy)', compute='_compute_date_display')

    @api.depends('start_date', 'end_date')
    def _compute_date_display(self):
        for record in self:
            record.start_date_display = datetime.strftime(
                fields.Datetime.from_string(record.start_date),
                '%d/%m/%Y') if record.start_date else ''

            record.end_date_display = datetime.strftime(
                fields.Datetime.from_string(record.end_date),
                '%d/%m/%Y') if record.end_date else ''

    @api.depends('rental_product_id', 'start_date', 'end_date')
    def _compute_total_price(self):
        for record in self:
            if record.start_date and record.end_date:
                duration = (record.end_date - record.start_date).days + 1
                record.total_price = duration * record.rental_product_id.rental_price

    @api.constrains('start_date', 'end_date')
    def _check_rental_dates(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError("End date must be after the start date.")
            if record.start_date < fields.Date.today():
                raise ValidationError("Start date cannot be in the past.")

    # Implementação da lógica de verificação de disponibilidade
    def check_product_availability(self, product, start_date, end_date, quantity):
        RentalOrder = self.env['rental.order']
        ProductTemplate = self.env['product.template']

        # Obtém o tempo de limpeza do produto
        cleaning_time = ProductTemplate.browse(product.id).cleaning_time or 0

        # Data de início considerando o tempo de limpeza
        start_date_with_cleaning = fields.Date.to_string(fields.Date.from_string(start_date) - timedelta(days=cleaning_time))

        # Verifica se há alguma locação que se sobreponha ao período desejado
        overlapping_orders = RentalOrder.search([
            ('rental_product_id.product_id', '=', product.id),
            ('start_date', '<=', end_date),
            ('end_date', '>=', start_date_with_cleaning)
        ])

        # Calcula a quantidade total locada durante o período especificado
        total_quantity_reserved = sum(order.rental_product_id.quantity for order in overlapping_orders)

        # Verifica se a quantidade disponível é suficiente
        return product.quantity_available >= (quantity + total_quantity_reserved)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    rental_price = fields.Float(string='Preço de Locação Diário')
