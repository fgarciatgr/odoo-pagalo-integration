{
    'name': 'Pagalo v2 Payment Acquirer',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Integra la pasarela de pagos Pagalo v2 con Odoo',
    'author': 'Tu Nombre',
    'website': 'https://www.tuempresa.com',
    'license': 'LGPL-3',
    'depends': [
        'payment'
    ],
    'data': [
        'views/payment_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'application': True,
    'installable': True,
}