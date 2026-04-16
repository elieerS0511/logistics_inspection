{
    'name': 'Logistics Inspection Workflow',
    'version': '19.0.1.0.0',
    'author': 'ESGD',
    'category': 'Inventory',
    'summary': 'Gestión de inspección de rayos X con retroceso a negociación',
    'depends': ['sale_management', 'stock', 'account'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}