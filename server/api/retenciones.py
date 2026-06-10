from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from ..database.db import db
from ..database.models import Retencion, DetalleRetencion, Proveedor, Empresa
from ..services.clave_acceso import generar_clave_acceso
from ..services.xml_generator import generar_xml_retencion
from ..services.sri_service import procesar_documento, generar_pdf
from ..config import BASE_DIR
import os

retenciones_bp = Blueprint('retenciones', __name__)


def _siguiente_numero(empresa_id):
    from sqlalchemy import func
    ultimo = db.session.query(func.max(Retencion.numero)).filter_by(empresa_id=empresa_id).scalar()
    return (ultimo or 0) + 1


@retenciones_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    q = request.args.get('q', '')
    query = Retencion.query.filter_by(empresa_id=empresa_id)
    if q:
        query = query.join(Proveedor).filter(
            (Proveedor.razon_social.ilike(f'%{q}%')) |
            (Proveedor.identificacion.ilike(f'%{q}%'))
        )
    items = query.order_by(Retencion.created_at.desc()).limit(200).all()
    return jsonify({'ok': True, 'data': [_s(r) for r in items]})


@retenciones_bp.route('/<int:id>', methods=['GET'])
def obtener(id):
    r = Retencion.query.get_or_404(id)
    return jsonify({'ok': True, 'data': _s_full(r)})


@retenciones_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    empresa_id = data['empresa_id']
    empresa = Empresa.query.get(empresa_id)

    numero = _siguiente_numero(empresa_id)
    fecha_emision = datetime.strptime(data['fecha_emision'], '%Y-%m-%d').date()
    clave = generar_clave_acceso(
        fecha_emision, 'retencion', empresa.ruc,
        empresa.ambiente, empresa.establecimiento, empresa.punto_emision, numero
    )

    r = Retencion(
        empresa_id=empresa_id,
        usuario_id=data['usuario_id'],
        proveedor_id=data['proveedor_id'],
        numero=numero,
        clave_acceso=clave,
        fecha_emision=fecha_emision,
        periodo_fiscal=data.get('periodo_fiscal', ''),
    )
    db.session.add(r)
    db.session.flush()

    total = 0
    for det in data.get('detalles', []):
        valor = round(float(det['base_imponible']) * float(det['porcentaje']) / 100, 2)
        d = DetalleRetencion(
            retencion_id=r.id,
            codigo_sustento=det.get('codigo_sustento', '01'),
            cod_doc_sustento=det.get('cod_doc_sustento', '01'),
            num_doc_sustento=det.get('num_doc_sustento', '').strip(),
            fecha_emision_doc_sustento=datetime.strptime(det['fecha_emision_doc_sustento'], '%Y-%m-%d').date() if det.get('fecha_emision_doc_sustento') else fecha_emision,
            codigo_retencion=det['codigo'].strip(),
            tipo_retencion=det.get('tipo_retencion', 'renta'),
            descripcion=det.get('descripcion', '').strip(),
            base_imponible=float(det['base_imponible']),
            porcentaje_retener=float(det['porcentaje']),
            valor_retenido=valor,
        )
        db.session.add(d)
        total += valor

    r.total_retenido = round(total, 2)
    db.session.commit()
    return jsonify({'ok': True, 'data': _s_full(r)}), 201


@retenciones_bp.route('/<int:id>/autorizar', methods=['POST'])
def autorizar(id):
    r = Retencion.query.get_or_404(id)
    if r.estado == 'AUTORIZADO':
        return jsonify({'ok': False, 'error': 'Ya está autorizada'}), 400

    empresa = Empresa.query.get(r.empresa_id)
    proveedor = Proveedor.query.get(r.proveedor_id)
    xml = generar_xml_retencion(empresa, proveedor, r, r.detalles)
    resultado = procesar_documento(empresa, xml, 'RT', r.clave_acceso, BASE_DIR)

    if resultado['ok']:
        r.estado = 'AUTORIZADO'
        r.numero_autorizacion = resultado['numero_autorizacion']
        if resultado.get('fecha_autorizacion'):
            try:
                r.fecha_autorizacion = datetime.fromisoformat(
                    resultado['fecha_autorizacion'].replace('-05:00', ''))
            except Exception:
                r.fecha_autorizacion = datetime.utcnow()
        r.xml_path = resultado.get('xml_firmado_path')
        r.xml_autorizado_path = resultado.get('xml_autorizado_path')
        db.session.commit()
        return jsonify({'ok': True, 'data': _s_full(r)})
    else:
        r.estado = 'NO_AUTORIZADO'
        db.session.commit()
        return jsonify({'ok': False, 'error': resultado['error']}), 422


