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
    


class StockPickingCustom(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(StockPickingCustom, self).button_validate()
        for picking in self:
            if picking.picking_type_id.code == 'incoming':
                # Cria um novo picking de saída
                picking_type_out = self.env.ref('stock.picking_type_out')
                location_dest = picking.location_dest_id
                location_src = picking.picking_type_id.default_location_src_id
                picking_out = self.env['stock.picking'].create({
                    'picking_type_id': picking_type_out.id,
                    'location_id': location_dest.id,
                    'location_dest_id': location_src.id,
                    'origin': picking.name,
                })

                # Cria movimentações de estoque para o novo picking
                for move in picking.move_lines:
                    self.env['stock.move'].create({
                        'name': move.name,
                        'product_id': move.product_id.id,
                        'product_uom_qty': move.product_uom_qty,
                        'product_uom': move.product_uom.id,
                        'location_id': location_dest.id,
                        'location_dest_id': location_src.id,
                        'picking_id': picking_out.id,
                        'picking_type_id': picking_type_out.id,
                        'origin': picking.name,
                    })

                # Confirma o picking de saída se desejado
                # picking_out.action_confirm()
                # picking_out.action_assign()
                # Opcionalmente, pode-se validar o picking de saída automaticamente
                # picking_out.button_validate()
        return res
    @api.model
    def create_stock_out_moves(self, stock_in_move):
        product = stock_in_move.product_id
        # Verifica se o produto é estocável
        if product.type != 'product':
            return
        # Resto da lógica para criar movimento de saída...

    @api.model
    def check_custom_routes_and_create_stock_out(self, stock_in_move):
        # Exemplo de verificação de rota (pseudocódigo)
        if self._should_create_out_move_based_on_routes(stock_in_move):
            self.create_stock_out_moves(stock_in_move)
