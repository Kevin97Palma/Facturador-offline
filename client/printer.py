"""ESC/POS and Windows ticket printing."""
from . import config as cfg


def _get_printer():
    ptype = cfg.get('printer_type', 'none')
    if ptype == 'escpos_usb':
        from escpos.printer import Usb
        return Usb(0x04b8, 0x0202, profile='TM-T20')
    elif ptype == 'escpos_network':
        from escpos.printer import Network
        ip = cfg.get('printer_ip', '')
        port = int(cfg.get('printer_port', 9100))
        return Network(ip, port)
    elif ptype == 'windows':
        from escpos.printer import Win32Raw
        name = cfg.get('printer_name', '')
        return Win32Raw(name)
    return None


def imprimir_prueba():
    p = _get_printer()
    if not p:
        raise RuntimeError('No hay impresora configurada')
    p.text('=== PRUEBA DE IMPRESION ===\n')
    p.text('Sistema de Facturacion\n')
    p.text('========================\n')
    p.cut()


def imprimir_ticket_factura(factura: dict):
    p = _get_printer()
    if not p:
        raise RuntimeError('No hay impresora de tickets configurada')

    empresa = factura.get('empresa', {})
    cliente = factura.get('cliente', {})
    f = factura

    p.set(align='center', bold=True, width=2, height=2)
    rs = (empresa.get('razon_social') or f.get('empresa_razon_social', ''))[:24]
    p.text(f'{rs}\n')
    p.set(align='center', bold=False, width=1, height=1)
    ruc = empresa.get('ruc') or ''
    p.text(f'RUC: {ruc}\n')
    p.text('--------------------------------\n')

    p.set(align='left', bold=True)
    p.text('FACTURA\n')
    p.set(bold=False)
    p.text(f'N°: {f.get("numero_formateado", "")}\n')
    p.text(f'Fecha: {f.get("fecha_emision", "")}\n')
    p.text('--------------------------------\n')
    p.text(f'Cliente: {f.get("cliente_nombre", "")}\n')
    p.text(f'RUC/CI: {f.get("cliente_identificacion", "")}\n')
    p.text('================================\n')

    p.set(bold=True)
    p.text(f'{"DESCRIPCION":<20}{"CANT":>4}{"TOTAL":>8}\n')
    p.set(bold=False)
    p.text('--------------------------------\n')

    for det in f.get('detalles', []):
        desc = str(det.get('descripcion', ''))[:20]
        cant = float(det.get('cantidad', 0))
        sub = float(det.get('precio_total_sin_impuesto', 0))
        p.text(f'{desc:<20}{cant:>4.0f}{sub:>8.2f}\n')

    p.text('================================\n')
    subtotal = float(f.get('subtotal_sin_impuesto', 0))
    iva12 = float(f.get('iva_12', 0))
    iva15 = float(f.get('iva_15', 0))
    total = float(f.get('total', 0))
    p.text(f'{"Subtotal:":<22}{subtotal:>10.2f}\n')
    if iva12 > 0:
        p.text(f'{"IVA 12%:":<22}{iva12:>10.2f}\n')
    if iva15 > 0:
        p.text(f'{"IVA 15%:":<22}{iva15:>10.2f}\n')
    p.set(bold=True)
    p.text(f'{"TOTAL:":<22}{total:>10.2f}\n')
    p.set(bold=False)
    p.text('================================\n')

    auth = f.get('numero_autorizacion', '')
    if auth:
        p.set(align='center')
        p.text(f'Auth: {auth[:20]}\n')
        p.text(f'{auth[20:]}\n' if len(auth) > 20 else '')

    p.text('\n\n')
    p.cut()
