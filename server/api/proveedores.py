from flask import Blueprint, request, jsonify
from ..database.db import db
from ..database.models import Proveedor

proveedores_bp = Blueprint('proveedores', __name__)


@proveedores_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    q = request.args.get('q', '')
    query = Proveedor.query.filter_by(empresa_id=empresa_id, activo=True)
    if q:
        query = query.filter(
            (Proveedor.razon_social.ilike(f'%{q}%')) |
            (Proveedor.identificacion.ilike(f'%{q}%'))
        )
    return jsonify({'ok': True, 'data': [_s(p) for p in query.order_by(Proveedor.razon_social).all()]})


@proveedores_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    p = Proveedor(
        empresa_id=data['empresa_id'],
        tipo_identificacion=data.get('tipo_identificacion', '04'),
        identificacion=data['identificacion'].strip(),
        razon_social=data['razon_social'].strip(),
        email=data.get('email', '').strip() or None,
        telefono=data.get('telefono', '').strip() or None,
        direccion=data.get('direccion', '').strip() or None,
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(p)}), 201


@proveedores_bp.route('/<int:id>', methods=['PUT'])
def actualizar(id):
    p = Proveedor.query.get_or_404(id)
    data = request.get_json()
    p.tipo_identificacion = data.get('tipo_identificacion', p.tipo_identificacion)
    p.identificacion = data.get('identificacion', p.identificacion).strip()
    p.razon_social = data.get('razon_social', p.razon_social).strip()
    p.email = data.get('email', '').strip() or None
    p.telefono = data.get('telefono', '').strip() or None
    p.direccion = data.get('direccion', '').strip() or None
    if data.get('activo') is not None:
        p.activo = data['activo']
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(p)})


@proveedores_bp.route('/<int:id>', methods=['DELETE'])
def eliminar(id):
    p = Proveedor.query.get_or_404(id)
    p.activo = False
    db.session.commit()
    return jsonify({'ok': True})


def _s(p):
    return {
        'id': p.id, 'empresa_id': p.empresa_id,
        'tipo_identificacion': p.tipo_identificacion,
        'identificacion': p.identificacion,
        'razon_social': p.razon_social,
        'email': p.email or '', 'telefono': p.telefono or '',
        'direccion': p.direccion or '', 'activo': p.activo,
    }
