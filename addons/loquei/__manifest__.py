{
    'name': 'loquei',
    'version': '1.0',
    'category': 'Productivity',
    'summary': 'Rental management integration with Quotations, Sales, and Inventory',
    'description': """modulo paa gerenciar locacoes de produtos""",
    'depends': ['sale_management', 'stock'],
    'data': ['views/rental.xml','views/cleaning_time.xml','security/ir.model.access.csv'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}