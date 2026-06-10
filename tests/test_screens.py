import os, sys, traceback, faulthandler
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
log = open(os.path.join(os.path.dirname(__file__), 'screens_log.txt'), 'w', encoding='utf-8')
faulthandler.enable(file=log)

def w(msg):
    log.write(msg + '\n')
    log.flush()

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
w('QApplication OK')

SCREENS = [
    ('dashboard', 'DashboardScreen'),
    ('clientes', 'ClientesScreen'),
    ('proveedores', 'ProveedoresScreen'),
    ('categorias', 'CategoriasScreen'),
    ('productos', 'ProductosScreen'),
    ('facturas', 'FacturasScreen'),
    ('retenciones', 'RetencionesScreen'),
    ('notas_credito', 'NotasCreditoScreen'),
    ('notas_debito', 'NotasDebitoScreen'),
    ('guias', 'GuiasScreen'),
    ('liquidaciones', 'LiquidacionesScreen'),
    ('compras', 'ComprasScreen'),
    ('configuracion', 'ConfiguracionScreen'),
]

import importlib
for mod_name, cls_name in SCREENS:
    w(f'--- {mod_name}.{cls_name}')
    try:
        mod = importlib.import_module(f'client.screens.{mod_name}')
        cls = getattr(mod, cls_name)
        inst = cls()
        w('    OK')
    except Exception:
        w('    EXCEPTION:\n' + traceback.format_exc())

w('DONE')
