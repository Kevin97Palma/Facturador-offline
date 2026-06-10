from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from ..database.db import db
from ..database.models import GuiaRemision, DestinatarioGuia, DetalleGuia, Empresa
from ..services.clave_acceso import generar_clave_acceso
from ..services.xml_generator import generar_xml_guia_remision
from ..services.sri_service import procesar_documento, generar_pdf
from ..config import BASE_DIR
import os

guias_bp = Blueprint('guias', __name__)


def _siguiente_numero(empresa_id):
    from sqlalchemy import func
    ultimo = db.session.query(func.max(GuiaRemision.numero)).filter_by(empresa_id=empresa_id).scalar()
    return (ultimo or 0) + 1


@guias_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    q = request.args.get('q', '')
    query = GuiaRemision.query.filter_by(empresa_id=empresa_id)
    if q:
        query = query.filter(GuiaRemision.razon_social_transportista.ilike(f'%{q}%'))
    items = query.order_by(GuiaRemision.created_at.desc()).limit(200).all()
    return jsonify({'ok': True, 'data': [_s(g) for g in items]})


@guias_bp.route('/<int:id>', methods=['GET'])
def obtener(id):
    g = GuiaRemision.query.get_or_404(id)
    return jsonify({'ok': True, 'data': _s_full(g)})


@guias_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    empresa_id = data['empresa_id']
    empresa = Empresa.query.get(empresa_id)

    numero = _siguiente_numero(empresa_id)
    fecha_ini = datetime.strptime(data['fecha_ini_transporte'], '%Y-%m-%d').date()
    fecha_fin = datetime.strptime(data['fecha_fin_transporte'], '%Y-%m-%d').date()
    clave = generar_clave_acceso(
        fecha_ini, 'guia_remision', empresa.ruc,
        empresa.ambiente, empresa.establecimiento, empresa.punto_emision, numero
    )

    g = GuiaRemision(
        empresa_id=empresa_id,
        usuario_id=data['usuario_id'],
        numero=numero,
        clave_acceso=clave,
        fecha_emision=fecha_ini,
        dir_partida=data.get('dir_partida', '').strip() or empresa.direccion,
        fecha_ini_transporte=fecha_ini,
        fecha_fin_transporte=fecha_fin,
        ruc_transportista=data['ruc_transportista'].strip(),
        razon_social_transportista=data['razon_social_transportista'].strip(),
        placa=data.get('placa', '').strip() or 'S/P',
    )
    db.session.add(g)
    db.session.flush()

    for dest_data in data.get('destinatarios', []):
        dest = DestinatarioGuia(
            guia_remision_id=g.id,
            identificacion=dest_data['identificacion_destinatario'].strip(),
            razon_social=dest_data['razon_social_destinatario'].strip(),
            direccion_destino=dest_data.get('direccion_destinatario', '').strip() or 'N/A',
            motivo_traslado=dest_data.get('motivo_traslado', '').strip() or 'Traslado de mercadería',
            num_doc_sustento=dest_data.get('num_doc_sustento', '').strip(),
        )
        db.session.add(dest)
        db.session.flush()

        for det_data in dest_data.get('detalles', []):
            det = DetalleGuia(
                destinatario_id=dest.id,
                codigo_interno=det_data.get('codigo_interno', '').strip(),
                descripcion=det_data['descripcion'].strip(),
                cantidad=float(det_data['cantidad']),
            )
            db.session.add(det)

    db.session.commit()
    return jsonify({'ok': True, 'data': _s_full(g)}), 201


@guias_bp.route('/<int:id>/autorizar', methods=['POST'])
def autorizar(id):
    g = GuiaRemision.query.get_or_404(id)
    if g.estado == 'AUTORIZADO':
        return jsonify({'ok': False, 'error': 'Ya está autorizada'}), 400

    empresa = Empresa.query.get(g.empresa_id)
    xml = generar_xml_guia_remision(empresa, g, g.destinatarios)
    resultado = procesar_documento(empresa, xml, 'GR', g.clave_acceso, BASE_DIR)

    if resultado['ok']:
        g.estado = 'AUTORIZADO'
        g.numero_autorizacion = resultado['numero_autorizacion']
        if resultado.get('fecha_autorizacion'):
            try:
                g.fecha_autorizacion = datetime.fromisoformat(
                    resultado['fecha_autorizacion'].replace('-05:00', ''))
            except Exception:
                g.fecha_autorizacion = datetime.utcnow()
        g.xml_path = resultado.get('xml_firmado_path')
        g.xml_autorizado_path = resultado.get('xml_autorizado_path')
        db.session.commit()
        return jsonify({'ok': True, 'data': _s_full(g)})
    else:
        g.estado = 'NO_AUTORIZADO'
        db.session.commit()
        return jsonify({'ok': False, 'error': resultado['error']}), 422


