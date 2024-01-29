from odoo import models, fields, api
from datetime import timedelta

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Campos de data de início e fim da locação
    rental_start_date = fields.Date(string="Rental Start Date")
    rental_finish_date = fields.Date(string="Rental Finish Date")

    @api.depends('rental_finish_date', 'product_id.cleaning_time')
    def _compute_rental_return_date(self):
        for record in self:
            if record.rental_finish_date and record.product_id.cleaning_time:
                # Calcula a data de retorno considerando o tempo de limpeza
                record.rental_return_date = record.rental_finish_date + timedelta(days=record.product_id.cleaning_time)
            else:
                record.rental_return_date = False

    # Campo calculado para a data de retorno
    rental_return_date = fields.Date(string="Rental Return Date", compute="_compute_rental_return_date", store=True)
