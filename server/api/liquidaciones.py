from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from ..database.db import db
from ..database.models import LiquidacionCompra, DetalleLiquidacion, Proveedor, Empresa
from ..services.clave_acceso import generar_clave_acceso
from ..services.xml_generator import generar_xml_liquidacion
from ..services.sri_service import procesar_documento, generar_pdf
from ..config import BASE_DIR
import os

liquidaciones_bp = Blueprint('liquidaciones', __name__)


def _siguiente_numero(empresa_id):
    from sqlalchemy import func
    ultimo = db.session.query(func.max(LiquidacionCompra.numero)).filter_by(empresa_id=empresa_id).scalar()
    return (ultimo or 0) + 1


@liquidaciones_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    q = request.args.get('q', '')
    query = LiquidacionCompra.query.filter_by(empresa_id=empresa_id)
    if q:
        query = query.join(Proveedor).filter(
            (Proveedor.razon_social.ilike(f'%{q}%')) |
            (Proveedor.identificacion.ilike(f'%{q}%'))
        )
    items = query.order_by(LiquidacionCompra.created_at.desc()).limit(200).all()
    return jsonify({'ok': True, 'data': [_s(l) for l in items]})


@liquidaciones_bp.route('/<int:id>', methods=['GET'])
def obtener(id):
    l = LiquidacionCompra.query.get_or_404(id)
    return jsonify({'ok': True, 'data': _s_full(l)})