@retenciones_bp.route('/<int:id>/xml', methods=['GET'])
def descargar_xml(id):
    r = Retencion.query.get_or_404(id)
    ruta = r.xml_autorizado_path or r.xml_path
    if ruta and os.path.exists(ruta):
        return send_file(ruta, as_attachment=True, download_name=f'{r.clave_acceso}.xml')
    empresa = Empresa.query.get(r.empresa_id)
    proveedor = Proveedor.query.get(r.proveedor_id)
    xml = generar_xml_retencion(empresa, proveedor, r, r.detalles)
    from io import BytesIO
    return send_file(BytesIO(xml.encode('utf-8')), as_attachment=True,
                     download_name=f'{r.clave_acceso}.xml', mimetype='application/xml')


@retenciones_bp.route('/<int:id>/pdf', methods=['GET'])
def descargar_pdf(id):
    r = Retencion.query.get_or_404(id)
    empresa = Empresa.query.get(r.empresa_id)
    if not empresa.pdf_url:
        return jsonify({'ok': False, 'error': 'URL del servicio PDF no configurada'}), 400
    datos = {
        'empresa': {'ruc': empresa.ruc, 'razon_social': empresa.razon_social},
        'proveedor': {
            'razon_social': r.proveedor.razon_social,
            'identificacion': r.proveedor.identificacion,
        },
        'retencion': {
            'numero': r.get_numero_formateado(),
            'clave_acceso': r.clave_acceso,
            'fecha_emision': r.fecha_emision.strftime('%d/%m/%Y'),
            'periodo_fiscal': r.periodo_fiscal or '',
            'total_retenido': float(r.total_retenido or 0),
            'estado': r.estado,
            'numero_autorizacion': r.numero_autorizacion or '',
        },
        'detalles': [{
            'codigo': d.codigo_retencion, 'descripcion': d.descripcion or '',
            'base_imponible': float(d.base_imponible),
            'porcentaje': float(d.porcentaje_retener),
            'valor_retenido': float(d.valor_retenido),
        } for d in r.detalles],
    }
    resultado = generar_pdf(empresa.pdf_url, 'retencion', datos)
    if resultado['ok']:
        from io import BytesIO
        return send_file(BytesIO(resultado['content']), as_attachment=True,
                         download_name=f'RIDE_{r.clave_acceso}.pdf', mimetype='application/pdf')
    return jsonify({'ok': False, 'error': resultado['error']}), 422


def _s(r):
    return {
        'id': r.id, 'empresa_id': r.empresa_id,
        'proveedor_id': r.proveedor_id,
        'proveedor_nombre': r.proveedor.razon_social if r.proveedor else '',
        'proveedor_identificacion': r.proveedor.identificacion if r.proveedor else '',
        'numero': r.numero, 'numero_formateado': r.get_numero_formateado(),
        'clave_acceso': r.clave_acceso or '',
        'fecha_emision': r.fecha_emision.strftime('%Y-%m-%d'),
        'total_retenido': float(r.total_retenido or 0),
        'estado': r.estado,
        'numero_autorizacion': r.numero_autorizacion or '',
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else '',
    }


def _s_full(r):
    d = _s(r)
    d.update({
        'periodo_fiscal': r.periodo_fiscal or '',
        'fecha_autorizacion': r.fecha_autorizacion.strftime('%Y-%m-%d %H:%M:%S') if r.fecha_autorizacion else '',
        'xml_path': r.xml_path or '',
        'xml_autorizado_path': r.xml_autorizado_path or '',
        'detalles': [{
            'id': det.id,
            'codigo_sustento': det.codigo_sustento or '01',
            'cod_doc_sustento': det.cod_doc_sustento or '01',
            'num_doc_sustento': det.num_doc_sustento or '',
            'fecha_emision_doc_sustento': det.fecha_emision_doc_sustento.strftime('%Y-%m-%d') if det.fecha_emision_doc_sustento else '',
            'codigo': det.codigo_retencion,
            'descripcion': det.descripcion or '',
            'base_imponible': float(det.base_imponible),
            'porcentaje': float(det.porcentaje_retener),
            'valor_retenido': float(det.valor_retenido),
        } for det in r.detalles],
    })
    return d
