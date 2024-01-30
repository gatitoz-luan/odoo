from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cleaning_time = fields.Integer("Dias para Limpeza")
    rental_price = fields.Float(string='Preço de Locação Diário')

    @api.onchange('list_price')
    def _onchange_list_price(self):
        self.rental_price = self.list_price

    @api.onchange('rental_price')
    def _onchange_rental_price(self):
        self.list_price = self.rental_price
        for variant in self.product_variant_ids:
            variant.rental_price = self.rental_price

            
class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Campo relacionado para garantir consistência entre os modelos
    cleaning_time = fields.Integer(related='product_tmpl_id.cleaning_time', string="Dias para Limpeza", readonly=True)

    rental_price = fields.Float(string='Preço de Locação Diário', related='product_tmpl_id.rental_price', readonly=False)

    @api.onchange('lst_price')
    def _onchange_lst_price(self):
        self.rental_price = self.lst_price

    @api.onchange('rental_price')
    def _onchange_rental_price(self):
        self.lst_price = self.rental_price
        self.product_tmpl_id.rental_price = self.rental_price

