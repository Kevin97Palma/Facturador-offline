import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')

DEFAULTS = {
    'server_url': 'http://localhost:5000',
    'mode': 'servidor',  # 'servidor' | 'cliente'
    'printer_name': '',
    'printer_type': 'none',  # 'none' | 'escpos_usb' | 'escpos_network' | 'windows'
    'printer_ip': '',
    'printer_port': 9100,
}


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {**DEFAULTS, **data}
        except Exception:
            pass
    return dict(DEFAULTS)


def save_config(cfg: dict):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def get(key: str, default=None):
    return load_config().get(key, default)


def set_value(key: str, value):
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)
