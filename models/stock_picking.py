"""Extensión del modelo ``stock.picking`` para flujo de inspección logística.

Este submódulo añade un estado de inspección y acciones de servidor que enlazan
la validación del albarán con la facturación y el pedido de venta asociado.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    """Extensión de albaranes de stock con inspección y acoplamiento a ventas/facturas.

    Hereda de ``stock.picking`` Y añade campos y métodos de negocio sobre el modelo estándar de Odoo sin
    reemplazar su definición base.

    El estado de inspección gobierna la visibilidad de los botones en la vista
    formulario y se integra con el chatter mediante ``tracking`` en el campo.
    """

    _inherit = 'stock.picking'

    inspection_state = fields.Selection([
        ('draft', 'Pendiente'),
        ('passed', 'Aprobado'),
        ('failed', 'Rechazado')
    ], string="Estado Inspección", default='draft', tracking=True)

    def action_inspection_pass(self):
        """Marca la inspección como aprobada y contabiliza facturas en borrador vinculadas al pedido.

        Para cada albarán del conjunto ``self``, si existe un ``sale_id``, localiza
        las facturas del pedido en estado borrador y las publica (``action_post``).
        Registra un mensaje en el chatter del albarán cuando hay pedido asociado.

        :param self: Albaranes sobre los que se ejecuta la acción (puede ser un
            recordset múltiple).
        :type self: :class:`~odoo.models.Model` / recordset ``stock.picking``

        :return: ``None`` implícito salvo que el núcleo o extensiones interpreten
            otro valor (acción de botón estándar).

        .. note::
            Los albaranes sin ``sale_id`` solo actualizan ``inspection_state`` a
            aprobado; no se intenta facturación automática (comportamiento heredado
            del bucle condicional, no modificado aquí).
        """
        self.write({'inspection_state': 'passed'})
        for picking in self:
            if picking.sale_id:
                # Localizamos facturas vinculadas en borrador y las publicamos
                draft_invoices = picking.sale_id.invoice_ids.filtered(lambda inv: inv.state == 'draft')
                if draft_invoices:
                    draft_invoices.action_post()
                
                picking.message_post(body=_("Inspección de Rayos X exitosa. Facturación procesada."))

    def action_inspection_fail(self):
        """Rechaza la inspección y revierte el flujo comercial asociado al pedido de venta.

        Por cada albarán con ``sale_id``:

        #. Cancela las facturas en borrador del pedido.
        #. Cancela el albarán actual (``action_cancel``).
        #. Devuelve el pedido de venta a borrador (``action_draft``).
        #. Publica una alerta en el chatter del pedido.

        Al finalizar el bucle, todos los registros en ``self`` reciben
        ``inspection_state`` = ``failed``.

        :param self: Albaranes sobre los que se rechaza la inspección.
        :type self: recordset ``stock.picking``

        :return: ``None`` implícito (acción de botón sin retorno de acción cliente).

        .. warning::
            Si un albarán no tiene ``sale_id``, el ``continue`` omite cancelación de
            facturas, cancelación del movimiento y retorno del pedido a borrador
            para ese registro concreto; no obstante, el ``write`` final aplica
            ``failed`` a todo el conjunto ``self``. Comportamiento a tener en cuenta
            en operaciones masivas o albaranes huérfanos de venta.

        .. note::
            La disponibilidad de ``sale.order.action_draft`` y el efecto exacto de
            cancelar facturas/albaranes dependen de la versión de Odoo y de
            módulos adicionales; conviene validar en entorno de pruebas antes de
            producción.
        """
        for picking in self:
            if not picking.sale_id:
                continue

            order = picking.sale_id
            
            # 1. Cancelar facturas en borrador
            draft_invoices = order.invoice_ids.filtered(lambda inv: inv.state == 'draft')
            for inv in draft_invoices:
                inv.button_cancel()
            
            # 2. Cancelar el movimiento de inventario actual
            picking.action_cancel()
            
            # 3. Regresar la Orden de Venta a borrador (Negociación)
            order.action_draft()
            
            # 4. Notificar en el Chatter del pedido
            order.message_post(body=_(
                "ALERTA: El envío %s falló en Rayos X. El pedido ha sido devuelto a borrador para renegociación.", 
                picking.name
            ))
        
        self.write({'inspection_state': 'failed'})