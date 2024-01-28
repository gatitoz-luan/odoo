{
    'name': 'loquei',
    'version': '1.0',
    'category': 'Productivity',
    'summary': 'Rental management integration with Quotations, Sales, and Inventory',
    'description': """modulo paa gerenciar locacoes de produtos""",
    'depends': ['sale','sale_management', 'stock', 'base', 'product'],
    'data': [
        'security/security_groups.xml',    # Primeiro defina os grupos de segurança
        'security/ir.model.access.csv',    # Em seguida, defina as regras de acesso
        'views/rental_order_view.xml',
        'views/product_template_view.xml',
        'views/rental.xml'
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}