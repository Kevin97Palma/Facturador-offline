import os
import time
import requests
import requests.exceptions


def firmar_xml(fe_url: str, xml_content: str, ruta_firma: str, clave_firma: str,
               ruta_xml_sin_firmar: str, ruta_xml_firmado: str) -> dict:
    os.makedirs(os.path.dirname(ruta_xml_sin_firmar), exist_ok=True)
    os.makedirs(os.path.dirname(ruta_xml_firmado), exist_ok=True)

    with open(ruta_xml_sin_firmar, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    payload = {
        'pathXml': ruta_xml_sin_firmar,
        'pathXmlFirmado': ruta_xml_firmado,
        'pathFirma': ruta_firma,
        'claveFirma': clave_firma,
    }
    try:
        resp = requests.post(f'{fe_url}/api/facturacion/FirmaXml', json=payload, timeout=30, verify=False)
        resp.raise_for_status()
        return {'ok': True, 'ruta_firmado': ruta_xml_firmado}
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': str(e)}


def recepcionar_sri(fe_url: str, ruta_xml_firmado: str) -> dict:
    payload = {'pathXmlFirmado': ruta_xml_firmado}
    try:
        resp = requests.post(f'{fe_url}/api/facturacion/Recepcion', json=payload, timeout=30, verify=False)
        resp.raise_for_status()
        data = resp.json()
        return {'ok': True, 'respuesta': data.get('respuestaRecepcion', ''), 'data': data}
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': str(e)}


def autorizar_sri(fe_url: str, ruta_xml_firmado: str, clave_acceso: str,
                  ruta_xml_autorizado: str) -> dict:
    os.makedirs(os.path.dirname(ruta_xml_autorizado), exist_ok=True)
    payload = {
        'pathXmlFirmado': ruta_xml_firmado,
        'ClaveAcceso': clave_acceso,
        'PathXmlAutorizado': ruta_xml_autorizado,
    }
    try:
        resp = requests.post(f'{fe_url}/api/facturacion/Autorizacion', json=payload, timeout=60, verify=False)
        resp.raise_for_status()
        data = resp.json()
        return {
            'ok': True,
            'respuesta': data.get('respuestaAutorizacion', ''),
            'fecha_autorizacion': data.get('fechaAutorizacion'),
            'data': data,
        }
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': str(e)}


def generar_pdf(pdf_url: str, tipo: str, datos: dict) -> dict:
    """
    tipo: factura | nota-credito | nota-debito | retencion | guia | liquidacion
    """
    try:
        resp = requests.post(f'{pdf_url}/{tipo}', json=datos, timeout=60, verify=False)
        resp.raise_for_status()
        return {'ok': True, 'content': resp.content, 'data': resp.json() if resp.headers.get('content-type', '').startswith('application/json') else None}
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': str(e)}


def procesar_documento(empresa, xml_content: str, tipo_doc: str, clave_acceso: str,
                       base_dir: str) -> dict:
    """
    Flujo completo: firmar → recepcionar → autorizar.
    Retorna dict con ok, numero_autorizacion, fecha_autorizacion, xml_autorizado_path
    """
    if not empresa.fe_url:
        return {'ok': False, 'error': 'URL del servicio FE no configurada para esta empresa'}
    if not empresa.nombre_archivo_firma:
        return {'ok': False, 'error': 'Firma electrónica no configurada'}
    if not empresa.clave_firma:
        return {'ok': False, 'error': 'Clave de firma no configurada'}

    ruta_firma = os.path.join(base_dir, 'private', 'firmas', empresa.nombre_archivo_firma)
    if not os.path.exists(ruta_firma):
        return {'ok': False, 'error': f'Archivo de firma no encontrado: {empresa.nombre_archivo_firma}'}

    xml_dir = os.path.join(base_dir, 'private', 'xml', empresa.ruc, tipo_doc)
    ruta_sin_firmar = os.path.join(xml_dir, 'sin_firmar', f'{clave_acceso}.xml')
    ruta_firmado = os.path.join(xml_dir, 'firmado', f'{clave_acceso}_firmado.xml')
    ruta_autorizado = os.path.join(xml_dir, 'autorizado', f'{clave_acceso}.xml')

    resultado_firma = firmar_xml(
        empresa.fe_url, xml_content, ruta_firma, empresa.clave_firma,
        ruta_sin_firmar, ruta_firmado
    )
    if not resultado_firma['ok']:
        return {'ok': False, 'error': f'Error al firmar: {resultado_firma["error"]}'}

    resultado_recepcion = recepcionar_sri(empresa.fe_url, ruta_firmado)
    if not resultado_recepcion['ok']:
        return {'ok': False, 'error': f'Error en recepción SRI: {resultado_recepcion["error"]}'}

    if resultado_recepcion['respuesta'] not in ('RECIBIDA', 'DEVUELTA'):
        return {'ok': False, 'error': f'SRI no recibió el comprobante: {resultado_recepcion["respuesta"]}'}

    time.sleep(3)

    resultado_autorizacion = autorizar_sri(empresa.fe_url, ruta_firmado, clave_acceso, ruta_autorizado)
    if not resultado_autorizacion['ok']:
        return {'ok': False, 'error': f'Error en autorización SRI: {resultado_autorizacion["error"]}'}

    if resultado_autorizacion['respuesta'] != 'AUTORIZADO':
        return {
            'ok': False,
            'error': f'Comprobante no autorizado por SRI: {resultado_autorizacion["respuesta"]}',
            'datos': resultado_autorizacion.get('data')
        }

    return {
        'ok': True,
        'numero_autorizacion': clave_acceso,
        'fecha_autorizacion': resultado_autorizacion['fecha_autorizacion'],
        'xml_firmado_path': ruta_firmado,
        'xml_autorizado_path': ruta_autorizado,
    }
