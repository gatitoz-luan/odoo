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

 

    @api.depends('start_date', 'end_date')
    def _compute_date_display(self):
        for record in self:
            record.start_date_display = datetime.strftime(
                fields.Datetime.from_string(record.start_date),
                '%d/%m/%Y') if record.start_date else ''

            record.end_date_display = datetime.strftime(
                fields.Datetime.from_string(record.end_date),
                '%d/%m/%Y') if record.end_date else ''


    @api.constrains('start_date', 'end_date')
    def _check_rental_dates(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError("End date must be after the start date.")
            if record.start_date < fields.Date.today():
                raise ValidationError("Start date cannot be in the past.")

    # Implementação da lógica de verificação de disponibilidade
    @api.constrains('order_line')
    def _check_product_availability(self):
        for order in self:
            for line in order.order_line:
                if line.product_id.type == 'product':  # Apenas para produtos físicos
                    # Considerar a data orçada (início e fim da locação + tempo de limpeza)
                    start_date = line.start_date
                    end_date = line.end_date
                    cleaning_time = line.product_id.product_tmpl_id.cleaning_time or 0
                    start_date_with_cleaning = start_date - timedelta(days=cleaning_time)

                    # Verificar disponibilidade do estoque
                    available_qty = self.env['stock.quant']._get_available_quantity(
                        line.product_id, line.order_id.warehouse_id.lot_stock_id, 
                        from_date=start_date_with_cleaning, to_date=end_date
                    )

                    if line.product_uom_qty > available_qty:
                        raise UserError(_('Não há estoque suficiente para o produto "%s" na data orçada.') % (line.product_id.name))
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    rental_order_id = fields.Many2one('rental.order', string='Rental Order')

    start_date = fields.Date(related='rental_order_id.start_date', string='Start Date', store=True, readonly=False)
    end_date = fields.Date(related='rental_order_id.end_date', string='End Date', store=True, readonly=False)
    cleaning_time = fields.Integer(string="Cleaning Time (days)")

    rental_price = fields.Float(string='Preço de Locação Diário')

    @api.onchange('product_id')
    def _onchange_product_id_update_rental_price(self):
        if self.product_id:
            self.rental_price = self.product_id.lst_price

    @api.onchange('rental_price')
    def _onchange_rental_price_update_unit_price(self):
        if self.rental_price:
            self.product_id.lst_price = self.rental_price
    @api.depends('start_date', 'end_date', 'product_id')
    def _compute_availability(self):
        for line in self:
            if line.product_id and line.start_date and line.end_date:
                # Calcular a disponibilidade e previsão de estoque considerando as datas orçadas
                cleaning_time = line.product_id.product_tmpl_id.cleaning_time or 0
                start_date_with_cleaning = line.start_date - timedelta(days=cleaning_time)
                
                line.availability = self.env['stock.quant']._get_available_quantity(
                    line.product_id, line.order_id.warehouse_id.lot_stock_id, 
                    from_date=start_date_with_cleaning, to_date=line.end_date
                )

                line.forecasted_stock = self.env['stock.quant']._get_forecasted_quantity(
                    line.product_id, line.order_id.warehouse_id.lot_stock_id, 
                    from_date=start_date_with_cleaning, to_date=line.end_date
                )
    @api.depends('    end_date = fields.Date(related='rental_order_id.end_date', string='End Date', store=True, readonly=False)
', 'product_id.cleaning_time')
    def _compute_rental_return_date(self):
        for record in self:
            if record.rental_finish_date and record.product_id.cleaning_time:
                # Calcula a data de retorno considerando o tempo de limpeza
                record.rental_return_date = record.rental_finish_date + timedelta(days=record.product_id.cleaning_time)
            else:
                record.rental_return_date = False

    # Campo calculado para a data de retorno
    rental_return_date = fields.Date(string="Rental Return Date", compute="_compute_rental_return_date", store=True)

    # Campos adicionais
    availability = fields.Float(compute='_compute_availability', string='Disponibilidade')
    forecasted_stock = fields.Float(compute='_compute_availability', string='Estoque Previsto')
