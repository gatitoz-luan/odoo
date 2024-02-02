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
    
    def _action_done(self):
        res = super(StockMove, self)._action_done()
        for move in self:
            if move.picking_id.picking_type_id.code == 'incoming':
                # Criar a movimentação de saída correspondente
                self.env['stock.move'].create({
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'product_uom_qty': move.product_uom_qty,
                    'product_uom': move.product_uom.id,
                    'location_id': move.location_dest_id.id,
                    'location_dest_id': move.location_id.id,
                    'picking_type_id': self.env.ref('stock.picking_type_out').id, # Ajuste conforme necessário
                    'origin': move.origin,
                    'state': 'confirmed', # ou 'draft', conforme preferir
                })
        return res