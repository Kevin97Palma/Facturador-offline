import os
from flask import Blueprint, send_file, abort
from ..config import BASE_DIR

archivos_bp = Blueprint('archivos', __name__)

XML_DIR = os.path.join(BASE_DIR, 'data', 'xml')


@archivos_bp.route('/xml/<path:filename>', methods=['GET'])
def servir_xml(filename):
    ruta = os.path.join(XML_DIR, filename)
    if not os.path.exists(ruta) or not ruta.startswith(XML_DIR):
        abort(404)
    return send_file(ruta, as_attachment=True, download_name=filename, mimetype='application/xml')
