from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    inspection_state = fields.Selection([
        ('draft', 'Pendiente'),
        ('passed', 'Aprobado'),
        ('failed', 'Rechazado')
    ], string="Estado Inspección", default='draft', tracking=True)

    def action_inspection_pass(self):
        """Aprobar inspección y validar facturas borrador"""
        self.write({'inspection_state': 'passed'})
        for picking in self:
            if picking.sale_id:
                # Localizamos facturas vinculadas en borrador y las publicamos
                draft_invoices = picking.sale_id.invoice_ids.filtered(lambda inv: inv.state == 'draft')
                if draft_invoices:
                    draft_invoices.action_post()
                
                picking.message_post(body=_("Inspección de Rayos X exitosa. Facturación procesada."))

    def action_inspection_fail(self):
        """Rechazar inspección y resetear todo el flujo comercial"""
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