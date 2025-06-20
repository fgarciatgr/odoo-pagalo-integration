# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class PagaloController(http.Controller):

    @http.route('/payment/pagalo/return', type='http', auth='public', csrf=False, save_session=False)
    def pagalo_return_from_checkout(self, **kwargs):
        """
        Ruta a la que Pagalo redirige al usuario después del pago.
        """
        _logger.info("Regresando de Pagalo con los parámetros: %s", kwargs)
        
        # Odoo 17+ usa un flujo diferente, donde la transacción se procesa
        # automáticamente a través de un webhook o al visitar la página de estado.
        # Aquí, simplemente buscamos la transacción y redirigimos a la página de estado de Odoo.
        # La lógica en `_get_specific_processing_values` se encargará de la verificación real.
        
        # Pagalo no parece enviar la referencia de vuelta en los parámetros de la URL,
        # por lo que Odoo identificará la transacción pendiente a través de la sesión del usuario.
        
        return request.redirect('/payment/status')