@guias_bp.route('/<int:id>/xml', methods=['GET'])
def descargar_xml(id):
    g = GuiaRemision.query.get_or_404(id)
    ruta = g.xml_autorizado_path or g.xml_path
    if ruta and os.path.exists(ruta):
        return send_file(ruta, as_attachment=True, download_name=f'{g.clave_acceso}.xml')
    empresa = Empresa.query.get(g.empresa_id)
    xml = generar_xml_guia_remision(empresa, g, g.destinatarios)
    from io import BytesIO
    return send_file(BytesIO(xml.encode('utf-8')), as_attachment=True,
                     download_name=f'{g.clave_acceso}.xml', mimetype='application/xml')


@guias_bp.route('/<int:id>/pdf', methods=['GET'])
def descargar_pdf(id):
    g = GuiaRemision.query.get_or_404(id)
    empresa = Empresa.query.get(g.empresa_id)
    if not empresa.pdf_url:
        return jsonify({'ok': False, 'error': 'URL del servicio PDF no configurada'}), 400
    datos = {
        'empresa': {'ruc': empresa.ruc, 'razon_social': empresa.razon_social},
        'guia': {
            'numero': g.get_numero_formateado(), 'clave_acceso': g.clave_acceso,
            'fecha_ini_transporte': g.fecha_ini_transporte.strftime('%d/%m/%Y'),
            'fecha_fin_transporte': g.fecha_fin_transporte.strftime('%d/%m/%Y'),
            'ruc_transportista': g.ruc_transportista,
            'razon_social_transportista': g.razon_social_transportista,
            'placa': g.placa or '', 'estado': g.estado,
            'numero_autorizacion': g.numero_autorizacion or '',
        },
        'destinatarios': [{
            'identificacion': d.identificacion,
            'razon_social': d.razon_social,
            'direccion': d.direccion_destino or '',
            'motivo_traslado': d.motivo_traslado or '',
            'detalles': [{'codigo': det.codigo_interno or '', 'descripcion': det.descripcion,
                          'cantidad': float(det.cantidad)} for det in d.detalles],
        } for d in g.destinatarios],
    }
    resultado = generar_pdf(empresa.pdf_url, 'guia', datos)
    if resultado['ok']:
        from io import BytesIO
        return send_file(BytesIO(resultado['content']), as_attachment=True,
                         download_name=f'RIDE_{g.clave_acceso}.pdf', mimetype='application/pdf')
    return jsonify({'ok': False, 'error': resultado['error']}), 422


def _s(g):
    return {
        'id': g.id, 'empresa_id': g.empresa_id,
        'numero': g.numero, 'numero_formateado': g.get_numero_formateado(),
        'clave_acceso': g.clave_acceso or '',
        'fecha_ini_transporte': g.fecha_ini_transporte.strftime('%Y-%m-%d'),
        'fecha_fin_transporte': g.fecha_fin_transporte.strftime('%Y-%m-%d'),
        'razon_social_transportista': g.razon_social_transportista,
        'placa': g.placa or '',
        'estado': g.estado, 'numero_autorizacion': g.numero_autorizacion or '',
        'created_at': g.created_at.strftime('%Y-%m-%d %H:%M') if g.created_at else '',
    }


def _s_full(g):
    d = _s(g)
    d.update({
        'ruc_transportista': g.ruc_transportista,
        'fecha_autorizacion': g.fecha_autorizacion.strftime('%Y-%m-%d %H:%M:%S') if g.fecha_autorizacion else '',
        'xml_path': g.xml_path or '', 'xml_autorizado_path': g.xml_autorizado_path or '',
        'destinatarios': [{
            'id': dest.id,
            'identificacion_destinatario': dest.identificacion,
            'razon_social_destinatario': dest.razon_social,
            'direccion_destinatario': dest.direccion_destino or '',
            'motivo_traslado': dest.motivo_traslado or '',
            'num_doc_sustento': dest.num_doc_sustento or '',
            'detalles': [{
                'id': det.id,
                'codigo_interno': det.codigo_interno or '',
                'descripcion': det.descripcion,
                'cantidad': float(det.cantidad),
            } for det in dest.detalles],
        } for dest in g.destinatarios],
    })
    return d
