# -*- coding: utf-8 -*-
import logging
import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentTransactionPagalo(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_processing_values(self, processing_values):
        """
        Anula el método para obtener datos frescos de la transacción desde el proveedor.
        """
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != 'pagalo_v2':
            return res
        
        self._pagalo_v2_get_tx_status()
        return processing_values

    def _pagalo_v2_get_tx_status(self):
        """
        Contacta a la API de Pagalo para obtener el estado final de la transacción.
        """
        self.ensure_one()
        if not self.acquirer_reference:
            _logger.warning("Transacción de Pagalo sin referencia de adquirente: %s", self.reference)
            return

        api_url = f"{self.acquirer_id._get_pagalo_v2_urls()}/payment-requests/{self.acquirer_reference}"
        headers = self.acquirer_id._get_pagalo_v2_headers()

        try:
            _logger.info("Verificando estado de transacción %s en Pagalo", self.acquirer_reference)
            response = requests.get(api_url, headers=headers, timeout=20)
            response.raise_for_status()
            response_data = response.json()
            _logger.info("Respuesta de estado de Pagalo: %s", response_data)
            self._handle_pagalo_v2_notification(response_data)

        except requests.exceptions.RequestException as e:
            _logger.error("Error al verificar el estado de la transacción en Pagalo: %s", e)
            # No cambiar el estado, se puede reintentar más tarde
            pass

    def _handle_pagalo_v2_notification(self, data):
        """
        Procesa la respuesta de Pagalo y actualiza el estado de la transacción en Odoo.
        """
        self.ensure_one()
        status = data.get('status')
        
        if status == 'CAPTURED':
            self._set_done()
        elif status in ['REJECTED', 'FAILED']:
            error_message = data.get('rejectionReason') or _('El pago fue rechazado.')
            self._set_canceled(message=error_message)
        elif status == 'PENDING':
            self._set_pending()
        else:
            _logger.warning("Estado no manejado de Pagalo: %s para la transacción %s", status, self.reference)
            self._set_pending(message=_("Estado de pago desconocido: %s", status))
