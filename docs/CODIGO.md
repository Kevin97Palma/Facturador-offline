# Documentación del Código — Facturador Electrónico SRI Ecuador

> Versión 1.0.0 · PyQt5 + Flask + SQLite

---

## Índice

1. [Punto de entrada — `app.py`](#1-punto-de-entrada--apppy)
2. [Cliente — `client/config.py`](#2-cliente--clientconfigpy)
3. [Cliente — `client/api.py`](#3-cliente--clientapipy)
4. [Cliente — `client/theme.py`](#4-cliente--clientthemepy)
5. [Cliente — `client/widgets.py`](#5-cliente--clientwidgetspy)
6. [Cliente — `client/main_window.py`](#6-cliente--clientmain_windowpy)
7. [Cliente — `client/printer.py`](#7-cliente--clientprinterpy)
8. [Pantallas — `client/screens/login.py`](#8-pantallas--clientscreensloginpy)
9. [Pantallas — `client/screens/dashboard.py`](#9-pantallas--clientscreensdashboardpy)
10. [Pantallas — `client/screens/facturas.py`](#10-pantallas--clientscreensfacturaspy)
11. [Base de Datos — `server/database/models.py`](#11-base-de-datos--serverdatabasemodelspy)
12. [Servicios — `server/services/clave_acceso.py`](#12-servicios--serverservicesclave_accesopy)
13. [Servicios — `server/services/xml_generator.py`](#13-servicios--serverservicesxml_generatorpy)
14. [Servicios — `server/services/sri_service.py`](#14-servicios--serverservicessri_servicepy)
15. [API Routes — `server/api/auth.py`](#15-api-routes--serverapiauthpy)
16. [API Routes — `server/api/facturas.py`](#16-api-routes--serverapifacturaspy)
17. [API Routes — Catálogos](#17-api-routes--catálogos)

---

## 1. Punto de entrada — `app.py`

Archivo raíz que orquesta el arranque completo de la aplicación.

### `_ensure_dirs()`

```python
def _ensure_dirs()
```

Crea los directorios de datos necesarios si no existen al iniciar la aplicación.

| Directorio creado | Propósito |
|---|---|
| `data/xml` | XMLs generados y autorizados por el SRI |
| `data/firmas` | Archivos de firma digital `.p12` |
| `data/logos` | Logos de empresas para el RIDE |

**Cuándo se llama:** siempre, antes de cualquier otra acción en `main()`.

---

### `_start_server()`

```python
def _start_server()
```

Lanza el servidor Flask en un **hilo daemon** separado del hilo principal de Qt.

- Importa y llama a `server.main.run_server('0.0.0.0', 5000)`.
- El hilo es `daemon=True`, por lo que se destruye automáticamente cuando la app Qt cierra.
- Espera `1.5 segundos` tras iniciar el hilo para que Flask quede listo antes de que el login intente conectarse.

**Solo se ejecuta** cuando `config.json → mode = "servidor"`. En equipos clientes esta función no se invoca.

---

### `main()`

```python
def main()
```

Función principal. Secuencia de ejecución:

1. `_ensure_dirs()` — prepara el sistema de archivos.
2. Lee `mode` de `config.json` (default: `"servidor"`).
3. Si `mode == "servidor"` → llama a `_start_server()`.
4. Crea `QApplication` con estilo `Fusion`.
5. Instancia `LoginScreen` y la muestra.
6. Conecta la señal `login_success` de `LoginScreen` al slot `on_login`.
7. `on_login`: oculta el login y abre `MainWindow`.
8. Entra en el loop de eventos Qt con `sys.exit(app.exec_())`.

---

## 2. Cliente — `client/config.py`

Gestiona la configuración local de cada equipo en `config.json`.

### Constantes

```python
CONFIG_FILE  # Ruta absoluta a config.json (junto al ejecutable)

DEFAULTS = {
    'server_url': 'http://localhost:5000',
    'mode': 'servidor',       # 'servidor' | 'cliente'
    'printer_name': '',
    'printer_type': 'none',   # 'none' | 'escpos_usb' | 'escpos_network' | 'windows'
    'printer_ip': '',
    'printer_port': 9100,
}
```

---

### `load_config() → dict`

```python
def load_config() -> dict
```

Lee `config.json` del disco y lo fusiona con los valores por defecto.

- Si el archivo no existe o tiene JSON inválido, devuelve una copia de `DEFAULTS`.
- Usa `{**DEFAULTS, **data}` para que las claves presentes en el archivo sobreescriban los defaults, pero las claves faltantes queden con su valor por defecto.

---

### `save_config(cfg: dict)`

```python
def save_config(cfg: dict)
```

Escribe el diccionario `cfg` a `config.json` con indentación de 2 espacios y soporte UTF-8.

---

### `get(key: str, default=None)`

```python
def get(key: str, default=None)
```

Atajo para leer un valor individual de la configuración. Llama a `load_config()` internamente. Ejemplo:

```python
url = cfg.get('server_url')        # 'http://localhost:5000'
modo = cfg.get('mode', 'cliente')  # 'servidor'
```

---

### `set_value(key: str, value)`

```python
def set_value(key: str, value)
```

Modifica un solo campo de la configuración en disco. Lee la config completa, actualiza la clave, y vuelve a guardar.

---

## 3. Cliente — `client/api.py`

Capa HTTP del cliente. Todas las pantallas usan estas funciones para comunicarse con el servidor Flask.

### Estado de sesión (módulo-level)

```python
_session  # requests.Session reutilizada entre llamadas
_token    # JWT / token de sesión devuelto por /api/auth/login
_user     # dict con datos del usuario autenticado
_empresa  # dict con datos de la empresa activa
```

---

### `set_session(token, user, empresa)`

Almacena los datos de la sesión activa tras un login exitoso. Llamado por `LoginScreen` al recibir la respuesta del servidor.

```python
set_session(
    token="abc123...",
    user={"id": 1, "nombre": "Juan Pérez", "rol": "admin", ...},
    empresa={"id": 1, "ruc": "1234567890001", ...}
)
```

---

### `clear_session()`

Borra token, usuario y empresa de memoria. Llamado al cerrar sesión desde el sidebar.

---

### `get_user() → dict | None`

Devuelve el diccionario del usuario activo. Campos: `id`, `nombre`, `email`, `rol`, `empresa_id`.

---

### `get_empresa() → dict | None`

Devuelve el diccionario de la empresa activa. Campos: `id`, `ruc`, `razon_social`, etc.

---

### `empresa_id() → int | None`

Atajo que devuelve `_empresa['id']`. Usado en casi todas las pantallas para construir las URLs de los endpoints.

---

### `usuario_id() → int | None`

Atajo que devuelve `_user['id']`. Usado al crear documentos para registrar quién los emitió.

---

### `_url(path: str) → str`  *(privada)*

Construye la URL completa concatenando `server_url` de config y el `path`. Elimina barras dobles.

```python
_url('/api/facturas/1')  → 'http://192.168.1.100:5000/api/facturas/1'
```

---

### `_headers() → dict`  *(privada)*

Devuelve los headers HTTP estándar. Si hay token activo, agrega `Authorization: Bearer <token>`.

---

### `_req(method, path, **kwargs) → dict`  *(privada)*

Ejecutor genérico de peticiones HTTP. Captura y normaliza errores:

| Excepción capturada | Respuesta devuelta |
|---|---|
| `ConnectionError` | `{'ok': False, 'error': 'No se puede conectar...'}` |
| `Timeout` (15 s) | `{'ok': False, 'error': 'Tiempo de espera agotado...'}` |
| Cualquier otra | `{'ok': False, 'error': str(e)}` |

Todas las respuestas exitosas son JSON parseado automáticamente.

---

### `get(path, params=None) → dict`

```python
resp = api.get('/api/productos/1', params={'q': 'laptop'})
```

---

### `post(path, data=None) → dict`

```python
resp = api.post('/api/facturas/', data={...})
```

---

### `put(path, data=None) → dict`

```python
resp = api.put('/api/clientes/5', data={'telefono': '0999999999'})
```

---

### `delete(path) → dict`

```python
resp = api.delete('/api/productos/3')
```

---

### `download(path) → tuple[bytes | None, str | None]`

Descarga contenido binario (PDF o XML). Devuelve una tupla `(contenido, error)`.

- Si éxito: `(bytes, None)`
- Si error HTTP: `(None, 'mensaje de error')`
- Si excepción: `(None, str(e))`

Timeout extendido a **30 segundos** para archivos grandes.

```python
contenido, error = api.download('/api/facturas/5/pdf')
if contenido:
    with open('factura.pdf', 'wb') as f:
        f.write(contenido)
```

---

### `login(email, password) → dict`

Llama a `POST /api/auth/login`. Devuelve la respuesta del servidor con `ok`, `usuario`, y datos de empresa.

---

## 4. Cliente — `client/theme.py`

Sistema de diseño centralizado. Define la paleta de colores, tipografía, y el stylesheet global de Qt.

### Paleta `C` (colores)

```python
C = {
    'bg_deep':   '#0d1117',  # Fondo más oscuro (ventana principal)
    'bg_base':   '#161b22',  # Fondo base de paneles
    'bg_card':   '#1c2128',  # Fondo de tarjetas/cards
    'bg_input':  '#21262d',  # Fondo de campos de entrada
    'border':    '#30363d',  # Bordes y separadores
    'accent':    '#2ea043',  # Verde — acción principal
    'accent2':   '#388bfd',  # Azul — acción secundaria
    'warning':   '#d29922',  # Amarillo — advertencias
    'danger':    '#da3633',  # Rojo — errores y eliminar
    'text':      '#e6edf3',  # Texto principal
    'text_muted':'#8b949e',  # Texto secundario/apagado
    'text_on_accent': '#ffffff',  # Texto sobre botones verdes
}
```

### Tamaños de fuente `F`

```python
F = {
    'xs':   '10px',
    'sm':   '11px',
    'base': '13px',
    'md':   '14px',
    'lg':   '16px',
    'xl':   '20px',
    'xxl':  '24px',
}
```

### `APP_STYLE`

String con el QSS (Qt Style Sheet) global que estiliza:
- `QMainWindow`, `QDialog`, `QWidget` — fondos oscuros
- `QPushButton` — variantes: `primary` (verde), `danger` (rojo), `secondary` (gris)
- `QLineEdit`, `QComboBox`, `QSpinBox`, `QDateEdit` — inputs con borde y foco verde
- `QTableWidget` — cabecera oscura, filas alternadas, selección verde
- `QGroupBox` — título con borde verde
- `QScrollBar` — barra delgada con thumb gris

### `SIDEBAR_STYLE`

QSS específico del sidebar lateral. Botones con estado `checked` resaltado en verde.

---

## 5. Cliente — `client/widgets.py`

Componentes reutilizables de UI.

### `Toast(QWidget)`

Notificación flotante no-bloqueante que aparece en la esquina inferior-derecha de la pantalla padre.

**Constructor:** `Toast(parent, message, kind='ok')`

| `kind` | Color | Icono |
|---|---|---|
| `'ok'` | Verde | ✓ |
| `'error'` | Rojo | ✗ |
| `'warning'` | Amarillo | ⚠ |
| `'info'` | Azul | ℹ |

Se auto-destruye tras **3 segundos** con animación de desvanecimiento.

---

### `toast(parent, msg, kind='ok')`

Función de conveniencia para mostrar un `Toast`. Ejemplo:

```python
toast(self, "Factura autorizada correctamente", kind='ok')
toast(self, "Error al conectar con el SRI", kind='error')
```

---

### `StatCard(QFrame)`

Tarjeta de estadística para el dashboard.

**Constructor:** `StatCard(title, value, color=C['accent'])`

- Muestra un título pequeño, un valor grande, y una barra de color en la parte superior.
- Tiene sombra con `QGraphicsDropShadowEffect`.

---

### `SearchBar(QLineEdit)`

Campo de búsqueda con ícono 🔍 y placeholder gris. Bordes redondeados.

**Constructor:** `SearchBar(placeholder='Buscar...')`

---

### `LoadWorker(QThread)`

Hilo de trabajo genérico para ejecutar funciones en segundo plano sin bloquear la UI.

**Señales:**
- `done = pyqtSignal(object)` — emitida al finalizar, lleva el valor de retorno de la función

**Constructor:** `LoadWorker(func, *args, **kwargs)`

**Uso típico:**
```python
def _cargar():
    return api.get(f'/api/facturas/{self.empresa_id}')

worker = LoadWorker(_cargar)
worker.done.connect(self._on_data_loaded)
worker.start()
```

---

### `BaseScreen(QWidget)`

Clase base para todas las pantallas del sistema.

**Métodos:**

- `_run(func, *args) → None` — ejecuta `func` en un `LoadWorker`, conecta `done` a `_on_result`.
- `refresh()` — override en subclases para recargar datos.
- `_page_header(title, subtitle='') → QWidget` — genera un widget de cabecera con título y subtítulo.

---

### Funciones de utilidad para tablas

#### `make_btn(text, obj_name='') → QPushButton`
Crea un botón estilizado para usar dentro de celdas de tabla.

#### `make_table(cols: list[str]) → QTableWidget`
Crea una `QTableWidget` con las columnas especificadas, cabecera oscura y sin edición directa.

```python
tabla = make_table(['#', 'Cliente', 'Total', 'Estado', 'Acciones'])
```

#### `table_item(text='') → QTableWidgetItem`
Crea un `QTableWidgetItem` no-editable centrado.

#### `set_estado_item(item, estado)`
Colorea un `QTableWidgetItem` según el estado del documento:

| Estado | Color |
|---|---|
| `AUTORIZADO` | Verde |
| `PENDIENTE` | Amarillo |
| `NO_AUTORIZADO` | Rojo |
| `ANULADO` | Gris |

---

## 6. Cliente — `client/main_window.py`

Ventana principal de la aplicación tras el login.

### `MainWindow(QMainWindow)`

**Constructor:** `MainWindow()`

Estructura de la ventana:
- **Sidebar izquierdo**: botones de navegación agrupados por sección.
- **Área central**: `QStackedWidget` que muestra la pantalla activa.
- **Barra de estado**: muestra estado del servidor + RUC de la empresa.

### `MENU`

Lista de tuplas `(icono, clave, label, sección)` que define la navegación:

```python
MENU = [
    ('🏠', 'dashboard',     'Dashboard',           'INICIO'),
    ('🧾', 'facturas',      'Facturas',             'VENTAS'),
    ('✂️', 'retenciones',   'Retenciones',          'VENTAS'),
    ('📋', 'notas_credito', 'Notas de Crédito',     'VENTAS'),
    ('📌', 'notas_debito',  'Notas de Débito',      'VENTAS'),
    ('🚚', 'guias',         'Guías de Remisión',    'VENTAS'),
    ('🤝', 'liquidaciones', 'Liquidaciones',        'VENTAS'),
    ('📦', 'productos',     'Productos',            'CATÁLOGOS'),
    ('🗂️', 'categorias',    'Categorías',           'CATÁLOGOS'),
    ('💰', 'impuestos',     'Impuestos',            'CATÁLOGOS'),
    ('👥', 'clientes',      'Clientes',             'CATÁLOGOS'),
    ('🏭', 'proveedores',   'Proveedores',          'CATÁLOGOS'),
    ('📥', 'compras',       'Compras',              'COMPRAS'),
    ('⚙️', 'configuracion', 'Configuración',        'SISTEMA'),
]
```

### `_navigate(key)`

Cambia la pantalla activa en el `QStackedWidget`. Las pantallas se instancian de forma diferida (solo cuando se navega a ellas por primera vez) para mejorar el tiempo de arranque.

### `_check_server()`

Timer que corre cada 10 segundos. Hace `GET /api/auth/empresas` con header especial y actualiza el ícono de la barra de estado (🟢 conectado / 🔴 sin conexión).

---

## 7. Cliente — `client/printer.py`

Integración con impresoras térmicas ESC/POS y Windows nativas.

### `_get_printer()`  *(privada)*

Lee `printer_type` de la config y devuelve una instancia del driver correcto:

| `printer_type` | Driver |
|---|---|
| `'escpos_usb'` | `escpos.printer.Usb` con VID/PID de la config |
| `'escpos_network'` | `escpos.printer.Network` con IP:puerto de la config |
| `'windows'` | `escpos.printer.Win32Raw` con el nombre de la impresora |
| `'none'` | `None` |

---

### `imprimir_ticket_factura(factura_dict)`

Imprime un ticket de factura en formato 80mm ESC/POS.

**Parámetro:** `factura_dict` — diccionario completo de la factura tal como devuelve `GET /api/facturas/{id}`.

**Formato del ticket:**
```
[LOGO si existe]
RAZON SOCIAL
RUC: xxx
FACTURA: 001-001-000000001
CLIENTE: xxx
────────────────────────────
descripcion   cant  precio  total
...
────────────────────────────
SUBTOTAL:  $xx.xx
IVA 12%:   $xx.xx
TOTAL:     $xx.xx
────────────────────────────
AUTORIZACIÓN: xxx...
Gracias por su compra
```

---

### `imprimir_prueba()`

Imprime una página de prueba para verificar la conectividad con la impresora. Útil desde la pantalla de Configuración.

---

## 8. Pantallas — `client/screens/login.py`

### `LoginScreen(QDialog)`

Pantalla de login con diseño de tarjeta centrada.

**Señales:**
- `login_success = pyqtSignal()` — emitida cuando el login es exitoso

**`_do_login()`**

1. Valida que email y contraseña no estén vacíos.
2. Deshabilita el botón y muestra "Verificando...".
3. Llama a `api.login(email, password)` en un `LoadWorker`.
4. Si `ok=True`: llama a `api.set_session(...)` y emite `login_success`.
5. Si `ok=False`: muestra toast de error y reactiva el botón.

---

## 9. Pantallas — `client/screens/dashboard.py`

### `DashboardScreen(BaseScreen)`

Pantalla de inicio con resumen estadístico de la empresa.

**`refresh()`**

Hace 6 peticiones en paralelo (una por tipo de documento) para obtener los conteos:

```
GET /api/facturas/{empresa_id}
GET /api/retenciones/{empresa_id}
GET /api/notas_credito/{empresa_id}
GET /api/notas_debito/{empresa_id}
GET /api/guias/{empresa_id}
GET /api/liquidaciones/{empresa_id}
```

Muestra los resultados en 6 `StatCard` con el total de documentos por estado.

---

## 10. Pantallas — `client/screens/facturas.py`

### `NuevaFacturaDialog(QDialog)`

Diálogo para crear una nueva factura de venta.

**Secciones del formulario:**
1. **Cabecera**: fecha de emisión, cliente (búsqueda por RUC/cédula), forma de pago.
2. **Detalles**: tabla de ítems con búsqueda de producto por código de barras (compatible con scanner USB).
3. **Totales**: subtotal 0%, subtotal 12%, IVA, total.

**`_buscar_cliente(identificacion)`**

Busca al cliente en `GET /api/clientes/{empresa_id}?q={identificacion}`. Si no existe, ofrece crearlo.

**`_buscar_producto(codigo)`**

Busca en `GET /api/productos/{empresa_id}?q={codigo}`. Usado tanto con el campo de texto como con el scanner USB (que emite el código como pulsaciones de teclado terminadas en `Enter`).

**`_calcular_totales()`**

Recorre todas las filas de la tabla de ítems y acumula subtotales e IVA en tiempo real conforme el usuario escribe.

**`_guardar()`**

Construye el payload JSON y hace `POST /api/facturas/` con todos los detalles. Muestra toast de éxito o error.

---

### `FacturasScreen(BaseScreen)`

Pantalla principal del listado de facturas.

**`_make_actions(row, factura_id, estado)`**

Genera un widget con botones contextuales para cada fila:

| Estado | Botones disponibles |
|---|---|
| `PENDIENTE` | ▶ Autorizar, XML, 🖨 Ticket |
| `AUTORIZADO` | PDF, XML, 🖨 Ticket |
| `NO_AUTORIZADO` | ▶ Reintentar, XML |
| `ANULADO` | (sin acciones) |

**`_autorizar_id(fid)`**

Llama a `POST /api/facturas/{id}/autorizar` usando `LoadWorker` para no bloquear la UI. Al terminar muestra toast con el resultado y recarga la tabla.

---

## 11. Base de Datos — `server/database/models.py`

Modelos SQLAlchemy que mapean a la base de datos SQLite.

### `Empresa`

Tabla `empresa`. Datos fiscales y de configuración de cada empresa.

| Campo | Tipo | Descripción |
|---|---|---|
| `ruc` | String(13) | RUC único |
| `ambiente` | Integer | 1=Pruebas, 2=Producción |
| `establecimiento` | String(3) | Ej: `"001"` |
| `punto_emision` | String(3) | Ej: `"001"` |
| `fe_url` | String(500) | URL del servicio de firma/SRI (Amelia) |
| `pdf_url` | String(500) | URL del servicio generador de RIDE PDF |
| `nombre_archivo_firma` | String(255) | Nombre del archivo `.p12` |
| `clave_firma` | String(255) | Contraseña del certificado |

**`get_serie() → str`**  
Devuelve `"001-001"` (establecimiento-punto_emision).

**`get_ambiente_nombre() → str`**  
Devuelve `"PRUEBAS"` o `"PRODUCCIÓN"`.

---

### `Usuario`

Tabla `usuario`. Roles: `superadmin`, `admin`, `vendedor`.

**`set_password(password)`**  
Genera hash bcrypt y lo guarda en `password_hash`.

**`check_password(password) → bool`**  
Verifica la contraseña contra el hash.

**`nombre_completo() → str`**  
Devuelve `"Nombre Apellido"`.

**`es_admin() → bool`**  
`True` si el rol es `admin` o `superadmin`.

---

### `Cliente` / `Proveedor`

Comparten la misma estructura de identificación.

**`TIPOS_IDENTIFICACION`** (dict de clase):

| Código | Tipo |
|---|---|
| `'04'` | RUC |
| `'05'` | Cédula |
| `'06'` | Pasaporte |
| `'07'` | Consumidor Final (solo Cliente) |
| `'08'` | Identificación Exterior |

**`get_tipo_nombre() → str`**  
Devuelve el nombre legible del tipo de identificación.

---

### `Factura` / `DetalleFactura`

Tabla `factura` con relación 1:N a `detalle_factura`.

**`get_numero_formateado() → str`**  
Devuelve el número en formato SRI: `"001-001-000000001"`.

**Estados posibles:** `PENDIENTE`, `AUTORIZADO`, `NO_AUTORIZADO`, `ANULADO`.

**Campos de totales:**

| Campo | Descripción |
|---|---|
| `subtotal_sin_impuesto` | Suma de todos los subtotales |
| `subtotal_iva_0` | Base gravada a 0% |
| `subtotal_iva_5` | Base gravada a 5% |
| `subtotal_iva_12` | Base gravada a 12% |
| `subtotal_iva_15` | Base gravada a 15% |
| `iva_5 / iva_12 / iva_15` | Valor del IVA calculado |
| `total` | Total final a pagar |

---

### `Retencion` / `DetalleRetencion`

`DetalleRetencion` contiene un registro por cada impuesto retenido (renta o IVA) por documento sustento.

| Campo de detalle | Descripción |
|---|---|
| `codigo_sustento` | Código sustento tributario (ej: `"01"`) |
| `cod_doc_sustento` | Tipo de doc sustento (`"01"`=factura) |
| `tipo_retencion` | `"renta"` o `"iva"` |
| `codigo_retencion` | Código del porcentaje de retención |
| `porcentaje_retener` | % a retener |
| `valor_retenido` | Valor calculado retenido |

---

### `NotaCredito` / `NotaDebito`

Ambas referencian el documento que modifican mediante:
- `tipo_doc_modificado` — código de documento (`"01"` = factura)
- `num_doc_modificado` — número de la factura original
- `fecha_doc_sustento` — fecha de emisión de la factura original
- `motivo` — razón del ajuste

`DetalleNotaDebito` solo tiene `razon` y `valor` (sin productos).

---

### `GuiaRemision` / `DestinatarioGuia` / `DetalleGuia`

Estructura jerárquica de 3 niveles:
```
GuiaRemision
  └── DestinatarioGuia (1..N)
        └── DetalleGuia (1..N productos por destinatario)
```

---

### `CompraProveedor`

Registro de facturas recibidas de proveedores. No genera documentos electrónicos propios, solo almacena la información para control de gastos.

---

## 12. Servicios — `server/services/clave_acceso.py`

Generación de claves de acceso SRI de 49 dígitos.

### `CODIGOS_DOCUMENTO`

```python
{
    'factura':       '01',
    'liquidacion':   '03',
    'nota_credito':  '04',
    'nota_debito':   '05',
    'guia_remision': '06',
    'retencion':     '07',
}
```

---

### `generar_digito_verificador(clave_48: str) → str`

Calcula el dígito verificador (posición 49) usando módulo 11.

**Algoritmo:**
1. Recorre los 48 dígitos de derecha a izquierda.
2. Multiplica cada dígito por factores ciclicos `[2, 3, 4, 5, 6, 7]`.
3. Suma todos los productos.
4. Calcula `residuo = suma % 11`.
5. Si `residuo == 0` → `'0'`, si `residuo == 1` → `'1'`, si no → `str(11 - residuo)`.

---

### `generar_clave_acceso(fecha, tipo_documento, ruc, ambiente, establecimiento, punto_emision, secuencial, codigo_numerico=None) → str`

Construye la clave de acceso completa de 49 dígitos.

**Estructura de los 48 dígitos base:**

| Posición | Longitud | Contenido |
|---|---|---|
| 1-8 | 8 | `ddMMyyyy` (fecha de emisión) |
| 9-10 | 2 | Código de documento (ej: `01`) |
| 11-23 | 13 | RUC del emisor |
| 24 | 1 | Ambiente (1=pruebas, 2=producción) |
| 25-30 | 6 | Establecimiento (3) + Punto emisión (3) |
| 31-39 | 9 | Secuencial con ceros a la izquierda |
| 40-47 | 8 | Código numérico aleatorio |
| 48 | 1 | Tipo de emisión (siempre `1` = normal) |
| **49** | **1** | **Dígito verificador módulo 11** |

---

## 13. Servicios — `server/services/xml_generator.py`

Genera los XMLs de cada tipo de comprobante según el esquema del SRI.

### `_escape(valor) → str`

Escapa caracteres especiales XML (`&`, `<`, `>`, `"`, `'`). Convierte `None` a cadena vacía.

---

### `_fmt_fecha(d) → str`

Formatea una fecha a `dd/MM/yyyy` (formato requerido por el SRI en los XML).

---

### `_info_tributaria(empresa, cod_doc, clave_acceso, establecimiento, punto_emision, secuencial) → str`

Genera el bloque `<infoTributaria>` común a todos los comprobantes. Incluye condicionalmente:
- `<nombreComercial>` si existe.
- `<agenteRetencion>1</agenteRetencion>` si aplica.
- `<contribuyenteRimpe>` si aplica.

---

### `generar_xml_factura(empresa, cliente, factura, detalles) → str`

Genera el XML completo de una factura de venta v1.1.0.

**Estructura XML:**
```xml
<factura id="comprobante" version="1.1.0">
  <infoTributaria>...</infoTributaria>
  <infoFactura>
    <totalConImpuestos>
      <!-- Un bloque por cada tarifa con base > 0 -->
    </totalConImpuestos>
    <pagos>...</pagos>
  </infoFactura>
  <detalles>
    <detalle>...</detalle> <!-- Un bloque por item -->
  </detalles>
  <infoAdicional>...</infoAdicional> <!-- Solo si cliente tiene email -->
</factura>
```

---

### `generar_xml_retencion(empresa, proveedor, retencion, detalles) → str`

Genera el XML v2.0.0 de un comprobante de retención. Agrupa los detalles por documento sustento (`num_doc_sustento`), generando un `<docSustento>` por cada factura retenida.

---

### `generar_xml_nota_credito(empresa, cliente, nota, detalles) → str`

XML v1.1.0 de nota de crédito. Incluye referencia al documento modificado mediante `<codDocModificado>` y `<numDocModificado>`.

---

### `generar_xml_nota_debito(empresa, cliente, nota, detalles) → str`

XML v1.0.0 de nota de débito. Los ítems se codifican como `<motivos>` con `<razon>` y `<valor>` (no como productos detallados).

---

### `generar_xml_guia_remision(empresa, guia, destinatarios) → str`

XML v1.0.0 de guía de remisión. El tipo de identificación del transportista se determina automáticamente por la longitud: 13 dígitos = RUC (`04`), otros = cédula (`05`).

---

### `generar_xml_liquidacion(empresa, proveedor, liquidacion, detalles) → str`

XML v1.1.0 de liquidación de compra. Igual estructura que factura pero para el proveedor.

---

## 14. Servicios — `server/services/sri_service.py`

Comunicación con el servicio externo de firma y SRI (Amelia).

### `firmar_xml(fe_url, xml_content, ruta_firma, clave_firma, ruta_xml_sin_firmar, ruta_xml_firmado) → dict`

1. Guarda el XML sin firmar en disco.
2. Llama a `POST {fe_url}/api/facturacion/FirmaXml` con el payload:
   ```json
   {
     "pathXml": "/ruta/al/sin_firmar.xml",
     "pathXmlFirmado": "/ruta/al/firmado.xml",
     "pathFirma": "/ruta/al/certificado.p12",
     "claveFirma": "contraseña"
   }
   ```
3. El servicio firma el XML en disco y devuelve confirmación.

**Retorna:** `{'ok': True, 'ruta_firmado': ruta}` o `{'ok': False, 'error': msg}`.

---

### `recepcionar_sri(fe_url, ruta_xml_firmado) → dict`

Envía el XML firmado al SRI para recepción.

**Endpoint:** `POST {fe_url}/api/facturacion/Recepcion`

**Payload:**
```json
{"pathXmlFirmado": "/ruta/al/firmado.xml"}
```

**Retorna:** `{'ok': True, 'respuesta': 'RECIBIDA'}` o `{'ok': False, 'error': msg}`.

**Respuestas posibles del SRI:** `RECIBIDA`, `DEVUELTA`, `ERROR`.

---

### `autorizar_sri(fe_url, ruta_xml_firmado, clave_acceso, ruta_xml_autorizado) → dict`

Solicita la autorización del comprobante al SRI.

**Endpoint:** `POST {fe_url}/api/facturacion/Autorizacion`

**Payload:**
```json
{
  "pathXmlFirmado": "/ruta/al/firmado.xml",
  "ClaveAcceso": "4902202601...",
  "PathXmlAutorizado": "/ruta/al/autorizado.xml"
}
```

El servicio guarda el XML autorizado en disco y devuelve la fecha de autorización.

---

### `generar_pdf(pdf_url, tipo, datos) → dict`

Solicita el RIDE (representación impresa) al servicio PDF.

**Endpoint:** `POST {pdf_url}/{tipo}`

| `tipo` | Documento |
|---|---|
| `factura` | Factura de venta |
| `nota-credito` | Nota de crédito |
| `nota-debito` | Nota de débito |
| `retencion` | Comprobante de retención |
| `guia` | Guía de remisión |
| `liquidacion` | Liquidación de compra |

**Retorna:** `{'ok': True, 'content': bytes_pdf}` o `{'ok': False, 'error': msg}`.

---

### `procesar_documento(empresa, xml_content, tipo_doc, clave_acceso, base_dir) → dict`

Flujo completo de autorización: **firmar → recepcionar → esperar → autorizar**.

**Parámetros:**
- `empresa` — instancia del modelo `Empresa`
- `xml_content` — XML generado por `xml_generator`
- `tipo_doc` — código de carpeta: `'FV'`, `'RE'`, `'NC'`, etc.
- `clave_acceso` — los 49 dígitos
- `base_dir` — directorio raíz de la app (para rutas de archivos)

**Validaciones previas:**
- `empresa.fe_url` configurada
- `empresa.nombre_archivo_firma` configurado
- `empresa.clave_firma` configurada
- El archivo `.p12` existe en `{base_dir}/private/firmas/`

**Estructura de directorios XML:**
```
{base_dir}/private/xml/{ruc}/{tipo_doc}/
  ├── sin_firmar/  {clave_acceso}.xml
  ├── firmado/     {clave_acceso}_firmado.xml
  └── autorizado/  {clave_acceso}.xml
```

**Espera 3 segundos** entre recepción y autorización (requisito del SRI).

**Retorna en éxito:**
```python
{
    'ok': True,
    'numero_autorizacion': clave_acceso,  # El SRI usa la clave como número
    'fecha_autorizacion': '2024-01-15T...',
    'xml_firmado_path': '/ruta/firmado.xml',
    'xml_autorizado_path': '/ruta/autorizado.xml',
}
```

---

## 15. API Routes — `server/api/auth.py`

### `POST /api/auth/login`

**Función:** `login()`

Autentica al usuario. Busca por email (insensible a mayúsculas) y verifica la contraseña con bcrypt.

**Request:**
```json
{"email": "admin@empresa.com", "password": "Admin2024#"}
```

**Response exitosa:**
```json
{
  "ok": true,
  "usuario": {
    "id": 1,
    "nombre": "Juan Pérez",
    "email": "admin@empresa.com",
    "rol": "admin",
    "empresa_id": 1,
    "empresa_ruc": "1234567890001",
    "empresa_nombre": "Mi Empresa S.A."
  }
}
```

**Response fallida (401):**
```json
{"ok": false, "error": "Credenciales incorrectas"}
```

---

### `GET /api/auth/empresas`

**Función:** `listar_empresas_login()`

Lista empresas activas. Requiere header `X-User-Rol: superadmin`. Excluye la empresa con RUC `9999999999999` (empresa de sistema).

---

## 16. API Routes — `server/api/facturas.py`

### Función interna: `_siguiente_numero(empresa_id) → int`

Calcula el siguiente número secuencial de factura para la empresa. Usa `MAX(numero) + 1`. Si no hay facturas, devuelve `1`.

---

### `GET /api/facturas/{empresa_id}`

**Función:** `listar(empresa_id)`

Lista facturas de la empresa. Soporta filtros por query string:

| Parámetro | Tipo | Descripción |
|---|---|---|
| `q` | string | Busca en `razon_social` e `identificacion` del cliente |
| `estado` | string | Filtra por `PENDIENTE`, `AUTORIZADO`, etc. |

Devuelve máximo 200 registros ordenados por fecha descendente.

---

### `GET /api/facturas/{id}` — detalle

**Función:** `obtener(id)`

Devuelve la factura completa con todos sus detalles.

---

### `POST /api/facturas/`

**Función:** `crear()`

Crea una nueva factura. Calcula automáticamente el número secuencial, la clave de acceso, y los totales por tarifa de IVA.

**Request body:**
```json
{
  "empresa_id": 1,
  "usuario_id": 1,
  "cliente_id": 5,
  "fecha_emision": "2024-01-15",
  "forma_pago": "01",
  "observacion": "Opcional",
  "detalles": [
    {
      "producto_id": 3,
      "codigo_principal": "PROD001",
      "descripcion": "Laptop HP 14",
      "cantidad": 1,
      "precio_unitario": 800.00,
      "descuento": 0,
      "impuesto_codigo": "2",
      "impuesto_codigo_porcentaje": "2",
      "impuesto_tarifa": 12,
      "impuesto_valor": 96.00
    }
  ]
}
```

**Códigos de porcentaje IVA:**

| Código | Tarifa |
|---|---|
| `"0"` | 0% |
| `"5"` | 5% |
| `"2"` | 12% |
| `"4"` | 15% |

**Response (201):**
```json
{"ok": true, "data": {...factura completa con detalles...}}
```

---

### `POST /api/facturas/{id}/autorizar`

**Función:** `autorizar(id)`

Ejecuta el flujo completo SRI: genera XML → firma → recepciona → autoriza. 

Si ya está autorizada devuelve error 400.

**Response éxito:**
```json
{
  "ok": true,
  "data": {
    "estado": "AUTORIZADO",
    "numero_autorizacion": "4901202401...",
    "fecha_autorizacion": "2024-01-15 10:30:00"
  }
}
```

**Response error (422):**
```json
{"ok": false, "error": "Error al firmar: connection refused"}
```

---

### `POST /api/facturas/{id}/anular`

**Función:** `anular(id)`

Marca la factura como `ANULADO`. No notifica al SRI (la anulación formal se hace directamente en el portal SRI).

---

### `GET /api/facturas/{id}/xml`

**Función:** `descargar_xml(id)`

Descarga el XML. Si existe el XML autorizado en disco lo devuelve; si no, regenera el XML sin firmar al vuelo.

**Content-Type:** `application/xml`  
**Nombre de archivo:** `{clave_acceso}.xml`

---

### `GET /api/facturas/{id}/pdf`

**Función:** `descargar_pdf(id)`

Genera y descarga el RIDE PDF a través del servicio PDF externo.

**Content-Type:** `application/pdf`  
**Nombre de archivo:** `RIDE_{clave_acceso}.pdf`

---

## 17. API Routes — Catálogos

Todos los endpoints de catálogo siguen el patrón CRUD estándar:

### Productos — `/api/productos/{empresa_id}`

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/productos/{empresa_id}` | Lista productos, filtra con `?q=` y `?activo=true` |
| `GET` | `/api/productos/{id}` | Obtiene un producto |
| `POST` | `/api/productos/` | Crea producto |
| `PUT` | `/api/productos/{id}` | Actualiza producto |
| `DELETE` | `/api/productos/{id}` | Desactiva producto (soft delete) |

### Clientes — `/api/clientes/{empresa_id}`

Igual estructura. Búsqueda por `razon_social` e `identificacion`.

### Proveedores — `/api/proveedores/{empresa_id}`

Igual estructura.

### Categorías — `/api/categorias/{empresa_id}`

Igual estructura.

### Impuestos — `/api/impuestos/{empresa_id}`

Igual estructura. Campo clave: `codigo_porcentaje` (`"0"`, `"5"`, `"2"`, `"4"`).

### Usuarios — `/api/usuarios/{empresa_id}`

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/usuarios/{empresa_id}` | Lista usuarios de la empresa |
| `POST` | `/api/usuarios/` | Crea usuario (hash bcrypt automático) |
| `PUT` | `/api/usuarios/{id}` | Actualiza datos y/o contraseña |
| `DELETE` | `/api/usuarios/{id}` | Desactiva usuario |

### Empresas — `/api/empresas/`

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/empresas/` | Lista todas las empresas |
| `GET` | `/api/empresas/{id}` | Obtiene una empresa |
| `POST` | `/api/empresas/` | Crea empresa |
| `PUT` | `/api/empresas/{id}` | Actualiza empresa |

---

*Generado automáticamente — Facturador Electrónico v1.0.0*
