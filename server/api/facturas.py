import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from ..database.db import db
from ..database.models import Factura, DetalleFactura, Cliente, Empresa
from ..services.clave_acceso import generar_clave_acceso
from ..services.xml_generator import generar_xml_factura
from ..services.sri_service import procesar_documento, generar_pdf
from ..config import BASE_DIR

facturas_bp = Blueprint('facturas', __name__)


def _siguiente_numero(empresa_id):
    from sqlalchemy import func
    ultimo = db.session.query(func.max(Factura.numero)).filter_by(empresa_id=empresa_id).scalar()
    return (ultimo or 0) + 1


@facturas_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    q = request.args.get('q', '')
    estado = request.args.get('estado', '')
    query = Factura.query.filter_by(empresa_id=empresa_id)
    if q:
        query = query.join(Cliente).filter(
            (Cliente.razon_social.ilike(f'%{q}%')) |
            (Cliente.identificacion.ilike(f'%{q}%'))
        )
    if estado:
        query = query.filter_by(estado=estado)
    facturas = query.order_by(Factura.created_at.desc()).limit(200).all()
    return jsonify({'ok': True, 'data': [_s(f) for f in facturas]})


@facturas_bp.route('/<int:id>', methods=['GET'])
def obtener(id):
    f = Factura.query.get_or_404(id)
    return jsonify({'ok': True, 'data': _s_full(f)})


@facturas_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    empresa_id = data['empresa_id']
    empresa = Empresa.query.get(empresa_id)
    cliente = Cliente.query.get(data['cliente_id'])

    numero = _siguiente_numero(empresa_id)
    fecha_emision = datetime.strptime(data['fecha_emision'], '%Y-%m-%d').date()
    clave = generar_clave_acceso(
        fecha_emision, 'factura', empresa.ruc,
        empresa.ambiente, empresa.establecimiento, empresa.punto_emision, numero
    )

    f = Factura(
        empresa_id=empresa_id,
        usuario_id=data['usuario_id'],
        cliente_id=data['cliente_id'],
        numero=numero,
        clave_acceso=clave,
        fecha_emision=fecha_emision,
        forma_pago=data.get('forma_pago', '01'),
        observacion=data.get('observacion', '').strip() or None,
    )
    db.session.add(f)
    db.session.flush()

    sub0 = sub5 = sub12 = sub15 = iva5 = iva12 = iva15 = desc_total = 0

    for det in data.get('detalles', []):
        cant = float(det['cantidad'])
        precio = float(det['precio_unitario'])
        desc = float(det.get('descuento', 0))
        subtotal = round(cant * precio - desc, 2)
        tarifa = float(det.get('impuesto_tarifa', 0))
        iva_val = round(subtotal * tarifa / 100, 2)
        cod_porc = det.get('impuesto_codigo_porcentaje', '0')

        d = DetalleFactura(
            factura_id=f.id,
            producto_id=det.get('producto_id') or None,
            codigo_principal=det.get('codigo_principal', ''),
            descripcion=det['descripcion'].strip(),
            cantidad=cant, precio_unitario=precio, descuento=desc,
            precio_total_sin_impuesto=subtotal,
            impuesto_codigo=det.get('impuesto_codigo', '2'),
            impuesto_codigo_porcentaje=cod_porc,
            impuesto_tarifa=tarifa, impuesto_valor=iva_val,
        )
        db.session.add(d)
        desc_total += desc
        if cod_porc == '0':
            sub0 += subtotal
        elif cod_porc == '5':
            sub5 += subtotal; iva5 += iva_val
        elif cod_porc == '2':
            sub12 += subtotal; iva12 += iva_val
        elif cod_porc == '4':
            sub15 += subtotal; iva15 += iva_val

    f.subtotal_sin_impuesto = round(sub0 + sub5 + sub12 + sub15, 2)
    f.subtotal_iva_0 = round(sub0, 2)
    f.subtotal_iva_5 = round(sub5, 2)
    f.subtotal_iva_12 = round(sub12, 2)
    f.subtotal_iva_15 = round(sub15, 2)
    f.iva_5 = round(iva5, 2)
    f.iva_12 = round(iva12, 2)
    f.iva_15 = round(iva15, 2)
    f.descuento_total = round(desc_total, 2)
    f.total = round(f.subtotal_sin_impuesto + iva5 + iva12 + iva15, 2)

    db.session.commit()
    return jsonify({'ok': True, 'data': _s_full(f)}), 201


