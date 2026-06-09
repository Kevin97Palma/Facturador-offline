from flask import Blueprint, request, jsonify
from ..database.db import db
from ..database.models import Cliente

clientes_bp = Blueprint('clientes', __name__)


@clientes_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    q = request.args.get('q', '')
    query = Cliente.query.filter_by(empresa_id=empresa_id, activo=True)
    if q:
        query = query.filter(
            (Cliente.razon_social.ilike(f'%{q}%')) |
            (Cliente.identificacion.ilike(f'%{q}%'))
        )
    return jsonify({'ok': True, 'data': [_s(c) for c in query.order_by(Cliente.razon_social).all()]})


@clientes_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    c = Cliente(
        empresa_id=data['empresa_id'],
        tipo_identificacion=data.get('tipo_identificacion', '05'),
        identificacion=data['identificacion'].strip(),
        razon_social=data['razon_social'].strip(),
        email=data.get('email', '').strip() or None,
        telefono=data.get('telefono', '').strip() or None,
        direccion=data.get('direccion', '').strip() or None,
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(c)}), 201


@clientes_bp.route('/<int:id>', methods=['PUT'])
def actualizar(id):
    c = Cliente.query.get_or_404(id)
    data = request.get_json()
    c.tipo_identificacion = data.get('tipo_identificacion', c.tipo_identificacion)
    c.identificacion = data.get('identificacion', c.identificacion).strip()
    c.razon_social = data.get('razon_social', c.razon_social).strip()
    c.email = data.get('email', '').strip() or None
    c.telefono = data.get('telefono', '').strip() or None
    c.direccion = data.get('direccion', '').strip() or None
    if data.get('activo') is not None:
        c.activo = data['activo']
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(c)})


@clientes_bp.route('/<int:id>', methods=['DELETE'])
def eliminar(id):
    c = Cliente.query.get_or_404(id)
    c.activo = False
    db.session.commit()
    return jsonify({'ok': True})


def _s(c):
    return {
        'id': c.id, 'empresa_id': c.empresa_id,
        'tipo_identificacion': c.tipo_identificacion,
        'identificacion': c.identificacion,
        'razon_social': c.razon_social,
        'email': c.email or '', 'telefono': c.telefono or '',
        'direccion': c.direccion or '', 'activo': c.activo,
    }
