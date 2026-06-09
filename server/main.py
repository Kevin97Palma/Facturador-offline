from flask import Flask
from flask_cors import CORS
from .config import Config
from .database.db import db, init_db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)

    from .api.auth import auth_bp
    from .api.empresas import empresas_bp
    from .api.usuarios import usuarios_bp
    from .api.clientes import clientes_bp
    from .api.proveedores import proveedores_bp
    from .api.categorias import categorias_bp
    from .api.impuestos import impuestos_bp
    from .api.productos import productos_bp
    from .api.facturas import facturas_bp
    from .api.retenciones import retenciones_bp
    from .api.notas_credito import notas_credito_bp
    from .api.notas_debito import notas_debito_bp
    from .api.guias import guias_bp
    from .api.liquidaciones import liquidaciones_bp
    from .api.compras import compras_bp
    from .api.archivos import archivos_bp
    from .api.cloud import cloud_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(empresas_bp, url_prefix='/api/empresas')
    app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
    app.register_blueprint(clientes_bp, url_prefix='/api/clientes')
    app.register_blueprint(proveedores_bp, url_prefix='/api/proveedores')
    app.register_blueprint(categorias_bp, url_prefix='/api/categorias')
    app.register_blueprint(impuestos_bp, url_prefix='/api/impuestos')
    app.register_blueprint(productos_bp, url_prefix='/api/productos')
    app.register_blueprint(facturas_bp, url_prefix='/api/facturas')
    app.register_blueprint(retenciones_bp, url_prefix='/api/retenciones')
    app.register_blueprint(notas_credito_bp, url_prefix='/api/notas-credito')
    app.register_blueprint(notas_debito_bp, url_prefix='/api/notas-debito')
    app.register_blueprint(guias_bp, url_prefix='/api/guias')
    app.register_blueprint(liquidaciones_bp, url_prefix='/api/liquidaciones')
    app.register_blueprint(compras_bp, url_prefix='/api/compras')
    app.register_blueprint(archivos_bp, url_prefix='/api/archivos')
    app.register_blueprint(cloud_bp, url_prefix='/api/cloud')

    with app.app_context():
        init_db(app)

    return app


def run_server(host='0.0.0.0', port=5000):
    app = create_app()

    # Iniciar backup diario si hay configuración MySQL
    _iniciar_cloud(app)

    app.run(host=host, port=port, debug=False, threaded=True)


def _iniciar_cloud(app):
    """Inicia el scheduler de backup si la config MySQL está presente."""
    import json, os, logging
    log = logging.getLogger(__name__)
    base = os.path.dirname(os.path.dirname(__file__))
    cfg_path = os.path.join(base, 'config.json')
    if not os.path.exists(cfg_path):
        return
    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        required = ('mysql_host', 'mysql_user', 'mysql_password', 'mysql_database')
        if not all(cfg.get(k) for k in required):
            return
        from .services.cloud_backup import iniciar_scheduler
        hora = int(cfg.get('hora_backup', 2))
        iniciar_scheduler(app, cfg, hora_backup=hora)
        log.info(f'[Cloud] Backup diario configurado a las {hora:02d}:00')
    except Exception as e:
        log.warning(f'[Cloud] No se pudo iniciar backup: {e}')
