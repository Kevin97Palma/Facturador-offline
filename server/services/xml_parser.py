"""
Parser de comprobantes electrónicos SRI Ecuador (XML recibidos de proveedores).
Soporta: Factura (01), Liquidación (03), Nota Crédito (04), Nota Débito (05).
"""
import xml.etree.ElementTree as ET
from datetime import datetime


def _text(element, tag, default='') -> str:
    node = element.find(tag)
    return node.text.strip() if node is not None and node.text else default


def _float(element, tag, default=0.0) -> float:
    try:
        return float(_text(element, tag, str(default)))
    except (ValueError, TypeError):
        return default


def _parse_fecha(fecha_str: str):
    """Acepta dd/MM/yyyy o yyyy-MM-dd y devuelve date."""
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(fecha_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parsear_xml_comprobante(xml_content: str) -> dict:
    """
    Parsea un XML de comprobante electrónico SRI y devuelve un dict con los
    datos listos para crear/actualizar un CompraProveedor.

    Args:
        xml_content: String con el XML del comprobante (firmado o sin firmar).

    Returns:
        dict con:
            ok (bool)
            error (str) — solo si ok=False
            tipo_documento (str): '01', '03', '04', '05'
            tipo_nombre (str)
            clave_acceso (str)
            numero_documento (str): 'estab-ptoEmi-secuencial'
            numero_autorizacion (str)
            fecha_emision (date)
            ruc_proveedor (str)
            razon_social_proveedor (str)
            subtotal_sin_iva (float)
            subtotal_iva_0 (float)
            subtotal_iva_12 (float)
            iva (float)
            total (float)
            detalles (list[dict])
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        return {'ok': False, 'error': f'XML inválido: {e}'}

    # Detectar tipo de comprobante por el tag raíz
    tag = root.tag.lower()
    tipo_map = {
        'factura': ('01', 'Factura'),
        'liquidacioncompra': ('03', 'Liquidación de Compra'),
        'notacredito': ('04', 'Nota de Crédito'),
        'notadebito': ('05', 'Nota de Débito'),
        'comprobanteRetencion': ('07', 'Comprobante de Retención'),
    }
    tipo_codigo, tipo_nombre = None, None
    for k, (cod, nom) in tipo_map.items():
        if k in tag.replace(' ', '').lower():
            tipo_codigo, tipo_nombre = cod, nom
            break

    if not tipo_codigo:
        # Intentar por infoTributaria/codDoc
        cod_doc = _text(root, './/codDoc')
        tipo_nombre_map = {'01': 'Factura', '03': 'Liquidación de Compra',
                           '04': 'Nota de Crédito', '05': 'Nota de Débito'}
        tipo_codigo = cod_doc or '01'
        tipo_nombre = tipo_nombre_map.get(tipo_codigo, 'Comprobante')

    info_trib = root.find('infoTributaria')
    if info_trib is None:
        return {'ok': False, 'error': 'XML no contiene <infoTributaria>'}

    ruc_proveedor = _text(info_trib, 'ruc')
    razon_social = _text(info_trib, 'razonSocial')
    clave_acceso = _text(info_trib, 'claveAcceso')
    estab = _text(info_trib, 'estab', '001')
    pto_emi = _text(info_trib, 'ptoEmi', '001')
    secuencial = _text(info_trib, 'secuencial', '000000001')
    numero_documento = f'{estab}-{pto_emi}-{secuencial}'

    # Bloque de info según tipo
    fecha_emision = None
    total_sin_imp = 0.0
    total_imp = 0.0
    importe_total = 0.0
    subtotal_iva_0 = 0.0
    subtotal_iva_12 = 0.0
    iva_valor = 0.0

    # Buscar infoFactura / infoLiquidacionCompra / infoNotaCredito / infoNotaDebito
    info_node = (root.find('infoFactura') or
                 root.find('infoLiquidacionCompra') or
                 root.find('infoNotaCredito') or
                 root.find('infoNotaDebito'))

    if info_node is not None:
        fecha_str = _text(info_node, 'fechaEmision')
        fecha_emision = _parse_fecha(fecha_str) if fecha_str else None
        total_sin_imp = _float(info_node, 'totalSinImpuestos')
        importe_total = (_float(info_node, 'importeTotal') or
                         _float(info_node, 'valorTotal') or
                         _float(info_node, 'valorModificacion'))

        for imp_node in info_node.findall('.//totalImpuesto'):
            cod_porc = _text(imp_node, 'codigoPorcentaje', '0')
            base = _float(imp_node, 'baseImponible')
            valor = _float(imp_node, 'valor')
            if cod_porc == '0':
                subtotal_iva_0 += base
            elif cod_porc in ('2', '4', '5'):
                subtotal_iva_12 += base
                iva_valor += valor

    # Detalles de productos
    detalles = []
    for det in root.findall('.//detalle'):
        detalles.append({
            'codigo': _text(det, 'codigoPrincipal') or _text(det, 'codigoInterno'),
            'descripcion': _text(det, 'descripcion'),
            'cantidad': _float(det, 'cantidad', 1),
            'precio_unitario': _float(det, 'precioUnitario'),
            'descuento': _float(det, 'descuento'),
            'subtotal': _float(det, 'precioTotalSinImpuesto'),
            'iva': _float(det, './/impuesto/valor'),
        })

    return {
        'ok': True,
        'tipo_documento': tipo_codigo,
        'tipo_nombre': tipo_nombre,
        'clave_acceso': clave_acceso,
        'numero_documento': numero_documento,
        'numero_autorizacion': clave_acceso,
        'fecha_emision': fecha_emision,
        'ruc_proveedor': ruc_proveedor,
        'razon_social_proveedor': razon_social,
        'subtotal_sin_iva': total_sin_imp,
        'subtotal_iva_0': subtotal_iva_0,
        'subtotal_iva_12': subtotal_iva_12,
        'iva': iva_valor,
        'total': importe_total,
        'xml_content': xml_content,
        'detalles': detalles,
    }
