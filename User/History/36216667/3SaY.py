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

    @api.model
    def launch_replenishment(self):
        # Verifica se o produto está definido
        if not self.product_id:
            raise ValidationError("Produto não definido.")

        # Garante que a quantidade e a unidade de medida (UoM) estejam definidas
        if not self.quantity or not self.product_id.uom_id:
            raise ValidationError("Quantidade ou unidade de medida do produto não definida.")

        uom_reference = self.product_id.uom_id
        quantity = self.product_uom_id._compute_quantity(self.quantity, uom_reference, rounding_method='HALF-UP')

        # Implemente a lógica de reabastecimento aqui
        # Por exemplo, criar um pedido de compra ou movimentação de estoque para o produto

        # Exemplo fictício de como poderia ser a criação de uma ordem de reabastecimento
        try:
            replenishment_values = {
                'product_id': self.product_id.id,
                'quantity': quantity,
                'warehouse_id': self.warehouse_id.id,
                'date_planned': self.date_planned,
                # Adicione mais campos conforme necessário
            }
            # Substitua 'model.replenishment' pelo nome real do modelo onde a reabastecimento deve ser registrado
            self.env['model.replenishment'].create(replenishment_values)
        except Exception as e:
            raise ValidationError("Falha ao lançar reabastecimento: %s" % e)

        # Retorne alguma informação ou ação se necessário
        return True


    def _prepare_run_values(self):
        replenishment = self.env['procurement.group'].create({})
        values = {
            'warehouse_id': self.warehouse_id,
            'date_planned': self.date_planned,
            'group_id': replenishment,
        }
        return values

