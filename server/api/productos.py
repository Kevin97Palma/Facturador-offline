from flask import Blueprint, request, jsonify
from ..database.db import db
from ..database.models import Producto

productos_bp = Blueprint('productos', __name__)


@productos_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    q = request.args.get('q', '')
    query = Producto.query.filter_by(empresa_id=empresa_id, activo=True)
    if q:
        query = query.filter(
            (Producto.nombre.ilike(f'%{q}%')) | (Producto.codigo.ilike(f'%{q}%'))
        )
    return jsonify({'ok': True, 'data': [_s(p) for p in query.order_by(Producto.nombre).all()]})


@productos_bp.route('/codigo/<int:empresa_id>/<codigo>', methods=['GET'])
def buscar_por_codigo(empresa_id, codigo):
    """Para lectores de código de barras."""
    p = Producto.query.filter_by(empresa_id=empresa_id, codigo=codigo, activo=True).first()
    if not p:
        return jsonify({'ok': False, 'error': 'Producto no encontrado'}), 404
    return jsonify({'ok': True, 'data': _s(p)})


@productos_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    p = Producto(
        empresa_id=data['empresa_id'],
        categoria_id=data.get('categoria_id') or None,
        impuesto_id=data.get('impuesto_id') or None,
        codigo=data['codigo'].strip(),
        nombre=data['nombre'].strip(),
        descripcion=data.get('descripcion', '').strip() or None,
        precio_unitario=float(data.get('precio_unitario', 0)),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(p)}), 201


@productos_bp.route('/<int:id>', methods=['PUT'])
def actualizar(id):
    p = Producto.query.get_or_404(id)
    data = request.get_json()
    p.categoria_id = data.get('categoria_id') or None
    p.impuesto_id = data.get('impuesto_id') or None
    p.codigo = data.get('codigo', p.codigo).strip()
    p.nombre = data.get('nombre', p.nombre).strip()
    p.descripcion = data.get('descripcion', '').strip() or None
    p.precio_unitario = float(data.get('precio_unitario', p.precio_unitario))
    if data.get('activo') is not None:
        p.activo = data['activo']
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(p)})


@productos_bp.route('/<int:id>', methods=['DELETE'])
def eliminar(id):
    p = Producto.query.get_or_404(id)
    p.activo = False
    db.session.commit()
    return jsonify({'ok': True})


def _s(p):
    return {
        'id': p.id, 'empresa_id': p.empresa_id,
        'categoria_id': p.categoria_id,
        'impuesto_id': p.impuesto_id,
        'codigo': p.codigo, 'nombre': p.nombre,
        'descripcion': p.descripcion or '',
        'precio_unitario': float(p.precio_unitario),
        'impuesto_codigo': p.impuesto.codigo if p.impuesto else '2',
        'impuesto_codigo_porcentaje': p.impuesto.codigo_porcentaje if p.impuesto else '0',
        'impuesto_tarifa': float(p.impuesto.porcentaje) if p.impuesto else 0,
        'activo': p.activo,
    }
