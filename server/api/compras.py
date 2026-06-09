from datetime import datetime
from flask import Blueprint, request, jsonify
from ..database.db import db
from ..database.models import CompraProveedor, Proveedor

compras_bp = Blueprint('compras', __name__)


@compras_bp.route('/importar-xml', methods=['POST'])
def importar_xml():
    """
    Importa una o varias facturas de proveedores desde archivos XML del SRI.

    Acepta:
      - JSON: {"empresa_id": 1, "xmls": ["<?xml...", "<?xml..."]}
      - Form + file upload: campo 'xml_files' con múltiples archivos .xml

    Retorna lista de resultados por cada XML procesado.
    """
    from ..services.xml_parser import parsear_xml_comprobante

    empresa_id = None
    xmls = []

    # Caso 1: JSON con lista de strings XML
    if request.is_json:
        data = request.get_json()
        empresa_id = data.get('empresa_id')
        xmls = data.get('xmls', [])

    # Caso 2: multipart/form-data con archivos
    elif request.files:
        empresa_id = int(request.form.get('empresa_id', 0))
        for f in request.files.getlist('xml_files'):
            content = f.read().decode('utf-8', errors='replace')
            xmls.append(content)

    if not empresa_id:
        return jsonify({'ok': False, 'error': 'empresa_id requerido'}), 400
    if not xmls:
        return jsonify({'ok': False, 'error': 'No se proporcionaron XMLs'}), 400

    resultados = []
    importados = 0
    errores = 0

    for i, xml_content in enumerate(xmls):
        parsed = parsear_xml_comprobante(xml_content)

        if not parsed['ok']:
            errores += 1
            resultados.append({'index': i, 'ok': False, 'error': parsed['error']})
            continue

        # Verificar si ya existe por número de documento o clave de acceso
        existente = CompraProveedor.query.filter_by(
            empresa_id=empresa_id,
            numero_documento=parsed['numero_documento'],
        ).first()

        if existente:
            resultados.append({
                'index': i,
                'ok': False,
                'error': f'Documento {parsed["numero_documento"]} ya existe',
                'numero_documento': parsed['numero_documento'],
            })
            errores += 1
            continue

        # Buscar o crear proveedor por RUC
        proveedor = Proveedor.query.filter_by(
            empresa_id=empresa_id,
            identificacion=parsed['ruc_proveedor']
        ).first()

        if not proveedor:
            proveedor = Proveedor(
                empresa_id=empresa_id,
                tipo_identificacion='04' if len(parsed['ruc_proveedor']) == 13 else '05',
                identificacion=parsed['ruc_proveedor'],
                razon_social=parsed['razon_social_proveedor'],
            )
            db.session.add(proveedor)
            db.session.flush()

        c = CompraProveedor(
            empresa_id=empresa_id,
            proveedor_id=proveedor.id,
            tipo_documento=parsed['tipo_documento'],
            numero_documento=parsed['numero_documento'],
            numero_autorizacion=parsed['numero_autorizacion'],
            fecha_emision=parsed['fecha_emision'],
            ruc_proveedor=parsed['ruc_proveedor'],
            razon_social_proveedor=parsed['razon_social_proveedor'],
            subtotal_sin_iva=parsed['subtotal_sin_iva'],
            subtotal_iva_0=parsed['subtotal_iva_0'],
            subtotal_iva_12=parsed['subtotal_iva_12'],
            iva=parsed['iva'],
            total=parsed['total'],
            xml_content=xml_content,
        )
        db.session.add(c)
        db.session.flush()
        importados += 1
        resultados.append({
            'index': i,
            'ok': True,
            'id': c.id,
            'numero_documento': parsed['numero_documento'],
            'proveedor': parsed['razon_social_proveedor'],
            'total': parsed['total'],
            'tipo': parsed['tipo_nombre'],
        })

    db.session.commit()

    return jsonify({
        'ok': True,
        'importados': importados,
        'errores': errores,
        'resultados': resultados,
    })


@compras_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    q = request.args.get('q', '')
    query = CompraProveedor.query.filter_by(empresa_id=empresa_id)
    if q:
        query = query.join(Proveedor).filter(
            (Proveedor.razon_social.ilike(f'%{q}%')) |
            (Proveedor.identificacion.ilike(f'%{q}%')) |
            (CompraProveedor.numero_documento.ilike(f'%{q}%'))
        )
    items = query.order_by(CompraProveedor.fecha_emision.desc()).limit(200).all()
    return jsonify({'ok': True, 'data': [_s(c) for c in items]})


@compras_bp.route('/<int:id>', methods=['GET'])
def obtener(id):
    c = CompraProveedor.query.get_or_404(id)
    return jsonify({'ok': True, 'data': _s(c)})


@compras_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    c = CompraProveedor(
        empresa_id=data['empresa_id'],
        proveedor_id=data['proveedor_id'],
        tipo_documento=data.get('tipo_documento', '01'),
        numero_documento=data['numero_documento'].strip(),
        fecha_emision=datetime.strptime(data['fecha_emision'], '%Y-%m-%d').date(),
        subtotal=float(data.get('subtotal', 0)),
        iva=float(data.get('iva', 0)),
        total=float(data['total']),
        observacion=data.get('observacion', '').strip() or None,
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(c)}), 201


@compras_bp.route('/<int:id>', methods=['PUT'])
def actualizar(id):
    c = CompraProveedor.query.get_or_404(id)
    data = request.get_json()
    c.proveedor_id = data.get('proveedor_id', c.proveedor_id)
    c.tipo_documento = data.get('tipo_documento', c.tipo_documento)
    c.numero_documento = data.get('numero_documento', c.numero_documento).strip()
    c.fecha_emision = datetime.strptime(data['fecha_emision'], '%Y-%m-%d').date() if data.get('fecha_emision') else c.fecha_emision
    c.subtotal = float(data.get('subtotal', c.subtotal))
    c.iva = float(data.get('iva', c.iva))
    c.total = float(data.get('total', c.total))
    c.observacion = data.get('observacion', '').strip() or None
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(c)})


@compras_bp.route('/<int:id>', methods=['DELETE'])
def eliminar(id):
    c = CompraProveedor.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'ok': True})


def _s(c):
    return {
        'id': c.id, 'empresa_id': c.empresa_id, 'proveedor_id': c.proveedor_id,
        'proveedor_nombre': c.proveedor.razon_social if c.proveedor else '',
        'proveedor_identificacion': c.proveedor.identificacion if c.proveedor else '',
        'tipo_documento': c.tipo_documento,
        'numero_documento': c.numero_documento,
        'fecha_emision': c.fecha_emision.strftime('%Y-%m-%d'),
        'subtotal': float(c.subtotal or 0),
        'iva': float(c.iva or 0),
        'total': float(c.total or 0),
        'observacion': c.observacion or '',
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else '',
    }