@liquidaciones_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    empresa_id = data['empresa_id']
    empresa = Empresa.query.get(empresa_id)

    numero = _siguiente_numero(empresa_id)
    fecha_emision = datetime.strptime(data['fecha_emision'], '%Y-%m-%d').date()
    clave = generar_clave_acceso(
        fecha_emision, 'liquidacion', empresa.ruc,
        empresa.ambiente, empresa.establecimiento, empresa.punto_emision, numero
    )

    l = LiquidacionCompra(
        empresa_id=empresa_id,
        usuario_id=data['usuario_id'],
        proveedor_id=data['proveedor_id'],
        numero=numero,
        clave_acceso=clave,
        fecha_emision=fecha_emision,
        forma_pago=data.get('forma_pago', '01'),
        observacion=data.get('observacion', '').strip() or None,
    )
    db.session.add(l)
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

        d = DetalleLiquidacion(
            liquidacion_id=l.id,
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

    l.subtotal_sin_impuesto = round(sub0 + sub5 + sub12 + sub15, 2)
    l.iva_total = round(iva5 + iva12 + iva15, 2)
    l.total = round(l.subtotal_sin_impuesto + l.iva_total, 2)
    db.session.commit()
    return jsonify({'ok': True, 'data': _s_full(l)}), 201


@liquidaciones_bp.route('/<int:id>/autorizar', methods=['POST'])
def autorizar(id):
    l = LiquidacionCompra.query.get_or_404(id)
    if l.estado == 'AUTORIZADO':
        return jsonify({'ok': False, 'error': 'Ya está autorizada'}), 400

    empresa = Empresa.query.get(l.empresa_id)
    proveedor = Proveedor.query.get(l.proveedor_id)
    xml = generar_xml_liquidacion(empresa, proveedor, l, l.detalles)
    resultado = procesar_documento(empresa, xml, 'LC', l.clave_acceso, BASE_DIR)

    if resultado['ok']:
        l.estado = 'AUTORIZADO'
        l.numero_autorizacion = resultado['numero_autorizacion']
        if resultado.get('fecha_autorizacion'):
            try:
                l.fecha_autorizacion = datetime.fromisoformat(
                    resultado['fecha_autorizacion'].replace('-05:00', ''))
            except Exception:
                l.fecha_autorizacion = datetime.utcnow()
        l.xml_path = resultado.get('xml_firmado_path')
        l.xml_autorizado_path = resultado.get('xml_autorizado_path')
        db.session.commit()
        return jsonify({'ok': True, 'data': _s_full(l)})
    else:
        l.estado = 'NO_AUTORIZADO'
        db.session.commit()
        return jsonify({'ok': False, 'error': resultado['error']}), 422


@liquidaciones_bp.route('/<int:id>/xml', methods=['GET'])
def descargar_xml(id):
    l = LiquidacionCompra.query.get_or_404(id)
    ruta = l.xml_autorizado_path or l.xml_path
    if ruta and os.path.exists(ruta):
        return send_file(ruta, as_attachment=True, download_name=f'{l.clave_acceso}.xml')
    empresa = Empresa.query.get(l.empresa_id)
    proveedor = Proveedor.query.get(l.proveedor_id)
    xml = generar_xml_liquidacion(empresa, proveedor, l, l.detalles)
    from io import BytesIO
    return send_file(BytesIO(xml.encode('utf-8')), as_attachment=True,
                     download_name=f'{l.clave_acceso}.xml', mimetype='application/xml')


@liquidaciones_bp.route('/<int:id>/pdf', methods=['GET'])
def descargar_pdf(id):
    l = LiquidacionCompra.query.get_or_404(id)
    empresa = Empresa.query.get(l.empresa_id)
    if not empresa.pdf_url:
        return jsonify({'ok': False, 'error': 'URL del servicio PDF no configurada'}), 400
    datos = {
        'empresa': {'ruc': empresa.ruc, 'razon_social': empresa.razon_social},
        'proveedor': {
            'razon_social': l.proveedor.razon_social,
            'identificacion': l.proveedor.identificacion,
        },
        'liquidacion': {
            'numero': l.get_numero_formateado(), 'clave_acceso': l.clave_acceso,
            'fecha_emision': l.fecha_emision.strftime('%d/%m/%Y'),
            'subtotal_sin_impuesto': float(l.subtotal_sin_impuesto or 0),
            'iva_total': float(l.iva_total or 0), 'total': float(l.total or 0),
            'estado': l.estado, 'numero_autorizacion': l.numero_autorizacion or '',
        },
        'detalles': [{
            'codigo': d.codigo_principal or '', 'descripcion': d.descripcion,
            'cantidad': float(d.cantidad), 'precio_unitario': float(d.precio_unitario),
            'descuento': float(d.descuento or 0),
            'subtotal': float(d.precio_total_sin_impuesto),
            'iva': float(d.impuesto_valor or 0),
        } for d in l.detalles],
    }
    resultado = generar_pdf(empresa.pdf_url, 'liquidacion', datos)
    if resultado['ok']:
        from io import BytesIO
        return send_file(BytesIO(resultado['content']), as_attachment=True,
                         download_name=f'RIDE_{l.clave_acceso}.pdf', mimetype='application/pdf')
    return jsonify({'ok': False, 'error': resultado['error']}), 422


def _s(l):
    return {
        'id': l.id, 'empresa_id': l.empresa_id, 'proveedor_id': l.proveedor_id,
        'proveedor_nombre': l.proveedor.razon_social if l.proveedor else '',
        'numero': l.numero, 'numero_formateado': l.get_numero_formateado(),
        'clave_acceso': l.clave_acceso or '',
        'fecha_emision': l.fecha_emision.strftime('%Y-%m-%d'),
        'total': float(l.total or 0),
        'estado': l.estado, 'numero_autorizacion': l.numero_autorizacion or '',
        'created_at': l.created_at.strftime('%Y-%m-%d %H:%M') if l.created_at else '',
    }


def _s_full(l):
    d = _s(l)
    d.update({
        'forma_pago': l.forma_pago or '01', 'observacion': l.observacion or '',
        'subtotal_sin_impuesto': float(l.subtotal_sin_impuesto or 0),
        'iva_total': float(l.iva_total or 0),
        'fecha_autorizacion': l.fecha_autorizacion.strftime('%Y-%m-%d %H:%M:%S') if l.fecha_autorizacion else '',
        'xml_path': l.xml_path or '', 'xml_autorizado_path': l.xml_autorizado_path or '',
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
        } for det in l.detalles],
    })
    return d
