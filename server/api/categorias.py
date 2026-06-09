from flask import Blueprint, request, jsonify
from ..database.db import db
from ..database.models import Categoria

categorias_bp = Blueprint('categorias', __name__)


@categorias_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    cats = Categoria.query.filter_by(empresa_id=empresa_id, activo=True).order_by(Categoria.nombre).all()
    return jsonify({'ok': True, 'data': [_s(c) for c in cats]})


@categorias_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    c = Categoria(empresa_id=data['empresa_id'], nombre=data['nombre'].strip(),
                  descripcion=data.get('descripcion', '').strip() or None)
    db.session.add(c)
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(c)}), 201


@categorias_bp.route('/<int:id>', methods=['PUT'])
def actualizar(id):
    c = Categoria.query.get_or_404(id)
    data = request.get_json()
    c.nombre = data.get('nombre', c.nombre).strip()
    c.descripcion = data.get('descripcion', '').strip() or None
    if data.get('activo') is not None:
        c.activo = data['activo']
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(c)})


@categorias_bp.route('/<int:id>', methods=['DELETE'])
def eliminar(id):
    c = Categoria.query.get_or_404(id)
    c.activo = False
    db.session.commit()
    return jsonify({'ok': True})


def _s(c):
    return {'id': c.id, 'empresa_id': c.empresa_id,
            'nombre': c.nombre, 'descripcion': c.descripcion or '', 'activo': c.activo}
