# -*- coding: utf-8 -*-
import logging
import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

PAGALO_API_URL = "https://api.pagalo.co/v2"

class PaymentAcquirerPagalo(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('pagalo_v2', 'Pagalo v2')],
        ondelete={'pagalo_v2': 'set default'}
    )
    pagalo_v2_api_key = fields.Char(
        string='Clave API de Pagalo',
        required_if_provider='pagalo_v2',
        groups='base.group_user',
        password=True,
    )

    def _get_pagalo_v2_urls(self):
        """ Devuelve la URL base de la API de Pagalo. """
        return PAGALO_API_URL

    def _get_pagalo_v2_headers(self):
        """ Construye los encabezados para las solicitudes a la API. """
        self.ensure_one()
        if not self.pagalo_v2_api_key:
            raise ValidationError(_("La clave API de Pagalo no está configurada."))
        return {
            'x-api-key': self.pagalo_v2_api_key,
            'Content-Type': 'application/json',
        }

    def _get_redirect_form_values(self, transaction):
        """
        Anula el método estándar de Odoo para manejar la redirección.
        Aquí es donde contactamos a la API de Pagalo para crear la solicitud de pago.
        """
        self.ensure_one()
        base_url = self.get_base_url()
        return_url = f"{base_url}payment/pagalo/return"
        
        # Construir el payload según la documentación de Pagalo
        payload = {
            "amount": int(transaction.amount * 100),  # Pagalo espera el monto en centavos
            "currency": transaction.currency_id.name,
            "description": transaction.reference,
            "reference": transaction.reference,
            "returnUrl": return_url,
            "customerInformation": {
                "firstName": transaction.partner_name.split(' ')[0],
                "lastName": ' '.join(transaction.partner_name.split(' ')[1:]) or 'N/A',
                "email": transaction.partner_email,
                "phone": transaction.partner_phone or '00000000'
            }
        }

        try:
            api_url = f"{self._get_pagalo_v2_urls()}/payment-requests"
            headers = self._get_pagalo_v2_headers()
            _logger.info("Enviando solicitud de pago a Pagalo: %s", payload)
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            
            response_data = response.json()
            _logger.info("Respuesta recibida de Pagalo: %s", response_data)

            # Guardar el ID de la solicitud de pago para verificación futura
            transaction.acquirer_reference = response_data.get('paymentRequestId')
            
            # Devuelve los datos para la redirección automática
            return {
                'api_url': response_data.get('redirectUrl'),
            }

        except requests.exceptions.RequestException as e:
            _logger.error("Error al contactar la API de Pagalo: %s", e)
            raise ValidationError(_("No se pudo conectar con la pasarela de pago. Por favor, inténtelo de nuevo más tarde."))

    @api.model
    def _create_pagalo_v2_acquirer(self):
        """
        Este método se llama desde un archivo de datos para crear el adquirente de Pagalo v2.
        Usar una etiqueta de función en XML es más robusto que una etiqueta de registro
        para crear adquirentes con proveedores personalizados.
        """
        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'pagalo_v2')], limit=1)
        if not acquirer:
            view_template = self.env.ref('payment_pagalo_v2.pagalo_v2_redirect_form', raise_if_not_found=False)
            self.env['payment.acquirer'].create({
                'name': 'Pagalo v2',
                'provider': 'pagalo_v2',
                'redirect_form_template_id': view_template.id if view_template else False,
                'company_id': self.env.ref('base.main_company').id,
                'state': 'disabled', 
            })
