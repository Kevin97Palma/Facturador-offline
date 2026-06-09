from flask import Blueprint, request, jsonify
from ..database.db import db
from ..database.models import Impuesto

impuestos_bp = Blueprint('impuestos', __name__)


@impuestos_bp.route('/<int:empresa_id>', methods=['GET'])
def listar(empresa_id):
    imps = Impuesto.query.filter_by(empresa_id=empresa_id, activo=True).order_by(Impuesto.porcentaje).all()
    return jsonify({'ok': True, 'data': [_s(i) for i in imps]})


@impuestos_bp.route('/inicializar/<int:empresa_id>', methods=['POST'])
def inicializar(empresa_id):
    """Crea los impuestos estándar SRI para una empresa nueva."""
    defecto = [
        ('IVA 0%', '2', '0', 0),
        ('IVA 5%', '2', '5', 5),
        ('IVA 12%', '2', '2', 12),
        ('IVA 15%', '2', '4', 15),
        ('No objeto IVA', '2', '6', 0),
        ('Exento IVA', '2', '7', 0),
    ]
    creados = []
    for nombre, codigo, cod_porc, porcentaje in defecto:
        if not Impuesto.query.filter_by(empresa_id=empresa_id, codigo_porcentaje=cod_porc).first():
            imp = Impuesto(empresa_id=empresa_id, nombre=nombre,
                          codigo=codigo, codigo_porcentaje=cod_porc, porcentaje=porcentaje)
            db.session.add(imp)
            creados.append(nombre)
    db.session.commit()
    return jsonify({'ok': True, 'creados': creados})


@impuestos_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    imp = Impuesto(
        empresa_id=data['empresa_id'],
        nombre=data['nombre'].strip(),
        codigo=data.get('codigo', '2'),
        codigo_porcentaje=data['codigo_porcentaje'],
        porcentaje=float(data['porcentaje']),
    )
    db.session.add(imp)
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(imp)}), 201


@impuestos_bp.route('/<int:id>', methods=['PUT'])
def actualizar(id):
    imp = Impuesto.query.get_or_404(id)
    data = request.get_json()
    imp.nombre = data.get('nombre', imp.nombre).strip()
    imp.codigo = data.get('codigo', imp.codigo)
    imp.codigo_porcentaje = data.get('codigo_porcentaje', imp.codigo_porcentaje)
    imp.porcentaje = float(data.get('porcentaje', imp.porcentaje))
    if data.get('activo') is not None:
        imp.activo = data['activo']
    db.session.commit()
    return jsonify({'ok': True, 'data': _s(imp)})


def _s(i):
    return {'id': i.id, 'empresa_id': i.empresa_id, 'nombre': i.nombre,
            'codigo': i.codigo, 'codigo_porcentaje': i.codigo_porcentaje,
            'porcentaje': float(i.porcentaje), 'activo': i.activo}
