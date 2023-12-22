{
    'name': 'Stock - Packed Picking',
    'version': '16.0.1.0.0',
    'category': 'Stock/Inventory',
    'website': 'https://github.com/dmitriypaulov/test_task_packed_picking',
    'author': 'Dmytro Pavlov <dmitriy.paulov@gmail.com>',
    'company': 'Cetmix',
    'depends': [
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/stock_pack_products_views.xml',
        'views/menu.xml',
    ],
    'application': False,
    'installable': True,
    'license': 'OPL-1',
}
