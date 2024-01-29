from odoo import models, fields, api
from datetime import datetime

class StockMove(models.Model):
    _inherit = 'stock.move'

    def action_assign(self):
        for move in self:
            sale_line = move.sale_line_id
            if sale_line and sale_line.rental_start_date:
                # Verifica se a data atual é anterior à data de início da locação
                if datetime.now().date() < fields.Date.from_string(sale_line.rental_start_date):
                    continue  # Não reserva o estoque se ainda não atingiu a data de início
            super(StockMove, move).action_assign()
