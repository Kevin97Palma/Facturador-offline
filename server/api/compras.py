from datetime import datetime
from flask import Blueprint, request, jsonify
from ..database.db import db
from ..database.models import CompraProveedor, Proveedor

compras_bp = Blueprint('compras', __name__)


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
