"""
Servicio de respaldo diario a MySQL en la nube.

Sincroniza todos los datos de la base SQLite local hacia una base MySQL remota.
Cada equipo identifica sus registros con el campo source_pc (nombre del PC).
"""
import os
import socket
import logging
import threading
import time
from datetime import datetime, date

log = logging.getLogger(__name__)

# Nombre del equipo para identificar el origen de los datos
PC_NAME = socket.gethostname()


def _get_mysql_conn(cfg: dict):
    """
    Crea y devuelve una conexión PyMySQL.
    cfg debe tener: host, port, user, password, database
    """
    import pymysql
    return pymysql.connect(
        host=cfg['mysql_host'],
        port=int(cfg.get('mysql_port', 3306)),
        user=cfg['mysql_user'],
        password=cfg['mysql_password'],
        database=cfg['mysql_database'],
        charset='utf8mb4',
        autocommit=False,
        connect_timeout=10,
    )


def _val(v):
    """Convierte tipos Python a valores seguros para MySQL."""
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if v is None:
        return None
    return v


# ─── Tablas que se respaldan ──────────────────────────────────────────────────

def _backup_table(cursor, model_class, empresa_id: int):
    """
    Respalda todos los registros de una tabla SQLAlchemy en MySQL.
    Usa INSERT ... ON DUPLICATE KEY UPDATE para ser idempotente.
    """
    from ..database.db import db

    records = model_class.query.filter_by(empresa_id=empresa_id).all()
    if not records:
        return 0

    table_name = f'bk_{model_class.__tablename__}'
    cols = [c.name for c in model_class.__table__.columns]

    # Agregar columnas de metadatos de respaldo
    extra_cols = ['source_pc', 'backup_at']
    all_cols = cols + extra_cols

    placeholders = ', '.join(['%s'] * len(all_cols))
    col_names = ', '.join(f'`{c}`' for c in all_cols)
    updates = ', '.join(
        f'`{c}`=VALUES(`{c}`)' for c in all_cols
        if c not in ('id', 'source_pc')
    )

    sql = (
        f'INSERT INTO `{table_name}` ({col_names}) VALUES ({placeholders}) '
        f'ON DUPLICATE KEY UPDATE {updates}'
    )

    count = 0
    for rec in records:
        row = [_val(getattr(rec, c)) for c in cols]
        row += [PC_NAME, datetime.utcnow().isoformat()]
        cursor.execute(sql, row)
        count += 1

    return count


def ejecutar_backup(app, cloud_cfg: dict) -> dict:
    """
    Ejecuta el respaldo completo de la empresa activa hacia MySQL.

    Args:
        app: Instancia de la Flask app (para contexto)
        cloud_cfg: dict con claves mysql_host, mysql_port, mysql_user,
                   mysql_password, mysql_database

    Returns:
        dict con ok (bool), tablas (int), registros (int), error (str)
    """
    from ..database.models import (
        Empresa, Usuario, Categoria, Impuesto, Producto,
        Cliente, Proveedor, Factura, DetalleFactura,
        Retencion, DetalleRetencion, NotaCredito, DetalleNotaCredito,
        NotaDebito, DetalleNotaDebito, GuiaRemision, DestinatarioGuia,
        DetalleGuia, LiquidacionCompra, DetalleLiquidacion, CompraProveedor,
    )

    TABLAS = [
        Empresa, Usuario, Categoria, Impuesto, Producto,
        Cliente, Proveedor, Factura, DetalleFactura,
        Retencion, DetalleRetencion, NotaCredito, DetalleNotaCredito,
        NotaDebito, DetalleNotaDebito, GuiaRemision,
        LiquidacionCompra, DetalleLiquidacion, CompraProveedor,
    ]

    # Tablas sin empresa_id directa (detalles asociados)
    TABLAS_SIN_EMPRESA = {
        DetalleFactura, DetalleRetencion, DetalleNotaCredito,
        DetalleNotaDebito, DestinatarioGuia, DetalleGuia, DetalleLiquidacion,
    }

    try:
        conn = _get_mysql_conn(cloud_cfg)
    except Exception as e:
        return {'ok': False, 'error': f'No se pudo conectar a MySQL: {e}'}

    total_registros = 0
    total_tablas = 0

    try:
        with app.app_context():
            from ..database.models import Empresa
            empresas = Empresa.query.filter_by(activo=True).all()

            cursor = conn.cursor()

            for empresa in empresas:
                for model in TABLAS:
                    try:
                        if model in TABLAS_SIN_EMPRESA:
                            # Los detalles se respaldan via su padre, omitir aquí
                            continue
                        n = _backup_table(cursor, model, empresa.id)
                        total_registros += n
                        total_tablas += 1
                    except Exception as e:
                        log.warning(f'Error respaldando {model.__tablename__}: {e}')
                        conn.rollback()
                        continue

            # Registrar el evento de backup
            cursor.execute(
                'INSERT INTO bk_sync_log (source_pc, backup_at, total_registros, resultado) '
                'VALUES (%s, %s, %s, %s)',
                (PC_NAME, datetime.utcnow().isoformat(), total_registros, 'OK')
            )
            conn.commit()
            cursor.close()

    except Exception as e:
        conn.rollback()
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()

    log.info(f'[CloudBackup] OK — {total_tablas} tablas, {total_registros} registros desde {PC_NAME}')
    return {'ok': True, 'tablas': total_tablas, 'registros': total_registros}


# ─── Scheduler diario ─────────────────────────────────────────────────────────

_backup_thread = None
_stop_event = threading.Event()
_last_result = {'ok': None, 'ultima_vez': None, 'registros': 0}


def get_last_result() -> dict:
    return dict(_last_result)


def _scheduler_loop(app, cloud_cfg: dict, hora_backup: int = 2):
    """
    Hilo daemon que ejecuta el backup todos los días a la hora indicada (0-23).
    También ejecuta un backup inmediato al iniciar.
    """
    log.info(f'[CloudBackup] Scheduler iniciado — backup diario a las {hora_backup:02d}:00')

    # Backup inicial al arrancar (con delay de 30s para que la app cargue)
    time.sleep(30)
    if not _stop_event.is_set():
        _run_and_log(app, cloud_cfg)

    while not _stop_event.is_set():
        now = datetime.now()
        if now.hour == hora_backup and now.minute < 5:
            _run_and_log(app, cloud_cfg)
            time.sleep(360)  # Evitar doble ejecución en el mismo minuto
        time.sleep(60)


def _run_and_log(app, cloud_cfg):
    result = ejecutar_backup(app, cloud_cfg)
    _last_result.update({
        'ok': result['ok'],
        'ultima_vez': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'registros': result.get('registros', 0),
        'error': result.get('error', ''),
    })


def iniciar_scheduler(app, cloud_cfg: dict, hora_backup: int = 2):
    """
    Lanza el hilo de backup diario.
    Llamar desde server/main.py después de create_app().
    """
    global _backup_thread
    if _backup_thread and _backup_thread.is_alive():
        return

    _backup_thread = threading.Thread(
        target=_scheduler_loop,
        args=(app, cloud_cfg, hora_backup),
        daemon=True,
        name='cloud-backup'
    )
    _backup_thread.start()


def detener_scheduler():
    _stop_event.set()
