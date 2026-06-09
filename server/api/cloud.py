"""
Endpoints de administración cloud: backup manual, estado de licencia,
y configuración de la conexión MySQL.
"""
from flask import Blueprint, request, jsonify, current_app
from ..database.db import db

cloud_bp = Blueprint('cloud', __name__)


def _get_cloud_cfg():
    """Lee la configuración MySQL desde el archivo config.json de la app."""
    import json, os
    base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    cfg_path = os.path.join(base, 'config.json')
    if not os.path.exists(cfg_path):
        return None
    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    required = ('mysql_host', 'mysql_user', 'mysql_password', 'mysql_database')
    if not all(cfg.get(k) for k in required):
        return None
    return cfg


# ─── Estado del backup ────────────────────────────────────────────────────────

@cloud_bp.route('/backup/estado', methods=['GET'])
def estado_backup():
    """Devuelve el estado del último backup ejecutado."""
    from ..services.cloud_backup import get_last_result
    result = get_last_result()
    cfg = _get_cloud_cfg()
    return jsonify({
        'ok': True,
        'configurado': cfg is not None,
        'ultimo_backup': result,
    })


@cloud_bp.route('/backup/ejecutar', methods=['POST'])
def ejecutar_backup():
    """Dispara un backup manual inmediato hacia MySQL."""
    cfg = _get_cloud_cfg()
    if not cfg:
        return jsonify({
            'ok': False,
            'error': 'MySQL no configurado. Agregue mysql_host, mysql_user, '
                     'mysql_password y mysql_database en config.json'
        }), 400

    from ..services.cloud_backup import ejecutar_backup as _backup
    app = current_app._get_current_object()
    result = _backup(app, cfg)
    return jsonify(result), 200 if result['ok'] else 422


# ─── Licencia ─────────────────────────────────────────────────────────────────

@cloud_bp.route('/licencia/<string:ruc>', methods=['GET'])
def verificar_licencia(ruc):
    """
    Verifica la licencia de la empresa con el RUC indicado.
    Usa MySQL si hay conexión, caché local si no.
    """
    cfg = _get_cloud_cfg()
    if not cfg:
        return jsonify({
            'ok': False,
            'valida': False,
            'error': 'Cloud no configurado',
            'modo': 'sin_config',
        })

    from ..services.license_service import verificar_licencia as _verificar
    result = _verificar(ruc, cfg, db)
    return jsonify({'ok': True, **result})


@cloud_bp.route('/licencia/<string:ruc>/registrar-equipo', methods=['POST'])
def registrar_equipo(ruc):
    """
    Registra el equipo actual en la nube y verifica que no se exceda
    el límite de equipos de la licencia.
    """
    cfg = _get_cloud_cfg()
    if not cfg:
        return jsonify({'ok': True, 'permitido': True, 'modo': 'sin_config'})

    from ..services.license_service import registrar_equipo as _reg
    permitido = _reg(ruc, cfg)
    return jsonify({
        'ok': True,
        'permitido': permitido,
        'mensaje': 'Equipo registrado' if permitido else 'Límite de equipos alcanzado',
    })


# ─── Configuración MySQL ──────────────────────────────────────────────────────

@cloud_bp.route('/config', methods=['GET'])
def obtener_config():
    """Devuelve la configuración MySQL (sin la contraseña)."""
    cfg = _get_cloud_cfg()
    if not cfg:
        return jsonify({'ok': True, 'configurado': False, 'config': {}})
    return jsonify({
        'ok': True,
        'configurado': True,
        'config': {
            'mysql_host': cfg.get('mysql_host', ''),
            'mysql_port': cfg.get('mysql_port', 3306),
            'mysql_user': cfg.get('mysql_user', ''),
            'mysql_database': cfg.get('mysql_database', ''),
            'hora_backup': cfg.get('hora_backup', 2),
        }
    })


@cloud_bp.route('/config', methods=['POST'])
def guardar_config():
    """
    Guarda la configuración MySQL en config.json.
    Prueba la conexión antes de guardar.
    """
    import json, os
    data = request.get_json()

    required = ('mysql_host', 'mysql_user', 'mysql_password', 'mysql_database')
    if not all(data.get(k) for k in required):
        return jsonify({'ok': False, 'error': 'Faltan campos requeridos'}), 400

    # Probar conexión antes de guardar
    try:
        import pymysql
        conn = pymysql.connect(
            host=data['mysql_host'],
            port=int(data.get('mysql_port', 3306)),
            user=data['mysql_user'],
            password=data['mysql_password'],
            database=data['mysql_database'],
            charset='utf8mb4',
            connect_timeout=8,
        )
        conn.close()
    except Exception as e:
        return jsonify({'ok': False, 'error': f'No se pudo conectar: {e}'}), 422

    # Guardar en config.json
    base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    cfg_path = os.path.join(base, 'config.json')
    try:
        existing = {}
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        existing.update({
            'mysql_host': data['mysql_host'],
            'mysql_port': int(data.get('mysql_port', 3306)),
            'mysql_user': data['mysql_user'],
            'mysql_password': data['mysql_password'],
            'mysql_database': data['mysql_database'],
            'hora_backup': int(data.get('hora_backup', 2)),
        })
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
    except Exception as e:
        return jsonify({'ok': False, 'error': f'Error al guardar: {e}'}), 500

    return jsonify({'ok': True, 'mensaje': 'Configuración guardada y conexión verificada'})
