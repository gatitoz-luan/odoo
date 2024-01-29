<odoo>
    <data>
        <!-- Inherit Sale Order Line Form View -->
        <record id="sale_order_line_form_view_inherited" model="ir.ui.view">
            <field name="name">sale.order.line.form.inherited</field>
            <field name="model">sale.order.line</field>
            <field name="inherit_id" ref="sale.view_order_form"/>
            <field name="arch" type="xml">
                <xpath expr="//field[@name='product_uom_qty']" position="after">
                    <field name="rental_start_date"/>
                    <field name="rental_finish_date"/>
                    <field name="cleaning_time"/>
                    <field name="rental_return_date" readonly="1"/>
                </xpath>
            </field>
        </record>
    </data>
</odoo>
