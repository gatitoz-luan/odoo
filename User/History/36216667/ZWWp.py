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


    def launch_replenishment(self):
        if not self.route_id:
            raise UserError(_("You need to select a route to replenish your products"))
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

    # TODO: to remove in master
    def _prepare_orderpoint_values(self):
        values = {
            'location_id': self.warehouse_id.lot_stock_id.id,
            'product_id': self.product_id.id,
            'qty_to_order': self.quantity,
        }
        if self.route_id:
            values['route_id'] = self.route_id.id
        return values

    def _prepare_run_values(self):
        replenishment = self.env['procurement.group'].create({})
        values = {
            'warehouse_id': self.warehouse_id,
            'route_ids': self.route_id,
            'date_planned': self.date_planned,
            'group_id': replenishment,
        }
        return values

    def _get_record_to_notify(self, date):
        return self.env['stock.move'].search([('write_date', '>=', date)], limit=1)

    def _get_replenishment_order_notification_link(self, move):
        if move.picking_id:
            action = self.env.ref('stock.stock_picking_action_picking_type')
            return [{
                'label': move.picking_id.name,
                'url': f'#action={action.id}&id={move.picking_id.id}&model=stock.picking&view_type=form'
            }]
        return False

    def _get_replenishment_order_notification(self, move):
        link = self._get_replenishment_order_notification_link(move)
        if not link:
            return False
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('The following replenishment order have been generated'),
                'message': '%s',
                'links': link,
                'sticky': False,
            }
        }

    # OVERWRITE in 'Drop Shipping', 'Dropship and Subcontracting Management' and 'Dropship and Subcontracting Management' to hide it
    def _get_allowed_route_domain(self):
        stock_location_inter_wh_id = self.env.ref('stock.stock_location_inter_wh').id
        return [
            ('product_selectable', '=', True),
            ('rule_ids.location_src_id', '!=', stock_location_inter_wh_id),
            ('rule_ids.location_dest_id', '!=', stock_location_inter_wh_id)
        ]

    def _get_route_domain(self, product_tmpl_id):
        company = product_tmpl_id.company_id or self.env.company
        domain = expression.AND([self._get_allowed_route_domain(), self.env['stock.route']._check_company_domain(company)])
        if product_tmpl_id.route_ids:
            domain = expression.AND([domain, [('product_ids', '=', product_tmpl_id.id)]])
        return domain
