from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from ..database.db import db
from ..database.models import NotaCredito, DetalleNotaCredito, Cliente, Empresa
from ..services.clave_acceso import generar_clave_acceso
from ..services.xml_generator import generar_xml_nota_credito
from ..services.sri_service import procesar_documento, generar_pdf
from ..config import BASE_DIR
import os

notas_credito_bp = Blueprint('notas_credito', __name__)


def _siguiente_numero(empresa_id):
    from sqlalchemy import func
    ultimo = db.session.query(func.max(NotaCredito.numero)).filter_by(empresa_id=empresa_id).scalar()
    return (ultimo or 0) + 1


@notas_credito_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    q = request.args.get('q', '')
    query = NotaCredito.query.filter_by(empresa_id=empresa_id)
    if q:
        query = query.join(Cliente).filter(
            (Cliente.razon_social.ilike(f'%{q}%')) |
            (Cliente.identificacion.ilike(f'%{q}%'))
        )
    items = query.order_by(NotaCredito.created_at.desc()).limit(200).all()
    return jsonify({'ok': True, 'data': [_s(n) for n in items]})


@notas_credito_bp.route('/<int:id>', methods=['GET'])
def obtener(id):
    n = NotaCredito.query.get_or_404(id)
    return jsonify({'ok': True, 'data': _s_full(n)})


@notas_credito_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    empresa_id = data['empresa_id']
    empresa = Empresa.query.get(empresa_id)

    numero = _siguiente_numero(empresa_id)
    fecha_emision = datetime.strptime(data['fecha_emision'], '%Y-%m-%d').date()
    clave = generar_clave_acceso(
        fecha_emision, 'nota_credito', empresa.ruc,
        empresa.ambiente, empresa.establecimiento, empresa.punto_emision, numero
    )

    n = NotaCredito(
        empresa_id=empresa_id,
        usuario_id=data['usuario_id'],
        cliente_id=data['cliente_id'],
        numero=numero,
        clave_acceso=clave,
        fecha_emision=fecha_emision,
        motivo=data.get('motivo', '').strip(),
        cod_doc_modificado=data.get('cod_doc_modificado', '01'),
        num_doc_modificado=data.get('num_doc_modificado', '').strip(),
        fecha_emision_doc_sustento=datetime.strptime(data['fecha_emision_doc_sustento'], '%Y-%m-%d').date() if data.get('fecha_emision_doc_sustento') else fecha_emision,
    )
    db.session.add(n)
    db.session.flush()

    sub0 = sub5 = sub12 = sub15 = iva5 = iva12 = iva15 = 0

    for det in data.get('detalles', []):
        cant = float(det['cantidad'])
        precio = float(det['precio_unitario'])
        desc = float(det.get('descuento', 0))
        subtotal = round(cant * precio - desc, 2)
        tarifa = float(det.get('impuesto_tarifa', 0))
        iva_val = round(subtotal * tarifa / 100, 2)
        cod_porc = det.get('impuesto_codigo_porcentaje', '0')

        d = DetalleNotaCredito(
            nota_credito_id=n.id,
            codigo_principal=det.get('codigo_principal', ''),
            descripcion=det['descripcion'].strip(),
            cantidad=cant, precio_unitario=precio, descuento=desc,
            precio_total_sin_impuesto=subtotal,
            impuesto_codigo=det.get('impuesto_codigo', '2'),
            impuesto_codigo_porcentaje=cod_porc,
            impuesto_tarifa=tarifa, impuesto_valor=iva_val,
        )
        db.session.add(d)
        if cod_porc == '0':
            sub0 += subtotal
        elif cod_porc == '5':
            sub5 += subtotal; iva5 += iva_val
        elif cod_porc == '2':
            sub12 += subtotal; iva12 += iva_val
        elif cod_porc == '4':
            sub15 += subtotal; iva15 += iva_val

    n.subtotal_sin_impuesto = round(sub0 + sub5 + sub12 + sub15, 2)
    n.iva_total = round(iva5 + iva12 + iva15, 2)
    n.total = round(n.subtotal_sin_impuesto + n.iva_total, 2)
    db.session.commit()
    return jsonify({'ok': True, 'data': _s_full(n)}), 201


