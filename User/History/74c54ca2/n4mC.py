# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.osv import expression


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    def _get_default_weight_uom(self):
        return self.env['product.template']._get_weight_uom_name_from_ir_config_parameter()

    batch_group_by_carrier = fields.Boolean('Carrier', help="Automatically group batches by carriers")
    batch_max_weight = fields.Integer("Maximum weight per batch",
                                      help="A transfer will not be automatically added to batches that will exceed this weight if the transfer is added to it.\n"
                                           "Leave this value as '0' if no weight limit.")
    weight_uom_name = fields.Char(string='Weight unit of measure label', compute='_compute_weight_uom_name', readonly=True, default=_get_default_weight_uom)

    def _compute_weight_uom_name(self):
        for picking_type in self:
            picking_type.weight_uom_name = self.env['product.template']._get_weight_uom_name_from_ir_config_parameter()

    @api.model
    def _get_batch_group_by_keys(self):
        return super()._get_batch_group_by_keys() + ['batch_group_by_carrier']


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


    def _get_possible_pickings_domain(self):
        domain = super()._get_possible_pickings_domain()
        if self.picking_type_id.batch_group_by_carrier:
            domain = expression.AND([domain, [('carrier_id', '=', self.carrier_id.id if self.carrier_id else False)]])

        return domain

    def _get_possible_batches_domain(self):
        domain = super()._get_possible_batches_domain()
        if self.picking_type_id.batch_group_by_carrier:
            domain = expression.AND([domain, [('picking_ids.carrier_id', '=', self.carrier_id.id if self.carrier_id else False)]])

        return domain

    def _is_auto_batchable(self, picking=None):
        """ Verifies if a picking can be put in a batch with another picking without violating auto_batch constrains.
        """
        res = super()._is_auto_batchable(picking)
        if not picking:
            picking = self.env['stock.picking']
        if self.picking_type_id.batch_max_weight:
            res = res and (self.weight + picking.weight <= self.picking_type_id.batch_max_weight)
        return res