@facturas_bp.route('/<int:id>/autorizar', methods=['POST'])
def autorizar(id):
    f = Factura.query.get_or_404(id)
    if f.estado == 'AUTORIZADO':
        return jsonify({'ok': False, 'error': 'Ya está autorizada'}), 400

    empresa = Empresa.query.get(f.empresa_id)
    xml = generar_xml_factura(empresa, f.cliente, f, f.detalles)
    resultado = procesar_documento(empresa, xml, 'FV', f.clave_acceso, BASE_DIR)

    if resultado['ok']:
        f.estado = 'AUTORIZADO'
        f.numero_autorizacion = resultado['numero_autorizacion']
        if resultado.get('fecha_autorizacion'):
            try:
                f.fecha_autorizacion = datetime.fromisoformat(
                    resultado['fecha_autorizacion'].replace('-05:00', ''))
            except Exception:
                f.fecha_autorizacion = datetime.utcnow()
        f.xml_path = resultado.get('xml_firmado_path')
        f.xml_autorizado_path = resultado.get('xml_autorizado_path')
        db.session.commit()
        return jsonify({'ok': True, 'data': _s_full(f)})
    else:
        f.estado = 'NO_AUTORIZADO'
        db.session.commit()
        return jsonify({'ok': False, 'error': resultado['error']}), 422


@facturas_bp.route('/<int:id>/anular', methods=['POST'])
def anular(id):
    f = Factura.query.get_or_404(id)
    f.estado = 'ANULADO'
    db.session.commit()
    return jsonify({'ok': True})


@facturas_bp.route('/<int:id>/xml', methods=['GET'])
def descargar_xml(id):
    f = Factura.query.get_or_404(id)
    ruta = f.xml_autorizado_path or f.xml_path
    if ruta and os.path.exists(ruta):
        return send_file(ruta, as_attachment=True, download_name=f'{f.clave_acceso}.xml')
    empresa = Empresa.query.get(f.empresa_id)
    xml = generar_xml_factura(empresa, f.cliente, f, f.detalles)
    from io import BytesIO
    return send_file(BytesIO(xml.encode('utf-8')), as_attachment=True,
                     download_name=f'{f.clave_acceso}.xml', mimetype='application/xml')


@facturas_bp.route('/<int:id>/pdf', methods=['GET'])
def descargar_pdf(id):
    f = Factura.query.get_or_404(id)
    empresa = Empresa.query.get(f.empresa_id)
    if not empresa.pdf_url:
        return jsonify({'ok': False, 'error': 'URL del servicio PDF no configurada'}), 400
    datos = _preparar_datos_pdf(empresa, f)
    resultado = generar_pdf(empresa.pdf_url, 'factura', datos)
    if resultado['ok']:
        from io import BytesIO
        return send_file(BytesIO(resultado['content']), as_attachment=True,
                         download_name=f'RIDE_{f.clave_acceso}.pdf', mimetype='application/pdf')
    return jsonify({'ok': False, 'error': resultado['error']}), 422


