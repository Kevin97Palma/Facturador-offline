"""
Validación de licencias desde MySQL en la nube.

Cada empresa tiene una licencia asociada a su RUC.
El sistema verifica la licencia al iniciar y una vez al día.
Si no hay conexión, usa el caché local (SQLite) con gracia de 7 días.
"""
import logging
from datetime import datetime, date, timedelta

log = logging.getLogger(__name__)

_GRACE_DAYS = 7  # Días offline que se permiten sin conexión a la nube


# ─── Cache local ──────────────────────────────────────────────────────────────

def _get_cache_table(db):
    """Crea la tabla de caché de licencias si no existe."""
    try:
        db.engine.execute(
            '''CREATE TABLE IF NOT EXISTS licencia_cache (
                ruc TEXT PRIMARY KEY,
                activo INTEGER DEFAULT 1,
                plan TEXT DEFAULT 'basico',
                fecha_vencimiento TEXT,
                max_equipos INTEGER DEFAULT 1,
                last_check TEXT,
                last_online TEXT
            )'''
        )
    except Exception:
        pass  # SQLAlchemy 2.x usa text()
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text(
                '''CREATE TABLE IF NOT EXISTS licencia_cache (
                    ruc TEXT PRIMARY KEY,
                    activo INTEGER DEFAULT 1,
                    plan TEXT DEFAULT 'basico',
                    fecha_vencimiento TEXT,
                    max_equipos INTEGER DEFAULT 1,
                    last_check TEXT,
                    last_online TEXT
                )'''
            ))
            conn.commit()
    except Exception as e:
        log.debug(f'licencia_cache ya existe o error menor: {e}')


def _cache_get(db, ruc: str) -> dict | None:
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            row = conn.execute(
                text('SELECT * FROM licencia_cache WHERE ruc = :ruc'),
                {'ruc': ruc}
            ).fetchone()
            if row:
                return dict(row._mapping)
    except Exception as e:
        log.debug(f'Cache get error: {e}')
    return None


def _cache_set(db, ruc: str, data: dict):
    try:
        from sqlalchemy import text
        now = datetime.now().isoformat()
        with db.engine.connect() as conn:
            conn.execute(text(
                '''INSERT OR REPLACE INTO licencia_cache
                   (ruc, activo, plan, fecha_vencimiento, max_equipos, last_check, last_online)
                   VALUES (:ruc, :activo, :plan, :venc, :max_eq, :now, :now)'''
            ), {
                'ruc': ruc,
                'activo': 1 if data.get('activo') else 0,
                'plan': data.get('plan', 'basico'),
                'venc': data.get('fecha_vencimiento', ''),
                'max_eq': data.get('max_equipos', 1),
                'now': now,
            })
            conn.commit()
    except Exception as e:
        log.debug(f'Cache set error: {e}')


def _cache_touch(db, ruc: str):
    """Actualiza solo el last_check sin cambiar last_online (offline check)."""
    try:
        from sqlalchemy import text
        now = datetime.now().isoformat()
        with db.engine.connect() as conn:
            conn.execute(
                text('UPDATE licencia_cache SET last_check = :now WHERE ruc = :ruc'),
                {'now': now, 'ruc': ruc}
            )
            conn.commit()
    except Exception as e:
        log.debug(f'Cache touch error: {e}')


# ─── Consulta MySQL ───────────────────────────────────────────────────────────

def _consultar_mysql(cloud_cfg: dict, ruc: str) -> dict | None:
    try:
        import pymysql
        conn = pymysql.connect(
            host=cloud_cfg['mysql_host'],
            port=int(cloud_cfg.get('mysql_port', 3306)),
            user=cloud_cfg['mysql_user'],
            password=cloud_cfg['mysql_password'],
            database=cloud_cfg['mysql_database'],
            charset='utf8mb4',
            connect_timeout=8,
        )
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                'SELECT * FROM licencias WHERE ruc = %s AND activo = 1 LIMIT 1',
                (ruc,)
            )
            row = cur.fetchone()
        conn.close()
        return row
    except Exception as e:
        log.warning(f'[License] No se pudo consultar MySQL: {e}')
        return None


# ─── Verificación principal ───────────────────────────────────────────────────

