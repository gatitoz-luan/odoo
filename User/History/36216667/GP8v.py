# -*- coding: utf-8 -*-
import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import clean_context

class ProductReplenish(models.TransientModel):
    _name = 'product.replenish'
    _description = 'Product Replenish'
    _check_company_auto = True

    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', required=True)
    product_has_variants = fields.Boolean('Has variants', default=False, required=True)
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id', readonly=True, required=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unity of measure', required=True)
    forecast_uom_id = fields.Many2one(related='product_id.uom_id')
    quantity = fields.Float('Quantity', default=1, required=True)
    date_planned = fields.Datetime('Scheduled Date', required=True, compute="_compute_date_planned", readonly=False,
        help="Date at which the replenishment should take place.", store=True, precompute=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse', required=True,
        check_company=True,
    )
    company_id = fields.Many2one('res.company')
    forecasted_quantity = fields.Float(string="Forecasted Quantity", compute="_compute_forecasted_quantity")
    allowed_route_ids = fields.Many2many('stock.route', string='Allowed Routes')

    @api.onchange('product_id', 'warehouse_id')
    def _onchange_product_id(self):
        if not self.env.context.get('default_quantity'):
            self.quantity = abs(self.forecasted_quantity) if self.forecasted_quantity < 0 else 1

    @api.depends('warehouse_id', 'product_id')
    def _compute_forecasted_quantity(self):
        for rec in self:
            rec.forecasted_quantity = rec.product_id.with_context(warehouse=rec.warehouse_id.id).virtual_available

    @api.depends('product_id')
    def _compute_date_planned(self):
        for rec in self:
            rec.date_planned = rec._get_date_planned()

    @api.model
    def default_get(self, fields):
        res = super(ProductReplenish, self).default_get(fields)
        # O código foi ajustado para não depender do route_id, mas sim das configurações padrão do produto
        return res

    def _get_date_planned(self, **kwargs):
        now = fields.Datetime.now()
        # A lógica para calcular o delay pode ser ajustada conforme necessário
        return now  # Retorne a data atual como padrão ou ajuste conforme a lógica de negócios

    def launch_replenishment(self):
        uom_reference = self.product_id.uom_id
        self.quantity = self.product_uom_id._compute_quantity(self.quantity, uom_reference, rounding_method='HALF-UP')
        try:
            now = self.env.cr.now()
            self.env['procurement.group'].with_context(clean_context(self.env.context)).run([
                self.env['procurement.group'].Procurement(
                    self.product_id,
                    self.quantity,
                    uom_reference,
                    self.warehouse_id.lot_stock_id,  # Location
                    _("Manual Replenishment"),  # Name
                    _("Manual Replenishment"),  # Origin
                    self.warehouse_id.company_id,
                    self._prepare_run_values()  # Values
                )
            ])
            move = self._get_record_to_notify(now)
            notification = self._get_replenishment_order_notification(move)
            act_window_close = {
                'type': 'ir.actions.act_window_close',
                'infos': {'done': True},
            }
            if notification:
                notification['params']['next'] = act_window_close
                return notification
            return act_window_close
        except UserError as error:
            raise UserError(error)

    def _prepare_run_values(self):
        replenishment = self.env['procurement.group'].create({})
        values = {
            'warehouse_id': self.warehouse_id,
            'date_planned': self.date_planned,
            'group_id': replenishment,
        }
        return values

