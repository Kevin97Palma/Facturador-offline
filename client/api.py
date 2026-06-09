import requests
from . import config as cfg

_session = requests.Session()
_token = None
_user = None
_empresa = None


def set_session(token, user, empresa):
    global _token, _user, _empresa
    _token = token
    _user = user
    _empresa = empresa


def get_user():
    return _user


def get_empresa():
    return _empresa


def clear_session():
    global _token, _user, _empresa
    _token = _user = _empresa = None


def _url(path: str) -> str:
    base = cfg.get('server_url', 'http://localhost:5000').rstrip('/')
    return f'{base}{path}'


def _headers():
    h = {'Content-Type': 'application/json'}
    if _token:
        h['Authorization'] = f'Bearer {_token}'
    return h


def _req(method, path, **kwargs):
    try:
        r = _session.request(method, _url(path), headers=_headers(),
                             timeout=15, **kwargs)
        return r.json()
    except requests.exceptions.ConnectionError:
        return {'ok': False, 'error': 'No se puede conectar al servidor. Verifique la URL y que el servidor esté activo.'}
    except requests.exceptions.Timeout:
        return {'ok': False, 'error': 'Tiempo de espera agotado. El servidor no responde.'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def get(path, params=None):
    return _req('GET', path, params=params)


def post(path, data=None):
    return _req('POST', path, json=data)


def put(path, data=None):
    return _req('PUT', path, json=data)


def delete(path):
    return _req('DELETE', path)


def download(path):
    """Download binary content (PDF, XML). Returns bytes or None."""
    try:
        r = _session.get(_url(path), headers=_headers(), timeout=30)
        if r.status_code == 200:
            return r.content, None
        try:
            err = r.json().get('error', 'Error desconocido')
        except Exception:
            err = f'HTTP {r.status_code}'
        return None, err
    except Exception as e:
        return None, str(e)


# -- Auth helpers --

def login(email, password):
    return _req('POST', '/api/auth/login', json={'email': email, 'password': password})


# -- Empresa-scoped helpers --

def empresa_id():
    return _empresa['id'] if _empresa else None


def usuario_id():
    return _user['id'] if _user else None
