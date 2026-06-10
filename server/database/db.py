from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()
        _seed_superadmin()


def _seed_superadmin():
    from .models import Empresa, Usuario
    if Usuario.query.filter_by(rol='superadmin').first():
        return
    empresa = Empresa(
        ruc='9999999999999',
        razon_social='ADMINISTRADOR DEL SISTEMA',
        direccion='Sistema Local',
        establecimiento='001',
        punto_emision='001',
        ambiente=1,
    )
    db.session.add(empresa)
    db.session.flush()
    admin = Usuario(
        empresa_id=empresa.id,
        nombre='Super',
        apellido='Admin',
        email='admin@sistema.com',
        rol='superadmin',
    )
    admin.set_password('Admin2024#')
    db.session.add(admin)
    db.session.commit()