def _preparar_datos_pdf(empresa, f):
    return {
        'empresa': {
            'ruc': empresa.ruc, 'razon_social': empresa.razon_social,
            'nombre_comercial': empresa.nombre_comercial or empresa.razon_social,
            'direccion': empresa.direccion, 'ambiente': empresa.ambiente,
            'obligado_contabilidad': empresa.obligado_contabilidad,
        },
        'cliente': {
            'razon_social': f.cliente.razon_social,
            'identificacion': f.cliente.identificacion,
            'tipo_identificacion': f.cliente.tipo_identificacion,
            'email': f.cliente.email or '', 'direccion': f.cliente.direccion or '',
        },
        'factura': {
            'numero': f.get_numero_formateado(), 'clave_acceso': f.clave_acceso,
            'fecha_emision': f.fecha_emision.strftime('%d/%m/%Y'),
            'subtotal_sin_impuesto': float(f.subtotal_sin_impuesto or 0),
            'subtotal_iva_0': float(f.subtotal_iva_0 or 0),
            'subtotal_iva_12': float(f.subtotal_iva_12 or 0),
            'iva_12': float(f.iva_12 or 0),
            'descuento_total': float(f.descuento_total or 0),
            'total': float(f.total or 0),
            'estado': f.estado,
            'numero_autorizacion': f.numero_autorizacion or '',
            'fecha_autorizacion': f.fecha_autorizacion.strftime('%d/%m/%Y %H:%M:%S') if f.fecha_autorizacion else '',
        },
        'detalles': [{
            'codigo': d.codigo_principal or '', 'descripcion': d.descripcion,
            'cantidad': float(d.cantidad), 'precio_unitario': float(d.precio_unitario),
            'descuento': float(d.descuento or 0),
            'subtotal': float(d.precio_total_sin_impuesto),
            'iva': float(d.impuesto_valor or 0),
        } for d in f.detalles],
    }


def _s(f):
    return {
        'id': f.id, 'empresa_id': f.empresa_id,
        'cliente_id': f.cliente_id,
        'cliente_nombre': f.cliente.razon_social if f.cliente else '',
        'cliente_identificacion': f.cliente.identificacion if f.cliente else '',
        'numero': f.numero,
        'numero_formateado': f.get_numero_formateado(),
        'clave_acceso': f.clave_acceso or '',
        'fecha_emision': f.fecha_emision.strftime('%Y-%m-%d'),
        'total': float(f.total or 0),
        'estado': f.estado,
        'numero_autorizacion': f.numero_autorizacion or '',
        'created_at': f.created_at.strftime('%Y-%m-%d %H:%M') if f.created_at else '',
    }


def _s_full(f):
    d = _s(f)
    d.update({
        'forma_pago': f.forma_pago or '01',
        'observacion': f.observacion or '',
        'subtotal_sin_impuesto': float(f.subtotal_sin_impuesto or 0),
        'subtotal_iva_0': float(f.subtotal_iva_0 or 0),
        'subtotal_iva_5': float(f.subtotal_iva_5 or 0),
        'subtotal_iva_12': float(f.subtotal_iva_12 or 0),
        'subtotal_iva_15': float(f.subtotal_iva_15 or 0),
        'iva_5': float(f.iva_5 or 0),
        'iva_12': float(f.iva_12 or 0),
        'iva_15': float(f.iva_15 or 0),
        'descuento_total': float(f.descuento_total or 0),
        'fecha_autorizacion': f.fecha_autorizacion.strftime('%Y-%m-%d %H:%M:%S') if f.fecha_autorizacion else '',
        'xml_path': f.xml_path or '',
        'xml_autorizado_path': f.xml_autorizado_path or '',
        'detalles': [{
            'id': d.id, 'producto_id': d.producto_id,
            'codigo_principal': d.codigo_principal or '',
            'descripcion': d.descripcion,
            'cantidad': float(d.cantidad),
            'precio_unitario': float(d.precio_unitario),
            'descuento': float(d.descuento or 0),
            'precio_total_sin_impuesto': float(d.precio_total_sin_impuesto),
            'impuesto_codigo': d.impuesto_codigo or '2',
            'impuesto_codigo_porcentaje': d.impuesto_codigo_porcentaje or '0',
            'impuesto_tarifa': float(d.impuesto_tarifa or 0),
            'impuesto_valor': float(d.impuesto_valor or 0),
        } for d in f.detalles],
    })
    return d
