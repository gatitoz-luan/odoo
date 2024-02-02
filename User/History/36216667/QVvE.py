# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression

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
    date_planned = fields.Datetime('Scheduled Date', required=True, default=lambda self: fields.Datetime.now(), help="Date at which the replenishment should take place.")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, check_company=True)
    route_id = fields.Many2one('stock.route', string='Preferred Route', check_company=True, help="Apply specific route for the replenishment instead of product's default routes.")
    company_id = fields.Many2one('res.company')
    forecasted_quantity = fields.Float(string="Forecasted Quantity", compute="_compute_forecasted_quantity")
    allowed_route_ids = fields.Many2many("stock.route", compute="_compute_allowed_route_ids")

    @api.onchange('product_id', 'warehouse_id')
    def _onchange_product_id(self):
        if not self.env.context.get('default_quantity'):
            self.quantity = abs(self.forecasted_quantity) if self.forecasted_quantity < 0 else 1

    @api.depends('warehouse_id', 'product_id')
    def _compute_forecasted_quantity(self):
        for rec in self:
            rec.forecasted_quantity = rec.product_id.with_context(warehouse=rec.warehouse_id.id).virtual_available

    @api.depends('product_id', 'product_tmpl_id')
    def _compute_allowed_route_ids(self):
        self.allowed_route_ids = self.env['stock.route'].search(self._get_allowed_route_domain())

    @api.model
    def default_get(self, fields_list):
        res = super(ProductReplenish, self).default_get(fields_list)
        if 'product_id' in fields_list:
            product_id = self.env.context.get('default_product_id') or self.env.context.get('active_id')
            product = self.env['product.product'].browse(product_id)
            if product:
                res.update({
                    'product_id': product.id,
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'product_uom_id': product.uom_id.id,
                    'company_id': product.company_id.id or self.env.company.id,
                })
                warehouse = self.env['stock.warehouse'].search([('company_id', '=', res['company_id'])], limit=1)
                res['warehouse_id'] = warehouse.id if warehouse else False
                route_domain = self._get_route_domain(product.product_tmpl_id)
                route = self.env['stock.route'].search(route_domain, limit=1)
                res['route_id'] = route.id if route else False
        return res

    def _get_route_domain(self, product_tmpl_id):
        domain = [('product_selectable', '=', True)]
        if product_tmpl_id.route_ids:
            domain += [('id', 'in', product_tmpl_id.route_ids.ids)]
        return domain

    def _get_allowed_route_domain(self):
        # This method should return a domain based on the context or specific requirements
        return [('product_selectable', '=', True)]

    def launch_replenishment(self):
        # Implementation of launch replenishment logic
        pass

    # Additional methods as previously defined
