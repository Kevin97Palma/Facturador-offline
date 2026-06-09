from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from ..database.db import db
from ..database.models import NotaDebito, DetalleNotaDebito, Cliente, Empresa
from ..services.clave_acceso import generar_clave_acceso
from ..services.xml_generator import generar_xml_nota_debito
from ..services.sri_service import procesar_documento, generar_pdf
from ..config import BASE_DIR
import os

notas_debito_bp = Blueprint('notas_debito', __name__)


def _siguiente_numero(empresa_id):
    from sqlalchemy import func
    ultimo = db.session.query(func.max(NotaDebito.numero)).filter_by(empresa_id=empresa_id).scalar()
    return (ultimo or 0) + 1


@notas_debito_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    q = request.args.get('q', '')
    query = NotaDebito.query.filter_by(empresa_id=empresa_id)
    if q:
        query = query.join(Cliente).filter(
            (Cliente.razon_social.ilike(f'%{q}%')) |
            (Cliente.identificacion.ilike(f'%{q}%'))
        )
    items = query.order_by(NotaDebito.created_at.desc()).limit(200).all()
    return jsonify({'ok': True, 'data': [_s(n) for n in items]})


@notas_debito_bp.route('/<int:id>', methods=['GET'])
def obtener(id):
    n = NotaDebito.query.get_or_404(id)
    return jsonify({'ok': True, 'data': _s_full(n)})


@notas_debito_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    empresa_id = data['empresa_id']
    empresa = Empresa.query.get(empresa_id)

    numero = _siguiente_numero(empresa_id)
    fecha_emision = datetime.strptime(data['fecha_emision'], '%Y-%m-%d').date()
    clave = generar_clave_acceso(
        fecha_emision, 'nota_debito', empresa.ruc,
        empresa.ambiente, empresa.establecimiento, empresa.punto_emision, numero
    )

    n = NotaDebito(
        empresa_id=empresa_id,
        usuario_id=data['usuario_id'],
        cliente_id=data['cliente_id'],
        numero=numero,
        clave_acceso=clave,
        fecha_emision=fecha_emision,
        cod_doc_modificado=data.get('cod_doc_modificado', '01'),
        num_doc_modificado=data.get('num_doc_modificado', '').strip(),
        fecha_emision_doc_sustento=datetime.strptime(data['fecha_emision_doc_sustento'], '%Y-%m-%d').date() if data.get('fecha_emision_doc_sustento') else fecha_emision,
    )
    db.session.add(n)
    db.session.flush()

    total = 0
    for det in data.get('detalles', []):
        valor = float(det['valor'])
        d = DetalleNotaDebito(
            nota_debito_id=n.id,
            razon=det['razon'].strip(),
            valor=valor,
        )
        db.session.add(d)
        total += valor

    n.total = round(total, 2)
    db.session.commit()
    return jsonify({'ok': True, 'data': _s_full(n)}), 201


@notas_debito_bp.route('/<int:id>/autorizar', methods=['POST'])
def autorizar(id):
    n = NotaDebito.query.get_or_404(id)
    if n.estado == 'AUTORIZADO':
        return jsonify({'ok': False, 'error': 'Ya está autorizada'}), 400

    empresa = Empresa.query.get(n.empresa_id)
    xml = generar_xml_nota_debito(empresa, n.cliente, n, n.detalles)
    resultado = procesar_documento(empresa, xml, 'ND', n.clave_acceso, BASE_DIR)

    if resultado['ok']:
        n.estado = 'AUTORIZADO'
        n.numero_autorizacion = resultado['numero_autorizacion']
        if resultado.get('fecha_autorizacion'):
            try:
                n.fecha_autorizacion = datetime.fromisoformat(
                    resultado['fecha_autorizacion'].replace('-05:00', ''))
            except Exception:
                n.fecha_autorizacion = datetime.utcnow()
        n.xml_path = resultado.get('xml_firmado_path')
        n.xml_autorizado_path = resultado.get('xml_autorizado_path')
        db.session.commit()
        return jsonify({'ok': True, 'data': _s_full(n)})
    else:
        n.estado = 'NO_AUTORIZADO'
        db.session.commit()
        return jsonify({'ok': False, 'error': resultado['error']}), 422


@notas_debito_bp.route('/<int:id>/xml', methods=['GET'])
def descargar_xml(id):
    n = NotaDebito.query.get_or_404(id)
    ruta = n.xml_autorizado_path or n.xml_path
    if ruta and os.path.exists(ruta):
        return send_file(ruta, as_attachment=True, download_name=f'{n.clave_acceso}.xml')
    empresa = Empresa.query.get(n.empresa_id)
    xml = generar_xml_nota_debito(empresa, n.cliente, n, n.detalles)
    from io import BytesIO
    return send_file(BytesIO(xml.encode('utf-8')), as_attachment=True,
                     download_name=f'{n.clave_acceso}.xml', mimetype='application/xml')


@notas_debito_bp.route('/<int:id>/pdf', methods=['GET'])
def descargar_pdf(id):
    n = NotaDebito.query.get_or_404(id)
    empresa = Empresa.query.get(n.empresa_id)
    if not empresa.pdf_url:
        return jsonify({'ok': False, 'error': 'URL del servicio PDF no configurada'}), 400
    datos = {
        'empresa': {'ruc': empresa.ruc, 'razon_social': empresa.razon_social},
        'cliente': {'razon_social': n.cliente.razon_social, 'identificacion': n.cliente.identificacion},
        'nota_debito': {
            'numero': n.get_numero_formateado(), 'clave_acceso': n.clave_acceso,
            'fecha_emision': n.fecha_emision.strftime('%d/%m/%Y'),
            'num_doc_modificado': n.num_doc_modificado or '',
            'total': float(n.total or 0), 'estado': n.estado,
            'numero_autorizacion': n.numero_autorizacion or '',
        },
        'detalles': [{'razon': d.razon, 'valor': float(d.valor)} for d in n.detalles],
    }
    resultado = generar_pdf(empresa.pdf_url, 'nota-debito', datos)
    if resultado['ok']:
        from io import BytesIO
        return send_file(BytesIO(resultado['content']), as_attachment=True,
                         download_name=f'RIDE_{n.clave_acceso}.pdf', mimetype='application/pdf')
    return jsonify({'ok': False, 'error': resultado['error']}), 422


def _s(n):
    return {
        'id': n.id, 'empresa_id': n.empresa_id, 'cliente_id': n.cliente_id,
        'cliente_nombre': n.cliente.razon_social if n.cliente else '',
        'numero': n.numero, 'numero_formateado': n.get_numero_formateado(),
        'clave_acceso': n.clave_acceso or '',
        'fecha_emision': n.fecha_emision.strftime('%Y-%m-%d'),
        'num_doc_modificado': n.num_doc_modificado or '',
        'total': float(n.total or 0),
        'estado': n.estado, 'numero_autorizacion': n.numero_autorizacion or '',
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M') if n.created_at else '',
    }


def _s_full(n):
    d = _s(n)
    d.update({
        'cod_doc_modificado': n.cod_doc_modificado or '01',
        'fecha_emision_doc_sustento': n.fecha_emision_doc_sustento.strftime('%Y-%m-%d') if n.fecha_emision_doc_sustento else '',
        'fecha_autorizacion': n.fecha_autorizacion.strftime('%Y-%m-%d %H:%M:%S') if n.fecha_autorizacion else '',
        'xml_path': n.xml_path or '', 'xml_autorizado_path': n.xml_autorizado_path or '',
        'detalles': [{'id': det.id, 'razon': det.razon, 'valor': float(det.valor)} for det in n.detalles],
    })
    return d
