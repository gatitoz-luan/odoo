# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"
    def create_replenish_in(self, order, replenish_date):
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        
        # Encontrar o picking type para reabastecimento (movimentos de entrada)
        picking_type_id = self.env.ref('stock.picking_type_in').id  # Exemplo: substitua 'stock.picking_type_in' pelo seu picking type específico
        
        picking = Picking.create({
            'location_id': order.warehouse_id.lot_stock_id.id,  # Assumindo que a origem é o estoque do armazém da ordem
            'location_dest_id': order.partner_id.property_stock_supplier.id,  # Destino é o estoque do fornecedor (ou ajuste conforme necessário)
            'picking_type_id': picking_type_id,
            'scheduled_date': replenish_date,
            'origin': order.name,
        })

        for line in order.order_line:
            # Apenas criar movimentos para produtos físicos que requerem reabastecimento
            if line.product_id.type == 'product':
                Move.create({
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'picking_id': picking.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'date_expected': replenish_date,
                })

        picking.action_confirm()  # Confirma automaticamente o picking, se desejado
        picking.action_assign()  # Verifica a disponibilidade dos produtos

    def _pre_action_done_hook(self):
        res = super()._pre_action_done_hook()
        # We use the 'skip_expired' context key to avoid to make the check when
        # user did already confirmed the wizard about expired lots.
        if res is True and not self.env.context.get('skip_expired'):
            pickings_to_warn_expired = self._check_expired_lots()
            if pickings_to_warn_expired:
                return pickings_to_warn_expired._action_generate_expired_wizard()
        return res

    def _check_expired_lots(self):
        expired_pickings = self.move_line_ids.filtered(lambda ml: ml.lot_id.product_expiry_alert).picking_id
        return expired_pickings

    def _action_generate_expired_wizard(self):
        expired_lot_ids = self.move_line_ids.filtered(lambda ml: ml.lot_id.product_expiry_alert).lot_id.ids
        view_id = self.env.ref('product_expiry.confirm_expiry_view').id
        context = dict(self.env.context)

        context.update({
            'default_picking_ids': [(6, 0, self.ids)],
            'default_lot_ids': [(6, 0, expired_lot_ids)],
        })
        return {
            'name': _('Confirmation'),
            'type': 'ir.actions.act_window',
            'res_model': 'expiry.picking.confirmation',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'context': context,
        }
