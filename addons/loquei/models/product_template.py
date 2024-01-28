# product_template.py
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cleaning_time = fields.Integer("Dias para Limpeza")
    rental_price = fields.Float("Preço de Locação Diário")
