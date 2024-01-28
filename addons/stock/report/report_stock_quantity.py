# -*- coding: utf-8 -*-
from odoo import fields, models, tools
from datetime import datetime, timedelta

class ReportStockQuantity(models.Model):
    _name = 'report.stock.quantity'
    _auto = False
    _description = 'Stock Quantity Report for Rental'

    _depends = {
        'product.product': ['product_tmpl_id'],
        'product.template': ['type'],
        'stock.location': ['parent_path'],
        'stock.move': ['company_id', 'date', 'location_dest_id', 'location_id', 'product_id', 'product_qty', 'state'],
        'stock.quant': ['company_id', 'location_id', 'product_id', 'quantity'],
        'stock.warehouse': ['view_location_id'],
    }

    date = fields.Date(string='Date', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    state = fields.Selection([
        ('forecast', 'Forecasted Stock'),
        ('in', 'Forecasted Receipts'),
        ('out', 'Forecasted Deliveries'),
    ], string='State', readonly=True)
    product_qty = fields.Float(string='Quantity', readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', readonly=True)

    rental_start_date = fields.Date(string='Rental Start Date', readonly=True)
    rental_end_date = fields.Date(string='Rental End Date', readonly=True)
    rental_duration = fields.Integer(string='Rental Duration (Days)', readonly=True)
    cleaning_time = fields.Integer(string='Cleaning Time (Days)', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_stock_quantity')
        query = """
        
        

CREATE OR REPLACE VIEW report_stock_quantity AS (
    WITH existing_sm AS (
        SELECT 
            m.id, 
            m.product_id, 
            pt.id AS tmpl_id, 
            m.product_qty, 
            m.date, 
            m.state, 
            m.company_id, 
            COALESCE(whs.id, whd.id) AS warehouse_id
        FROM stock_move m
        LEFT JOIN stock_location ls ON ls.id = m.location_id
        LEFT JOIN stock_location ld ON ld.id = m.location_dest_id
        LEFT JOIN stock_warehouse whs ON ls.parent_path LIKE concat('%/', whs.view_location_id, '/%')
        LEFT JOIN stock_warehouse whd ON ld.parent_path LIKE concat('%/', whd.view_location_id, '/%')
        LEFT JOIN product_product pp ON pp.id = m.product_id
        LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
        WHERE pt.type = 'product' 
          AND m.product_qty != 0 
          AND m.state NOT IN ('draft', 'cancel') 
          AND (m.state IN ('draft', 'waiting', 'confirmed', 'partially_available', 'assigned') OR m.date >= (now() AT TIME ZONE 'utc')::date - INTERVAL '3 month')
          AND ((whs.id IS NOT NULL AND whd.id IS NULL) OR (whd.id IS NOT NULL AND whs.id IS NULL))
    ),
    rental_orders AS (
        SELECT
            -ro.id AS id,  -- Garantindo que o tipo seja o mesmo (integer)
            ro.rental_product_id AS product_id,
            pp.product_tmpl_id,
            'rental' AS state,
            d::date AS date,
            0::integer AS product_qty,  -- Garantindo que o tipo seja o mesmo (integer)
            pt.company_id,
            NULL::integer AS warehouse_id,  -- Garantindo que o tipo seja o mesmo (integer)
            ro.start_date AS rental_start_date,
            ro.end_date AS rental_end_date,
            (ro.end_date - ro.start_date + 1) AS rental_duration,
            pt.cleaning_time
        FROM rental_order ro
        JOIN product_product pp ON pp.id = ro.rental_product_id
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        CROSS JOIN GENERATE_SERIES(ro.start_date, ro.end_date + pt.cleaning_time, '1 day') AS d
        WHERE ro.start_date <= (now() AT TIME ZONE 'utc')::date + INTERVAL '3 month'
          AND ro.end_date >= (now() AT TIME ZONE 'utc')::date - INTERVAL '3 month'
    )
    SELECT
        MIN(id) AS id,
        product_id,
        product_tmpl_id,
        state,
        date,
        SUM(product_qty) AS product_qty,
        company_id,
        warehouse_id,
        rental_start_date,
        rental_end_date,
        rental_duration,
        cleaning_time
    FROM (
        SELECT
            esm.id,
            esm.product_id,
            esm.tmpl_id AS product_tmpl_id,
            CASE
                WHEN esm.warehouse_id IS NOT NULL AND esm.state = 'done' THEN 'in'
                WHEN esm.warehouse_id IS NOT NULL AND esm.state != 'done' THEN 'out'
            END AS state,
            esm.date::date AS date,
            CASE
                WHEN esm.state = 'done' THEN esm.product_qty
                ELSE -esm.product_qty
            END AS product_qty,
            esm.company_id,
            esm.warehouse_id,
            NULL::date AS rental_start_date,  -- Garantindo que o tipo seja o mesmo (date)
            NULL::date AS rental_end_date,  -- Garantindo que o tipo seja o mesmo (date)
            NULL::integer AS rental_duration,  -- Garantindo que o tipo seja o mesmo (integer)
            NULL::integer AS cleaning_time  -- Garantindo que o tipo seja o mesmo (integer)
        FROM existing_sm esm
        WHERE esm.product_qty != 0
        UNION ALL
        SELECT * FROM rental_orders
    ) AS combined_data
    GROUP BY product_id, product_tmpl_id, state, date, company_id, warehouse_id, rental_start_date, rental_end_date, rental_duration, cleaning_time
);




        """

        self.env.cr.execute(query)