def verificar_licencia(ruc: str, cloud_cfg: dict, db) -> dict:
    """
    Verifica si la empresa (RUC) tiene licencia activa y no vencida.

    Flujo:
      1. Intenta consultar MySQL en la nube.
      2. Si hay respuesta → actualiza caché local → devuelve resultado.
      3. Si no hay conexión → usa caché local.
      4. Si el caché tiene más de GRACE_DAYS días sin conexión → BLOQUEADO.

    Returns:
        dict con:
            valida (bool)
            plan (str): 'basico', 'profesional', 'enterprise'
            fecha_vencimiento (str)
            max_equipos (int)
            modo (str): 'online' | 'cache' | 'bloqueado'
            mensaje (str)
    """
    _get_cache_table(db)

    # 1. Intentar consulta online
    datos_mysql = _consultar_mysql(cloud_cfg, ruc)

    if datos_mysql:
        # Verificar vencimiento
        venc_str = str(datos_mysql.get('fecha_vencimiento', ''))
        vencida = False
        if venc_str:
            try:
                venc_date = date.fromisoformat(venc_str[:10])
                vencida = venc_date < date.today()
            except ValueError:
                pass

        activo = bool(datos_mysql.get('activo', 0)) and not vencida
        resultado = {
            'valida': activo,
            'plan': datos_mysql.get('plan', 'basico'),
            'fecha_vencimiento': venc_str[:10] if venc_str else '',
            'max_equipos': int(datos_mysql.get('max_equipos', 1)),
            'modo': 'online',
            'mensaje': 'Licencia activa' if activo else (
                'Licencia vencida' if vencida else 'Licencia inactiva — contacte al proveedor'
            ),
        }
        _cache_set(db, ruc, datos_mysql)
        return resultado

    # 2. Usar caché si no hay conexión
    cache = _cache_get(db, ruc)

    if cache is None:
        return {
            'valida': False,
            'plan': 'sin_licencia',
            'fecha_vencimiento': '',
            'max_equipos': 0,
            'modo': 'bloqueado',
            'mensaje': 'Sin licencia registrada. Contacte al proveedor del sistema.',
        }

    # Calcular días desde última conexión exitosa
    try:
        last_online = datetime.fromisoformat(cache.get('last_online', '2000-01-01'))
        dias_offline = (datetime.now() - last_online).days
    except ValueError:
        dias_offline = 999

    if dias_offline > _GRACE_DAYS:
        return {
            'valida': False,
            'plan': cache.get('plan', 'basico'),
            'fecha_vencimiento': cache.get('fecha_vencimiento', ''),
            'max_equipos': int(cache.get('max_equipos', 1)),
            'modo': 'bloqueado',
            'mensaje': (
                f'Sin conexión a la nube por {dias_offline} días. '
                f'Período de gracia ({_GRACE_DAYS} días) vencido. '
                'Verifique su conexión a Internet.'
            ),
        }

    _cache_touch(db, ruc)
    return {
        'valida': bool(cache.get('activo', 0)),
        'plan': cache.get('plan', 'basico'),
        'fecha_vencimiento': cache.get('fecha_vencimiento', ''),
        'max_equipos': int(cache.get('max_equipos', 1)),
        'modo': 'cache',
        'mensaje': (
            f'Sin conexión. Usando caché local '
            f'(días offline: {dias_offline}/{_GRACE_DAYS})'
        ),
    }


def registrar_equipo(ruc: str, cloud_cfg: dict) -> bool:
    """
    Registra el equipo actual en la tabla equipos_registrados de MySQL.
    Devuelve True si el número de equipos registrados está dentro del límite.
    """
    import socket
    pc_name = socket.gethostname()
    try:
        import pymysql
        conn = pymysql.connect(
            host=cloud_cfg['mysql_host'],
            port=int(cloud_cfg.get('mysql_port', 3306)),
            user=cloud_cfg['mysql_user'],
            password=cloud_cfg['mysql_password'],
            database=cloud_cfg['mysql_database'],
            charset='utf8mb4',
            connect_timeout=8,
        )
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # Registrar/actualizar este equipo
            cur.execute(
                '''INSERT INTO equipos_registrados (ruc, nombre_pc, ultimo_acceso)
                   VALUES (%s, %s, NOW())
                   ON DUPLICATE KEY UPDATE ultimo_acceso = NOW()''',
                (ruc, pc_name)
            )
            # Contar equipos activos (con acceso en los últimos 30 días)
            cur.execute(
                '''SELECT COUNT(*) as total FROM equipos_registrados
                   WHERE ruc = %s
                   AND ultimo_acceso >= DATE_SUB(NOW(), INTERVAL 30 DAY)''',
                (ruc,)
            )
            row = cur.fetchone()
            total_equipos = int(row['total']) if row else 1

            # Obtener límite de la licencia
            cur.execute('SELECT max_equipos FROM licencias WHERE ruc = %s', (ruc,))
            lic = cur.fetchone()
            max_eq = int(lic['max_equipos']) if lic else 1

        conn.commit()
        conn.close()
        return total_equipos <= max_eq

    except Exception as e:
        log.warning(f'[License] No se pudo registrar equipo: {e}')
        return True  # En caso de error de conexión, permitir acceso
