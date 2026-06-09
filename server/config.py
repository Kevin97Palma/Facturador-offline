import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
FIRMAS_DIR = os.path.join(DATA_DIR, 'firmas')
XML_DIR = os.path.join(DATA_DIR, 'xml')
LOGOS_DIR = os.path.join(DATA_DIR, 'logos')

for d in [DATA_DIR, FIRMAS_DIR, XML_DIR, LOGOS_DIR]:
    os.makedirs(d, exist_ok=True)


class Config:
    SECRET_KEY = 'facturador-sri-2024-local'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(DATA_DIR, 'facturador.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = False
