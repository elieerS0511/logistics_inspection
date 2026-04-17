# Manual de usuario — Logistics Inspection Workflow

## Qué hace este módulo

Permite registrar en cada **albarán de stock** un **estado de inspección** (por ejemplo, control de rayos X) y, desde el propio albarán, **aprobar** o **rechazar** esa inspección. La aprobación puede **publicar facturas en borrador** del pedido de venta vinculado; el rechazo **cancela borradores**, **cancela el envío** y **devuelve el pedido de venta a borrador** para renegociar.

---

## Instalación

1. Copie la carpeta del módulo (`logistics_inspection`) al directorio de addons de su instancia Odoo (o intégrelo vía repositorio y path de addons).
2. Actualice la lista de aplicaciones (**Aplicaciones** → **Actualizar lista de aplicaciones**), con modo desarrollador si su política lo exige.
3. Busque **Logistics Inspection Workflow** e instálelo.

### Dependencias necesarias

El instalador exigirá que estén instalados (declarados en el manifiesto):

- **Ventas** — `sale_management`
- **Inventario** — `stock`
- **Contabilidad** — `account`

Sin ellos el módulo no se instala.

---

## Configuración

### Parámetros iniciales

No se añaden parámetros del sistema (`ir.config_parameter`) en este módulo: no hay pantalla de ajustes propia.

### Permisos (grupos y reglas)

El módulo **no define** archivos propios de `security/` (ACL ni reglas de registro). El usuario debe poder:

- Abrir y editar **albaranes** (`stock.picking`).
- En escenarios con aprobación/rechazo que tocan facturas y pedidos: tener permisos habituales de **contabilidad** (facturas) y **ventas** (pedidos).

Si un usuario solo tiene inventario básico, puede ver los botones pero fallar al ejecutar acciones que llamen a `action_post`, `button_cancel` o `action_draft` por restricciones de acceso.

### Buenas prácticas

- Probar primero en una base de **copia** con datos reales de flujo venta → entrega → factura borrador.
- Definir internamente **quién** puede pulsar “Rechazar inspección”, porque impacta pedido y facturación.

---

## Guía de uso (vistas principales)

1. Abra **Inventario** (o el menú donde gestione **Operaciones** / **Traslados** según su versión).
2. Localice el **albarán** (picking) correspondiente a la entrega que debe pasar inspección.
3. Abra el formulario del albarán. En la cabecera verá:
   - **Aprobar Inspección**
   - **Rechazar Inspección**
   - Una **barra de estado** con: Pendiente → Aprobado / Rechazado.
4. Los botones solo están visibles cuando la inspección está **Pendiente** (`draft`) y el albarán **no** está cancelado.
5. Tras **Aprobar**:
   - El estado de inspección pasa a **Aprobado**.
   - Si el albarán está ligado a un **pedido de venta** y existen **facturas en borrador** de ese pedido, el sistema intentará **publicarlas** y dejará un mensaje en el albarán.
6. Tras **Rechazar** (solo si hay pedido de venta vinculado al albarán):
   - Se cancelan las **facturas en borrador** del pedido.
   - Se **cancela** el albarán.
   - El **pedido de venta** vuelve a **borrador**.
   - Se registra una **alerta** en el chatter del pedido.
   - El estado de inspección queda en **Rechazado**.

---

## Caso de uso práctico: de la venta a la renegociación por fallo de inspección

**Contexto:** Su empresa vende mercancía sujeta a inspección antes de salir del almacén. El pedido ya tiene factura en borrador y un albarán de salida listo para revisión.

1. **Punto A — Pedido y documentos listos**  
   Un comercial confirma el **pedido de venta**. Se genera la **entrega** y, desde el flujo habitual, se crea o queda una **factura en borrador** vinculada al pedido.

2. **Punto B — Inspección en el albarán**  
   El responsable de logística abre el **albarán de entrega**. El estado de inspección está en **Pendiente**. Realiza el control físico / de rayos X.

3. **Rama exitosa**  
   Pulsa **Aprobar Inspección**. El estado pasa a **Aprobado**; las facturas en borrador del pedido se **publican** (contabilizan) según permisos y datos; el equipo ve el mensaje de éxito en el albarán.

4. **Rama con incidencia**  
   Detecta mercancía no conforme. Pulsa **Rechazar Inspección**. El sistema **cancela** las facturas en borrador, **cancela** el envío, devuelve el **pedido a borrador** y deja la **alerta** en el pedido para que comercial y cliente **renegocien** precios, cantidades o condiciones.

5. **Punto C — Vuelta al negocio**  
   Con el pedido otra vez en borrador, el comercial ajusta líneas, confirma de nuevo cuando corresponda y se relanza el flujo logístico y contable según sus procedimientos internos.

---

## Limitaciones que debe conocer el usuario

- Si el **albarán no está vinculado a un pedido de venta**, el rechazo **no** ejecutará cancelación de facturas ni devolución del pedido (solo cambiará el estado de inspección a rechazado al final del proceso, según el comportamiento actual del código).
- Las acciones dependen de que la **versión de Odoo** y los **módulos instalados** permitan las operaciones estándar usadas (publicar factura, cancelar, devolver pedido a borrador).

Para detalle técnico y diagramas, consulte **Manual_Tecnico.md** en esta misma carpeta.
