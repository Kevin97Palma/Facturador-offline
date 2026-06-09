import os
from flask import Blueprint, request, jsonify, current_app, send_file
from ..database.db import db
from ..database.models import Empresa
from ..config import FIRMAS_DIR, LOGOS_DIR

empresas_bp = Blueprint('empresas', __name__)


@empresas_bp.route('/', methods=['GET'])
def listar():
    empresas = Empresa.query.filter(Empresa.ruc != '9999999999999').all()
    return jsonify({'ok': True, 'data': [_serialize(e) for e in empresas]})


@empresas_bp.route('/<int:id>', methods=['GET'])
def obtener(id):
    e = Empresa.query.get_or_404(id)
    return jsonify({'ok': True, 'data': _serialize(e)})


@empresas_bp.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    e = Empresa(
        ruc=data['ruc'].strip(),
        razon_social=data['razon_social'].strip(),
        nombre_comercial=data.get('nombre_comercial', '').strip() or None,
        direccion=data['direccion'].strip(),
        telefono=data.get('telefono', '').strip() or None,
        email=data.get('email', '').strip() or None,
        establecimiento=data.get('establecimiento', '001').zfill(3),
        punto_emision=data.get('punto_emision', '001').zfill(3),
        ambiente=int(data.get('ambiente', 1)),
        obligado_contabilidad=data.get('obligado_contabilidad', False),
        agente_retencion=data.get('agente_retencion', False),
        contribuyente_especial=data.get('contribuyente_especial', False),
        num_resolucion_contrib_especial=data.get('num_resolucion_contrib_especial', '').strip() or None,
        contribuyente_rimpe=data.get('contribuyente_rimpe', False),
        texto_regimen=data.get('texto_regimen', '').strip() or None,
        clave_firma=data.get('clave_firma', '').strip() or None,
        fe_url=data.get('fe_url', '').strip().rstrip('/') or None,
        pdf_url=data.get('pdf_url', '').strip().rstrip('/') or None,
    )
    db.session.add(e)
    db.session.commit()
    return jsonify({'ok': True, 'data': _serialize(e)}), 201


@empresas_bp.route('/<int:id>', methods=['PUT'])
def actualizar(id):
    e = Empresa.query.get_or_404(id)
    data = request.get_json()
    e.ruc = data.get('ruc', e.ruc).strip()
    e.razon_social = data.get('razon_social', e.razon_social).strip()
    e.nombre_comercial = data.get('nombre_comercial', '').strip() or None
    e.direccion = data.get('direccion', e.direccion).strip()
    e.telefono = data.get('telefono', '').strip() or None
    e.email = data.get('email', '').strip() or None
    e.establecimiento = data.get('establecimiento', e.establecimiento).zfill(3)
    e.punto_emision = data.get('punto_emision', e.punto_emision).zfill(3)
    e.ambiente = int(data.get('ambiente', e.ambiente))
    e.obligado_contabilidad = data.get('obligado_contabilidad', e.obligado_contabilidad)
    e.agente_retencion = data.get('agente_retencion', e.agente_retencion)
    e.contribuyente_especial = data.get('contribuyente_especial', e.contribuyente_especial)
    e.num_resolucion_contrib_especial = data.get('num_resolucion_contrib_especial', '').strip() or None
    e.contribuyente_rimpe = data.get('contribuyente_rimpe', e.contribuyente_rimpe)
    e.texto_regimen = data.get('texto_regimen', '').strip() or None
    e.clave_firma = data.get('clave_firma', e.clave_firma or '').strip() or None
    e.fe_url = data.get('fe_url', e.fe_url or '').strip().rstrip('/') or None
    e.pdf_url = data.get('pdf_url', e.pdf_url or '').strip().rstrip('/') or None
    if 'activo' in data:
        e.activo = data['activo']
    db.session.commit()
    return jsonify({'ok': True, 'data': _serialize(e)})


@empresas_bp.route('/<int:id>/firma', methods=['POST'])
def subir_firma(id):
    e = Empresa.query.get_or_404(id)
    if 'firma' not in request.files:
        return jsonify({'ok': False, 'error': 'No se envió archivo'}), 400
    f = request.files['firma']
    ext = f.filename.rsplit('.', 1)[-1].lower()
    if ext not in ('p12', 'pfx'):
        return jsonify({'ok': False, 'error': 'Solo se permiten archivos .p12 o .pfx'}), 400
    filename = f'firma_{e.ruc}.{ext}'
    f.save(os.path.join(FIRMAS_DIR, filename))
    e.nombre_archivo_firma = filename
    db.session.commit()
    return jsonify({'ok': True, 'nombre': filename})


@empresas_bp.route('/<int:id>/logo', methods=['POST'])
def subir_logo(id):
    e = Empresa.query.get_or_404(id)
    if 'logo' not in request.files:
        return jsonify({'ok': False, 'error': 'No se envió archivo'}), 400
    f = request.files['logo']
    ext = f.filename.rsplit('.', 1)[-1].lower()
    if ext not in ('png', 'jpg', 'jpeg'):
        return jsonify({'ok': False, 'error': 'Solo PNG o JPG'}), 400
    filename = f'logo_{e.ruc}.{ext}'
    f.save(os.path.join(LOGOS_DIR, filename))
    e.logo_path = filename
    db.session.commit()
    return jsonify({'ok': True, 'nombre': filename})


def _serialize(e):
    return {
        'id': e.id,
        'ruc': e.ruc,
        'razon_social': e.razon_social,
        'nombre_comercial': e.nombre_comercial or '',
        'direccion': e.direccion,
        'telefono': e.telefono or '',
        'email': e.email or '',
        'establecimiento': e.establecimiento,
        'punto_emision': e.punto_emision,
        'ambiente': e.ambiente,
        'obligado_contabilidad': e.obligado_contabilidad,
        'agente_retencion': e.agente_retencion,
        'contribuyente_especial': e.contribuyente_especial,
        'num_resolucion_contrib_especial': e.num_resolucion_contrib_especial or '',
        'contribuyente_rimpe': e.contribuyente_rimpe,
        'texto_regimen': e.texto_regimen or '',
        'nombre_archivo_firma': e.nombre_archivo_firma or '',
        'clave_firma': e.clave_firma or '',
        'logo_path': e.logo_path or '',
        'fe_url': e.fe_url or '',
        'pdf_url': e.pdf_url or '',
        'activo': e.activo,
    }
