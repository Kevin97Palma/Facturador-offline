"""
Prueba de extremo a extremo: crea todas las entidades y los 6 tipos de
documentos contra el servidor Flask corriendo en localhost:5000.

Uso:  python tests/smoke_test.py
"""
import sys
import requests

BASE = 'http://localhost:5000'
HOY = '2026-06-09'
PASARON = []
FALLARON = []


def paso(nombre, metodo, ruta, payload=None):
    try:
        if metodo == 'GET':
            r = requests.get(f'{BASE}{ruta}', timeout=10)
        else:
            r = requests.post(f'{BASE}{ruta}', json=payload, timeout=10)
        body = r.json()
        if r.status_code in (200, 201) and body.get('ok'):
            PASARON.append(nombre)
            print(f'  OK   {nombre}')
            return body
        FALLARON.append((nombre, f'{r.status_code}: {body}'))
        print(f'  FAIL {nombre} -> {r.status_code}: {body}')
        return None
    except Exception as e:
        FALLARON.append((nombre, str(e)))
        print(f'  FAIL {nombre} -> {e}')
        return None


print('=== SMOKE TEST FACTURADOR ===\n')

# 1. Login
login = paso('Login superadmin', 'POST', '/api/auth/login',
             {'email': 'admin@sistema.com', 'password': 'Admin2024#'})
if not login:
    sys.exit('No se pudo hacer login. Abortando.')
usuario_id = login['usuario']['id']

# 2. Empresa (con establecimiento y punto de emisión)
emp = paso('Crear empresa', 'POST', '/api/empresas/', {
    'ruc': '1790012345001',
    'razon_social': 'EMPRESA DE PRUEBA S.A.',
    'nombre_comercial': 'PruebaCorp',
    'direccion': 'Av. Amazonas N12-34, Quito',
    'telefono': '022345678',
    'email': 'prueba@empresa.com',
    'establecimiento': '001',
    'punto_emision': '001',
    'ambiente': 1,
})
if not emp:
    sys.exit('No se pudo crear empresa. Abortando.')
EID = emp['data']['id']

# 3. Usuario de la empresa
paso('Crear usuario', 'POST', '/api/usuarios/', {
    'empresa_id': EID, 'nombre': 'Juan', 'apellido': 'Pérez',
    'email': 'juan@empresa.com', 'password': 'Clave2024#', 'rol': 'vendedor',
})

# 4. Categoría
cat = paso('Crear categoría', 'POST', '/api/categorias/', {
    'empresa_id': EID, 'nombre': 'General', 'descripcion': 'Categoría general',
})

# 5. Impuesto (IVA 15%)
imp = paso('Crear impuesto IVA 15%', 'POST', '/api/impuestos/', {
    'empresa_id': EID, 'nombre': 'IVA 15%', 'codigo': '2',
    'codigo_porcentaje': '4', 'porcentaje': 15,
})

# 6. Producto
prod = paso('Crear producto', 'POST', '/api/productos/', {
    'empresa_id': EID,
    'categoria_id': cat['data']['id'] if cat else None,
    'impuesto_id': imp['data']['id'] if imp else None,
    'codigo': 'PROD-001', 'nombre': 'Producto de Prueba',
    'descripcion': 'Artículo de prueba', 'precio_venta': 10.00,
    'stock': 100,
})

# 7. Cliente
cli = paso('Crear cliente', 'POST', '/api/clientes/', {
    'empresa_id': EID, 'tipo_identificacion': '05',
    'identificacion': '1712345678', 'razon_social': 'Cliente de Prueba',
    'direccion': 'Calle Falsa 123', 'email': 'cliente@mail.com',
    'telefono': '0991234567',
})
CID = cli['data']['id'] if cli else None

# 8. Proveedor
prov = paso('Crear proveedor', 'POST', '/api/proveedores/', {
    'empresa_id': EID, 'tipo_identificacion': '04',
    'identificacion': '1790099887001', 'razon_social': 'Proveedor de Prueba S.A.',
    'direccion': 'Av. Proveedor 456', 'email': 'prov@mail.com',
})
PID = prov['data']['id'] if prov else None