@notas_credito_bp.route('/<int:id>/autorizar', methods=['POST'])
def autorizar(id):
    n = NotaCredito.query.get_or_404(id)
    if n.estado == 'AUTORIZADO':
        return jsonify({'ok': False, 'error': 'Ya está autorizada'}), 400

    empresa = Empresa.query.get(n.empresa_id)
    xml = generar_xml_nota_credito(empresa, n.cliente, n, n.detalles)
    resultado = procesar_documento(empresa, xml, 'NC', n.clave_acceso, BASE_DIR)

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


@notas_credito_bp.route('/<int:id>/xml', methods=['GET'])
def descargar_xml(id):
    n = NotaCredito.query.get_or_404(id)
    ruta = n.xml_autorizado_path or n.xml_path
    if ruta and os.path.exists(ruta):
        return send_file(ruta, as_attachment=True, download_name=f'{n.clave_acceso}.xml')
    empresa = Empresa.query.get(n.empresa_id)
    xml = generar_xml_nota_credito(empresa, n.cliente, n, n.detalles)
    from io import BytesIO
    return send_file(BytesIO(xml.encode('utf-8')), as_attachment=True,
                     download_name=f'{n.clave_acceso}.xml', mimetype='application/xml')


@notas_credito_bp.route('/<int:id>/pdf', methods=['GET'])
def descargar_pdf(id):
    n = NotaCredito.query.get_or_404(id)
    empresa = Empresa.query.get(n.empresa_id)
    if not empresa.pdf_url:
        return jsonify({'ok': False, 'error': 'URL del servicio PDF no configurada'}), 400
    datos = {
        'empresa': {'ruc': empresa.ruc, 'razon_social': empresa.razon_social},
        'cliente': {'razon_social': n.cliente.razon_social, 'identificacion': n.cliente.identificacion},
        'nota_credito': {
            'numero': n.get_numero_formateado(), 'clave_acceso': n.clave_acceso,
            'fecha_emision': n.fecha_emision.strftime('%d/%m/%Y'),
            'motivo': n.motivo, 'num_doc_modificado': n.num_doc_modificado,
            'subtotal_sin_impuesto': float(n.subtotal_sin_impuesto or 0),
            'iva_total': float(n.iva_total or 0), 'total': float(n.total or 0),
            'estado': n.estado, 'numero_autorizacion': n.numero_autorizacion or '',
        },
        'detalles': [{
            'codigo': d.codigo_principal or '', 'descripcion': d.descripcion,
            'cantidad': float(d.cantidad), 'precio_unitario': float(d.precio_unitario),
            'descuento': float(d.descuento or 0),
            'subtotal': float(d.precio_total_sin_impuesto),
            'iva': float(d.impuesto_valor or 0),
        } for d in n.detalles],
    }
    resultado = generar_pdf(empresa.pdf_url, 'nota-credito', datos)
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
        'motivo': n.motivo or '', 'total': float(n.total or 0),
        'estado': n.estado, 'numero_autorizacion': n.numero_autorizacion or '',
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M') if n.created_at else '',
    }


def _s_full(n):
    d = _s(n)
    d.update({
        'cod_doc_modificado': n.cod_doc_modificado or '01',
        'num_doc_modificado': n.num_doc_modificado or '',
        'fecha_emision_doc_sustento': n.fecha_emision_doc_sustento.strftime('%Y-%m-%d') if n.fecha_emision_doc_sustento else '',
        'subtotal_sin_impuesto': float(n.subtotal_sin_impuesto or 0),
        'iva_total': float(n.iva_total or 0),
        'fecha_autorizacion': n.fecha_autorizacion.strftime('%Y-%m-%d %H:%M:%S') if n.fecha_autorizacion else '',
        'xml_path': n.xml_path or '',
        'xml_autorizado_path': n.xml_autorizado_path or '',
        'detalles': [{
            'id': det.id, 'codigo_principal': det.codigo_principal or '',
            'descripcion': det.descripcion,
            'cantidad': float(det.cantidad), 'precio_unitario': float(det.precio_unitario),
            'descuento': float(det.descuento or 0),
            'precio_total_sin_impuesto': float(det.precio_total_sin_impuesto),
            'impuesto_codigo': det.impuesto_codigo or '2',
            'impuesto_codigo_porcentaje': det.impuesto_codigo_porcentaje or '0',
            'impuesto_tarifa': float(det.impuesto_tarifa or 0),
            'impuesto_valor': float(det.impuesto_valor or 0),
        } for det in n.detalles],
    })
    return d
