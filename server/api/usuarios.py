from flask import Blueprint, request, jsonify
from ..database.db import db
from ..database.models import Usuario

usuarios_bp = Blueprint('usuarios', __name__)


@usuarios_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    usuarios = Usuario.query.filter_by(empresa_id=empresa_id).all()
    return jsonify({'ok': True, 'data': [_s(u) for u in usuarios]})


@usuarios_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    email = data['email'].strip().lower()
    if Usuario.query.filter_by(email=email).first():
        return jsonify({'ok': False, 'error': 'El email ya existe'}), 409
    u = Usuario(
        empresa_id=data['empresa_id'],
        nombre=data['nombre'].strip(),
        apellido=data['apellido'].strip(),
        email=email,
        rol=data.get('rol', 'vendedor'),
    )
    u.set_password(data['password'])
    db.session.add(u)
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(u)}), 201


@usuarios_bp.route('/<int:id>', methods=['PUT'])
def actualizar(id):
    u = Usuario.query.get_or_404(id)
    data = request.get_json()
    u.nombre = data.get('nombre', u.nombre).strip()
    u.apellido = data.get('apellido', u.apellido).strip()
    u.rol = data.get('rol', u.rol)
    if data.get('activo') is not None:
        u.activo = data['activo']
    if data.get('password'):
        u.set_password(data['password'])
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(u)})


def _s(u):
    return {
        'id': u.id,
        'empresa_id': u.empresa_id,
        'nombre': u.nombre,
        'apellido': u.apellido,
        'email': u.email,
        'rol': u.rol,
        'activo': u.activo,
    }
