from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    cleaning_time = fields.Integer("Tempo que o produto fica fora do estoque para limpeza")
#    rental_start_date = fields.Date("Data de Início da Locação")
#    rental_end_date = fields.Date("Data de Fim da Locação")
#    rental_duration = fields.Integer("Duração da Locação (dias)", compute="_compute_rental_duration")
    
#    @api.depends('rental_start_date', 'rental_end_date')
#    def _compute_rental_duration(self):
#        for record in self:
#            if record.rental_start_date and record.rental_end_date:
#                record.rental_duration = (record.rental_end_date - record.rental_start_date).days
#            else:
#                record.rental_duration = 0
