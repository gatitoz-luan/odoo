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
        res = super(StockMoveCustom, self)._action_done()
        for move in self.filtered(lambda m: m.picking_id.picking_type_id.code == 'incoming' and m.product_id.type == 'product'):
            # Garante que apenas produtos armazenáveis gerem movimentações de saída
            out_picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
            self.env['stock.move'].create({
                'name': move.name,
                'product_id': move.product_id.id,
                'product_uom_qty': move.product_uom_qty,
                'product_uom': move.product_uom.id,
                'location_id': move.location_dest_id.id,
                'location_dest_id': move.product_id.property_stock_inventory.id,  # Exemplo de destino
                'picking_type_id': out_picking_type.id,
                'origin': move.origin,
                'state': 'confirmed',
            })
        return res

class StockPickingCustom(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):


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