DETALLE = [{
    'codigo_principal': 'PROD-001', 'descripcion': 'Producto de Prueba',
    'cantidad': 2, 'precio_unitario': 10.00, 'descuento': 0,
    'impuesto_codigo': '2', 'impuesto_codigo_porcentaje': '4',
    'impuesto_tarifa': 15,
}]

# 9. Factura
fac = paso('Crear FACTURA', 'POST', '/api/facturas/', {
    'empresa_id': EID, 'usuario_id': usuario_id, 'cliente_id': CID,
    'fecha_emision': HOY, 'forma_pago': '01', 'detalles': DETALLE,
})

# 10. Retención
paso('Crear RETENCIÓN', 'POST', '/api/retenciones/', {
    'empresa_id': EID, 'usuario_id': usuario_id, 'proveedor_id': PID,
    'fecha_emision': HOY, 'periodo_fiscal': '06/2026',
    'detalles': [{
        'codigo_sustento': '01', 'cod_doc_sustento': '01',
        'num_doc_sustento': '001-001-000000001',
        'fecha_emision_doc_sustento': HOY,
        'codigo': '303', 'descripcion': 'Honorarios',
        'base_imponible': 100.00, 'porcentaje': 10,
    }],
})

# 11. Nota de crédito
num_fac = fac['data'].get('numero_completo') or fac['data'].get('numero', '001-001-000000001') if fac else '001-001-000000001'
paso('Crear NOTA DE CRÉDITO', 'POST', '/api/notas-credito/', {
    'empresa_id': EID, 'usuario_id': usuario_id, 'cliente_id': CID,
    'fecha_emision': HOY, 'motivo': 'Devolución de mercadería',
    'cod_doc_modificado': '01', 'num_doc_modificado': str(num_fac),
    'fecha_emision_doc_sustento': HOY, 'detalles': DETALLE,
})

# 12. Nota de débito
paso('Crear NOTA DE DÉBITO', 'POST', '/api/notas-debito/', {
    'empresa_id': EID, 'usuario_id': usuario_id, 'cliente_id': CID,
    'fecha_emision': HOY, 'cod_doc_modificado': '01',
    'num_doc_modificado': str(num_fac), 'fecha_emision_doc_sustento': HOY,
    'detalles': [{'razon': 'Intereses por mora', 'valor': 5.00}],
})

# 13. Guía de remisión
paso('Crear GUÍA DE REMISIÓN', 'POST', '/api/guias/', {
    'empresa_id': EID, 'usuario_id': usuario_id,
    'fecha_ini_transporte': HOY, 'fecha_fin_transporte': HOY,
    'ruc_transportista': '1712345678001',
    'razon_social_transportista': 'Transportes Rápidos',
    'placa': 'PBA1234',
    'destinatarios': [{
        'identificacion_destinatario': '1712345678',
        'razon_social_destinatario': 'Cliente de Prueba',
        'direccion_destinatario': 'Calle Falsa 123',
        'motivo_traslado': 'Venta',
        'detalles': [{'codigo_interno': 'PROD-001',
                      'descripcion': 'Producto de Prueba', 'cantidad': 2}],
    }],
})

# 14. Liquidación de compra
paso('Crear LIQUIDACIÓN DE COMPRA', 'POST', '/api/liquidaciones/', {
    'empresa_id': EID, 'usuario_id': usuario_id, 'proveedor_id': PID,
    'fecha_emision': HOY, 'forma_pago': '01', 'detalles': DETALLE,
})

# 15. Listados
paso('Listar facturas', 'GET', f'/api/facturas/{EID}')
paso('Listar retenciones', 'GET', f'/api/retenciones/{EID}')
paso('Listar notas crédito', 'GET', f'/api/notas-credito/{EID}')
paso('Listar notas débito', 'GET', f'/api/notas-debito/{EID}')
paso('Listar guías', 'GET', f'/api/guias/{EID}')
paso('Listar liquidaciones', 'GET', f'/api/liquidaciones/{EID}')

print(f'\n=== RESULTADO: {len(PASARON)} OK, {len(FALLARON)} fallos ===')
for n, e in FALLARON:
    print(f'  FALLO: {n}\n    {e}')
sys.exit(1 if FALLARON else 0)
