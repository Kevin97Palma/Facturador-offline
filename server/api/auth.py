from flask import Blueprint, request, jsonify, session
from ..database.db import db
from ..database.models import Usuario, Empresa

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    usuario = Usuario.query.filter_by(email=email, activo=True).first()
    if not usuario or not usuario.check_password(password):
        return jsonify({'ok': False, 'error': 'Credenciales incorrectas'}), 401
    empresa = Empresa.query.get(usuario.empresa_id)
    return jsonify({
        'ok': True,
        'usuario': {
            'id': usuario.id,
            'nombre': usuario.nombre_completo(),
            'email': usuario.email,
            'rol': usuario.rol,
            'empresa_id': usuario.empresa_id,
            'empresa_ruc': empresa.ruc if empresa else '',
            'empresa_nombre': empresa.razon_social if empresa else '',
        }
    })


@auth_bp.route('/empresas', methods=['GET'])
def listar_empresas_login():
    """Para que el superadmin elija empresa al iniciar sesión."""
    token = request.headers.get('X-User-Rol', '')
    if token != 'superadmin':
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    empresas = Empresa.query.filter(
        Empresa.activo == True,
        Empresa.ruc != '9999999999999'
    ).all()
    return jsonify({'ok': True, 'empresas': [
        {'id': e.id, 'ruc': e.ruc, 'razon_social': e.razon_social}
        for e in empresas
    ]})
