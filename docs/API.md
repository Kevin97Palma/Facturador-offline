# Documentación de la API REST — Facturador Electrónico SRI Ecuador

> **Base URL del servidor:** `http://{IP_SERVIDOR}:5000`  
> **Versión:** 1.0.0  
> **Formato:** JSON (Content-Type: application/json)  
> **Autenticación:** Bearer Token en header `Authorization`

---

## Índice

1. [Autenticación](#1-autenticación)
2. [Convenciones de respuesta](#2-convenciones-de-respuesta)
3. [Empresas](#3-empresas)
4. [Usuarios](#4-usuarios)
5. [Catálogos — Categorías](#5-catálogos--categorías)
6. [Catálogos — Impuestos](#6-catálogos--impuestos)
7. [Catálogos — Productos](#7-catálogos--productos)
8. [Catálogos — Clientes](#8-catálogos--clientes)
9. [Catálogos — Proveedores](#9-catálogos--proveedores)
10. [Facturas de Venta](#10-facturas-de-venta)
11. [Retenciones](#11-retenciones)
12. [Notas de Crédito](#12-notas-de-crédito)
13. [Notas de Débito](#13-notas-de-débito)
14. [Guías de Remisión](#14-guías-de-remisión)
15. [Liquidaciones de Compra](#15-liquidaciones-de-compra)
16. [Compras de Proveedores](#16-compras-de-proveedores)
17. [Archivos — XML y PDF](#17-archivos--xml-y-pdf)
18. [Tablas de referencia SRI](#18-tablas-de-referencia-sri)
19. [Flujo completo de autorización](#19-flujo-completo-de-autorización)
20. [Ejemplos con Python requests](#20-ejemplos-con-python-requests)

---

## 1. Autenticación

### `POST /api/auth/login`

Inicia sesión y obtiene el token de acceso.

**Request:**
```json
{
  "email": "admin@empresa.com",
  "password": "Admin2024#"
}
```

**Response exitosa `200`:**
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

**Response error `401`:**
```json
{
  "ok": false,
  "error": "Credenciales incorrectas"
}
```

> **Nota de implementación actual:** El servidor devuelve los datos del usuario en la respuesta de login. El cliente almacena esta información en memoria para las peticiones siguientes. En una versión con tokens JWT, el campo `token` se incluiría aquí.

---

### `GET /api/auth/empresas`

Lista empresas activas. Solo para superadmin.

**Header requerido:**
```
X-User-Rol: superadmin
```

**Response `200`:**
```json
{
  "ok": true,
  "empresas": [
    {"id": 1, "ruc": "1234567890001", "razon_social": "Mi Empresa S.A."},
    {"id": 2, "ruc": "0987654321001", "razon_social": "Otra Empresa Cía."}
  ]
}
```

---

## 2. Convenciones de respuesta

Todas las respuestas tienen la misma estructura base:

```json
{
  "ok": true | false,
  "data": {...} | [...],   // Presente en éxito
  "error": "mensaje"       // Presente en error
}
```

| HTTP Status | Significado |
|---|---|
| `200` | OK — operación exitosa |
| `201` | Created — recurso creado |
| `400` | Bad Request — parámetros inválidos |
| `401` | Unauthorized — no autenticado |
| `403` | Forbidden — sin permisos |
| `404` | Not Found — recurso no existe |
| `422` | Unprocessable — error de negocio (ej: SRI rechazó) |
| `500` | Internal Server Error |

---

## 3. Empresas

### `GET /api/empresas/`

Lista todas las empresas.

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 1,
      "ruc": "1234567890001",
      "razon_social": "Mi Empresa S.A.",
      "nombre_comercial": "MiEmpresa",
      "direccion": "Av. Principal 123",
      "telefono": "023456789",
      "email": "info@empresa.com",
      "establecimiento": "001",
      "punto_emision": "001",
      "ambiente": 1,
      "ambiente_nombre": "PRUEBAS",
      "obligado_contabilidad": false,
      "agente_retencion": false,
      "contribuyente_especial": false,
      "contribuyente_rimpe": false,
      "fe_url": "http://amelia:8080",
      "pdf_url": "http://amelia:8081",
      "activo": true
    }
  ]
}
```

---

### `GET /api/empresas/{id}`

Obtiene una empresa por ID.

---

### `POST /api/empresas/`

Crea una nueva empresa.

**Request:**
```json
{
  "ruc": "1234567890001",
  "razon_social": "Mi Empresa S.A.",
  "nombre_comercial": "MiEmpresa",
  "direccion": "Av. Principal 123",
  "telefono": "023456789",
  "email": "info@empresa.com",
  "establecimiento": "001",
  "punto_emision": "001",
  "ambiente": 1,
  "obligado_contabilidad": false,
  "agente_retencion": false,
  "contribuyente_especial": false,
  "num_resolucion_contrib_especial": "",
  "contribuyente_rimpe": false,
  "texto_regimen": "",
  "nombre_archivo_firma": "firma.p12",
  "clave_firma": "contraseña123",
  "fe_url": "http://192.168.1.10:8080",
  "pdf_url": "http://192.168.1.10:8081"
}
```

**Response `201`:**
```json
{"ok": true, "data": {...empresa creada...}}
```

---

### `PUT /api/empresas/{id}`

Actualiza una empresa. Enviar solo los campos a modificar.

---

## 4. Usuarios

### `GET /api/usuarios/{empresa_id}`

Lista usuarios de una empresa.

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 1,
      "empresa_id": 1,
      "nombre": "Juan",
      "apellido": "Pérez",
      "email": "juan@empresa.com",
      "rol": "admin",
      "activo": true
    }
  ]
}
```

---

### `POST /api/usuarios/`

Crea un nuevo usuario.

**Request:**
```json
{
  "empresa_id": 1,
  "nombre": "María",
  "apellido": "García",
  "email": "maria@empresa.com",
  "password": "Clave$egura123",
  "rol": "vendedor"
}
```

**Roles válidos:** `superadmin`, `admin`, `vendedor`

---

### `PUT /api/usuarios/{id}`

Actualiza datos del usuario. Si se incluye `password`, se actualiza el hash.

**Request:**
```json
{
  "nombre": "María",
  "apellido": "García López",
  "email": "maria.garcia@empresa.com",
  "rol": "admin",
  "activo": true,
  "password": "NuevaClave$123"  // Opcional
}
```

---

### `DELETE /api/usuarios/{id}`

Desactiva el usuario (soft delete, `activo = false`).

---

## 5. Catálogos — Categorías

### `GET /api/categorias/{empresa_id}`

Lista categorías de la empresa.

**Query params:** `?q=texto` para buscar por nombre.

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 1,
      "empresa_id": 1,
      "nombre": "Electrónica",
      "descripcion": "Productos electrónicos",
      "activo": true
    }
  ]
}
```

---

### `POST /api/categorias/`

```json
{
  "empresa_id": 1,
  "nombre": "Electrodomésticos",
  "descripcion": "Línea blanca y electrodomésticos"
}
```

---

### `PUT /api/categorias/{id}`

```json
{"nombre": "Electrónica y Tecnología", "descripcion": "..."}
```

---

### `DELETE /api/categorias/{id}`

Desactiva la categoría.

---

## 6. Catálogos — Impuestos

### `GET /api/impuestos/{empresa_id}`

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 1,
      "empresa_id": 1,
      "nombre": "IVA 12%",
      "codigo": "2",
      "codigo_porcentaje": "2",
      "porcentaje": 12.00,
      "activo": true
    }
  ]
}
```

**Tabla de código de porcentajes:**

| `codigo_porcentaje` | Tarifa | `codigo` |
|---|---|---|
| `"0"` | 0% IVA | `"2"` |
| `"5"` | 5% IVA | `"2"` |
| `"2"` | 12% IVA | `"2"` |
| `"4"` | 15% IVA | `"2"` |

---

### `POST /api/impuestos/`

```json
{
  "empresa_id": 1,
  "nombre": "IVA 15%",
  "codigo": "2",
  "codigo_porcentaje": "4",
  "porcentaje": 15.00
}
```

---

## 7. Catálogos — Productos

### `GET /api/productos/{empresa_id}`

**Query params:**
- `?q=texto` — busca en código y nombre
- `?activo=true` — filtra solo activos

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 3,
      "empresa_id": 1,
      "categoria_id": 1,
      "categoria_nombre": "Electrónica",
      "impuesto_id": 1,
      "impuesto_nombre": "IVA 12%",
      "impuesto_tarifa": 12.00,
      "impuesto_codigo_porcentaje": "2",
      "codigo": "PROD001",
      "nombre": "Laptop HP 14",
      "descripcion": "Laptop HP 14 pulgadas Intel Core i5",
      "precio_unitario": 800.00,
      "activo": true
    }
  ]
}
```

---

### `POST /api/productos/`

```json
{
  "empresa_id": 1,
  "categoria_id": 1,
  "impuesto_id": 1,
  "codigo": "PROD002",
  "nombre": "Mouse Inalámbrico",
  "descripcion": "Mouse ergonómico 2.4GHz",
  "precio_unitario": 25.00
}
```

---

### `PUT /api/productos/{id}`

```json
{
  "nombre": "Mouse Inalámbrico Ergonómico",
  "precio_unitario": 27.50,
  "activo": true
}
```

---

### `DELETE /api/productos/{id}`

Desactiva el producto.

---

## 8. Catálogos — Clientes

### `GET /api/clientes/{empresa_id}`

**Query params:** `?q=texto` — busca en `razon_social` e `identificacion`.

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 5,
      "empresa_id": 1,
      "tipo_identificacion": "04",
      "tipo_identificacion_nombre": "RUC",
      "identificacion": "0987654321001",
      "razon_social": "Comprador Empresa S.A.",
      "email": "compras@comprador.com",
      "telefono": "0998765432",
      "direccion": "Calle Secundaria 456",
      "activo": true
    }
  ]
}
```

**Tipos de identificación:**

| Código | Tipo |
|---|---|
| `"04"` | RUC (13 dígitos) |
| `"05"` | Cédula (10 dígitos) |
| `"06"` | Pasaporte |
| `"07"` | Consumidor Final |
| `"08"` | Identificación Exterior |

---

### `POST /api/clientes/`

```json
{
  "empresa_id": 1,
  "tipo_identificacion": "05",
  "identificacion": "1712345678",
  "razon_social": "Carlos López",
  "email": "carlos@gmail.com",
  "telefono": "0987654321",
  "direccion": "Av. Amazonas 789"
}
```

---

### `PUT /api/clientes/{id}`

```json
{
  "email": "nuevo@email.com",
  "telefono": "0991234567"
}
```

---

### `DELETE /api/clientes/{id}`

Desactiva el cliente.

---

## 9. Catálogos — Proveedores

### `GET /api/proveedores/{empresa_id}`

**Query params:** `?q=texto`

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 2,
      "empresa_id": 1,
      "tipo_identificacion": "04",
      "identificacion": "1790123456001",
      "razon_social": "Proveedor XYZ S.A.",
      "email": "ventas@proveedor.com",
      "telefono": "022345678",
      "direccion": "Parque Industrial, Nave 5",
      "activo": true
    }
  ]
}
```

---

### `POST /api/proveedores/`

```json
{
  "empresa_id": 1,
  "tipo_identificacion": "04",
  "identificacion": "1790123456001",
  "razon_social": "Proveedor XYZ S.A.",
  "email": "ventas@proveedor.com",
  "telefono": "022345678",
  "direccion": "Parque Industrial, Nave 5"
}
```

---

## 10. Facturas de Venta

### `GET /api/facturas/{empresa_id}`

Lista facturas de la empresa con búsqueda y filtro de estado.

**Query params:**
- `?q=texto` — busca en `razon_social` e `identificacion` del cliente
- `?estado=PENDIENTE` — filtra por estado

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 10,
      "empresa_id": 1,
      "cliente_id": 5,
      "cliente_nombre": "Carlos López",
      "cliente_identificacion": "1712345678",
      "numero": 1,
      "numero_formateado": "001-001-000000001",
      "clave_acceso": "1501202401012345678900112345678901234561",
      "fecha_emision": "2024-01-15",
      "total": 896.00,
      "estado": "AUTORIZADO",
      "numero_autorizacion": "1501202401012345678900112345678901234561",
      "created_at": "2024-01-15 10:30"
    }
  ]
}
```

---

### `GET /api/facturas/{id}`

Obtiene una factura con todos sus detalles.

**Response:**
```json
{
  "ok": true,
  "data": {
    "id": 10,
    "empresa_id": 1,
    "cliente_id": 5,
    "cliente_nombre": "Carlos López",
    "numero_formateado": "001-001-000000001",
    "fecha_emision": "2024-01-15",
    "forma_pago": "01",
    "observacion": "",
    "subtotal_sin_impuesto": 800.00,
    "subtotal_iva_0": 0.00,
    "subtotal_iva_5": 0.00,
    "subtotal_iva_12": 800.00,
    "subtotal_iva_15": 0.00,
    "iva_5": 0.00,
    "iva_12": 96.00,
    "iva_15": 0.00,
    "descuento_total": 0.00,
    "total": 896.00,
    "estado": "AUTORIZADO",
    "numero_autorizacion": "...",
    "fecha_autorizacion": "2024-01-15 10:30:00",
    "detalles": [
      {
        "id": 25,
        "producto_id": 3,
        "codigo_principal": "PROD001",
        "descripcion": "Laptop HP 14",
        "cantidad": 1.0000,
        "precio_unitario": 800.0000,
        "descuento": 0.00,
        "precio_total_sin_impuesto": 800.00,
        "impuesto_codigo": "2",
        "impuesto_codigo_porcentaje": "2",
        "impuesto_tarifa": 12.00,
        "impuesto_valor": 96.00
      }
    ]
  }
}
```

---

### `POST /api/facturas/`

Crea una nueva factura. El servidor calcula automáticamente el número secuencial y la clave de acceso.

**Request:**
```json
{
  "empresa_id": 1,
  "usuario_id": 1,
  "cliente_id": 5,
  "fecha_emision": "2024-01-15",
  "forma_pago": "01",
  "observacion": "Factura por compra de equipos",
  "detalles": [
    {
      "producto_id": 3,
      "codigo_principal": "PROD001",
      "descripcion": "Laptop HP 14",
      "cantidad": 2,
      "precio_unitario": 800.00,
      "descuento": 0,
      "impuesto_codigo": "2",
      "impuesto_codigo_porcentaje": "2",
      "impuesto_tarifa": 12,
      "impuesto_valor": 192.00
    },
    {
      "producto_id": null,
      "codigo_principal": "",
      "descripcion": "Servicio de instalación",
      "cantidad": 1,
      "precio_unitario": 50.00,
      "descuento": 0,
      "impuesto_codigo": "2",
      "impuesto_codigo_porcentaje": "0",
      "impuesto_tarifa": 0,
      "impuesto_valor": 0
    }
  ]
}
```

**Formas de pago SRI:**

| Código | Forma de pago |
|---|---|
| `"01"` | Sin utilización del sistema financiero (efectivo) |
| `"16"` | Tarjeta de débito |
| `"19"` | Tarjeta de crédito |
| `"20"` | Otros con utilización del sistema financiero |
| `"21"` | Endoso de títulos |

**Response `201`:**
```json
{"ok": true, "data": {...factura completa con detalles y clave_acceso generada...}}
```

---

### `POST /api/facturas/{id}/autorizar`

Envía la factura al SRI para autorización.

**Request:** Cuerpo vacío `{}` o sin cuerpo.

**Response éxito `200`:**
```json
{
  "ok": true,
  "data": {
    "estado": "AUTORIZADO",
    "numero_autorizacion": "1501202401012345678900112345678901234561",
    "fecha_autorizacion": "2024-01-15 10:30:00",
    ...
  }
}
```

**Response error `422`:**
```json
{
  "ok": false,
  "error": "Comprobante no autorizado por SRI: DEVUELTA - DESCRIPCION DEL ERROR"
}
```

---

### `POST /api/facturas/{id}/anular`

Anula la factura localmente.

**Response `200`:**
```json
{"ok": true}
```

---

### `GET /api/facturas/{id}/xml`

Descarga el XML de la factura.

**Response:** Archivo XML (`application/xml`)  
**Nombre:** `{clave_acceso}.xml`

---

### `GET /api/facturas/{id}/pdf`

Genera y descarga el RIDE PDF.

**Response:** Archivo PDF (`application/pdf`)  
**Nombre:** `RIDE_{clave_acceso}.pdf`

---

## 11. Retenciones

### `GET /api/retenciones/{empresa_id}`

**Query params:** `?q=texto`, `?estado=`

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 3,
      "proveedor_id": 2,
      "proveedor_nombre": "Proveedor XYZ S.A.",
      "proveedor_identificacion": "1790123456001",
      "numero_formateado": "001-001-000000001",
      "clave_acceso": "...",
      "fecha_emision": "2024-01-15",
      "periodo_fiscal": "01/2024",
      "total_retenido": 25.00,
      "estado": "PENDIENTE"
    }
  ]
}
```

---

### `POST /api/retenciones/`

```json
{
  "empresa_id": 1,
  "usuario_id": 1,
  "proveedor_id": 2,
  "fecha_emision": "2024-01-15",
  "periodo_fiscal": "01/2024",
  "detalles": [
    {
      "codigo_sustento": "01",
      "cod_doc_sustento": "01",
      "num_doc_sustento": "001-001-000000050",
      "fecha_emision_doc_sustento": "2024-01-10",
      "num_aut_doc_sustento": "1001202401...",
      "base_0_doc": 0.00,
      "base_iva_doc": 500.00,
      "total_doc": 560.00,
      "codigo_retencion": "303",
      "tipo_retencion": "renta",
      "base_imponible": 500.00,
      "porcentaje_retener": 1.75,
      "valor_retenido": 8.75
    },
    {
      "codigo_sustento": "01",
      "cod_doc_sustento": "01",
      "num_doc_sustento": "001-001-000000050",
      "fecha_emision_doc_sustento": "2024-01-10",
      "num_aut_doc_sustento": "1001202401...",
      "base_0_doc": 0.00,
      "base_iva_doc": 500.00,
      "total_doc": 560.00,
      "codigo_retencion": "725",
      "tipo_retencion": "iva",
      "base_imponible": 60.00,
      "porcentaje_retener": 30.00,
      "valor_retenido": 18.00
    }
  ]
}
```

**Campos de detalle:**

| Campo | Descripción |
|---|---|
| `codigo_sustento` | Código sustento tributario (`"01"` = compra bienes) |
| `cod_doc_sustento` | Tipo doc sustento (`"01"` = factura) |
| `num_doc_sustento` | Número del doc sustentado (ej: `"001-001-000000050"`) |
| `tipo_retencion` | `"renta"` o `"iva"` |
| `codigo_retencion` | Código del % de retención (ej: `"303"`, `"725"`) |
| `porcentaje_retener` | Porcentaje a retener |
| `valor_retenido` | `base_imponible * porcentaje_retener / 100` |

---

### `POST /api/retenciones/{id}/autorizar`

Mismo flujo que facturas.

---

### `GET /api/retenciones/{id}/xml`
### `GET /api/retenciones/{id}/pdf`

---

## 12. Notas de Crédito

### `GET /api/notas_credito/{empresa_id}`

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 5,
      "cliente_nombre": "Carlos López",
      "numero_formateado": "001-001-000000001",
      "fecha_emision": "2024-01-20",
      "num_doc_modificado": "001-001-000000001",
      "motivo": "Devolución de mercadería",
      "total": 200.00,
      "estado": "PENDIENTE"
    }
  ]
}
```

---

### `POST /api/notas_credito/`

```json
{
  "empresa_id": 1,
  "usuario_id": 1,
  "cliente_id": 5,
  "fecha_emision": "2024-01-20",
  "tipo_doc_modificado": "01",
  "num_doc_modificado": "001-001-000000001",
  "fecha_emision_doc_sustento": "2024-01-15",
  "motivo": "Devolución parcial de mercadería defectuosa",
  "detalles": [
    {
      "producto_id": 3,
      "codigo_principal": "PROD001",
      "descripcion": "Laptop HP 14 (devuelta)",
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

**`tipo_doc_modificado`:** Tipo del documento que se modifica (`"01"` = factura).

---

### `POST /api/notas_credito/{id}/autorizar`
### `GET /api/notas_credito/{id}/xml`
### `GET /api/notas_credito/{id}/pdf`

---

## 13. Notas de Débito

### `GET /api/notas_debito/{empresa_id}`

---

### `POST /api/notas_debito/`

> **Diferencia clave:** Los detalles son cargos adicionales con `razon` y `valor`, no productos.

```json
{
  "empresa_id": 1,
  "usuario_id": 1,
  "cliente_id": 5,
  "fecha_emision": "2024-01-20",
  "tipo_doc_modificado": "01",
  "num_doc_modificado": "001-001-000000001",
  "fecha_emision_doc_sustento": "2024-01-15",
  "motivo": "Intereses por mora",
  "detalles": [
    {
      "razon": "Intereses por pago tardío (30 días)",
      "valor": 50.00
    },
    {
      "razon": "Gastos de cobranza",
      "valor": 20.00
    }
  ]
}
```

---

### `POST /api/notas_debito/{id}/autorizar`
### `GET /api/notas_debito/{id}/xml`
### `GET /api/notas_debito/{id}/pdf`

---

## 14. Guías de Remisión

### `GET /api/guias/{empresa_id}`

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 2,
      "numero_formateado": "001-001-000000001",
      "fecha_emision": "2024-01-15",
      "ruc_transportista": "1790000001001",
      "razon_social_transportista": "Transportes Rápido S.A.",
      "placa": "PBA-1234",
      "fecha_ini_transporte": "2024-01-15",
      "fecha_fin_transporte": "2024-01-16",
      "num_destinatarios": 2,
      "estado": "AUTORIZADO"
    }
  ]
}
```

---

### `POST /api/guias/`

```json
{
  "empresa_id": 1,
  "usuario_id": 1,
  "fecha_emision": "2024-01-15",
  "dir_partida": "Av. Principal 123, Quito",
  "ruc_transportista": "1790000001001",
  "razon_social_transportista": "Transportes Rápido S.A.",
  "tipo_identificacion_transportista": "04",
  "fecha_ini_transporte": "2024-01-15",
  "fecha_fin_transporte": "2024-01-16",
  "placa": "PBA-1234",
  "destinatarios": [
    {
      "tipo_identificacion": "04",
      "identificacion": "0987654321001",
      "razon_social": "Cliente Destino S.A.",
      "direccion_destino": "Calle 10 y Av. 6, Guayaquil",
      "motivo_traslado": "Venta de mercadería",
      "cod_doc_sustento": "01",
      "num_doc_sustento": "001-001-000000010",
      "num_aut_doc_sustento": "1001202401...",
      "fecha_emision_doc_sustento": "2024-01-14",
      "detalles": [
        {
          "producto_id": 3,
          "codigo_interno": "PROD001",
          "descripcion": "Laptop HP 14",
          "cantidad": 5
        }
      ]
    }
  ]
}
```

---

### `POST /api/guias/{id}/autorizar`
### `GET /api/guias/{id}/xml`
### `GET /api/guias/{id}/pdf`

---

## 15. Liquidaciones de Compra

### `GET /api/liquidaciones/{empresa_id}`

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 1,
      "proveedor_nombre": "Pedro Artesano",
      "numero_formateado": "001-001-000000001",
      "fecha_emision": "2024-01-15",
      "total": 112.00,
      "estado": "PENDIENTE"
    }
  ]
}
```

---

### `POST /api/liquidaciones/`

Misma estructura que Facturas pero con `proveedor_id` en lugar de `cliente_id`.

```json
{
  "empresa_id": 1,
  "usuario_id": 1,
  "proveedor_id": 2,
  "fecha_emision": "2024-01-15",
  "forma_pago": "01",
  "observacion": "Compra de artesanías",
  "detalles": [
    {
      "producto_id": null,
      "codigo_principal": "",
      "descripcion": "Artesanía en madera tallada",
      "cantidad": 10,
      "precio_unitario": 10.00,
      "descuento": 0,
      "impuesto_codigo": "2",
      "impuesto_codigo_porcentaje": "2",
      "impuesto_tarifa": 12,
      "impuesto_valor": 12.00
    }
  ]
}
```

---

### `POST /api/liquidaciones/{id}/autorizar`
### `GET /api/liquidaciones/{id}/xml`
### `GET /api/liquidaciones/{id}/pdf`

---

## 16. Compras de Proveedores

Registro de facturas **recibidas** de proveedores. No genera documentos electrónicos propios.

### `GET /api/compras/{empresa_id}`

**Query params:** `?q=texto` — busca en `razon_social_proveedor` y `numero_documento`.

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 7,
      "proveedor_id": 2,
      "proveedor_nombre": "Proveedor XYZ S.A.",
      "tipo_documento": "01",
      "tipo_documento_nombre": "Factura",
      "numero_documento": "001-001-000000100",
      "numero_autorizacion": "1001202401...",
      "fecha_emision": "2024-01-10",
      "ruc_proveedor": "1790123456001",
      "razon_social_proveedor": "Proveedor XYZ S.A.",
      "subtotal_sin_iva": 500.00,
      "subtotal_iva_0": 0.00,
      "subtotal_iva_12": 500.00,
      "iva": 60.00,
      "total": 560.00,
      "observacion": ""
    }
  ]
}
```

---

### `POST /api/compras/`

```json
{
  "empresa_id": 1,
  "proveedor_id": 2,
  "tipo_documento": "01",
  "numero_documento": "001-001-000000100",
  "numero_autorizacion": "1001202401...",
  "fecha_emision": "2024-01-10",
  "ruc_proveedor": "1790123456001",
  "razon_social_proveedor": "Proveedor XYZ S.A.",
  "subtotal_sin_iva": 500.00,
  "subtotal_iva_0": 0.00,
  "subtotal_iva_12": 500.00,
  "iva": 60.00,
  "total": 560.00,
  "xml_content": "<factura>...</factura>",
  "observacion": "Compra de insumos de oficina"
}
```

**Tipos de documento:**

| Código | Tipo |
|---|---|
| `"01"` | Factura |
| `"03"` | Liquidación de Compra |
| `"04"` | Nota de Crédito |
| `"05"` | Nota de Débito |

---

### `PUT /api/compras/{id}`

Actualiza una compra registrada.

---

### `DELETE /api/compras/{id}`

Elimina el registro de compra.

---

## 17. Archivos — XML y PDF

### `GET /api/archivos/xml/{filename}`

Descarga un archivo XML almacenado por nombre.

**Parámetro:** `filename` — nombre del archivo sin extensión o con `.xml`.

**Seguridad:** El servidor valida que el nombre no contenga `..` o `/` para prevenir path traversal.

**Response:** Archivo XML (`application/xml`).

---

## 18. Tablas de referencia SRI

### Tipos de identificación

| Código | Descripción |
|---|---|
| `04` | RUC |
| `05` | Cédula de identidad |
| `06` | Pasaporte |
| `07` | Consumidor final |
| `08` | Identificación del exterior |

---

### Tipos de comprobante

| Código | Comprobante |
|---|---|
| `01` | Factura |
| `03` | Liquidación de compra |
| `04` | Nota de crédito |
| `05` | Nota de débito |
| `06` | Guía de remisión |
| `07` | Comprobante de retención |

---

### Códigos de porcentaje IVA

| Código | Tarifa | Uso |
|---|---|---|
| `0` | 0% | Bienes/servicios exentos |
| `2` | 12% | Tarifa general |
| `4` | 15% | Bebidas alcohólicas, tabaco, etc. |
| `5` | 5% | Algunos bienes de primera necesidad |
| `6` | No objeto de IVA | |
| `7` | Exento de IVA | |

---

### Ambiente

| Código | Descripción |
|---|---|
| `1` | Pruebas (SRI sandbox) |
| `2` | Producción |

---

### Estados de documento

| Estado | Descripción |
|---|---|
| `PENDIENTE` | Creado, aún no enviado al SRI |
| `AUTORIZADO` | Autorizado por el SRI |
| `NO_AUTORIZADO` | Rechazado por el SRI |
| `ANULADO` | Anulado manualmente |

---

### Formas de pago

| Código | Descripción |
|---|---|
| `01` | Sin utilización del sistema financiero (efectivo) |
| `15` | Compensación de deudas |
| `16` | Tarjeta de débito |
| `17` | Dinero electrónico |
| `18` | Tarjeta prepago |
| `19` | Tarjeta de crédito |
| `20` | Otros con utilización del sistema financiero |
| `21` | Endoso de títulos |

---

## 19. Flujo completo de autorización

El flujo para autorizar cualquier documento electrónico es el mismo:

```
[Cliente] POST /api/facturas/             → Crea la factura (estado: PENDIENTE)
           ↓
[Cliente] POST /api/facturas/{id}/autorizar
           ↓
[Servidor] generar_xml_factura(...)       → XML según esquema SRI
           ↓
[Servidor] POST {fe_url}/api/facturacion/FirmaXml
           → Firma el XML con el certificado .p12
           ↓
[Servidor] POST {fe_url}/api/facturacion/Recepcion
           → SRI recibe el XML firmado → responde RECIBIDA
           ↓
[Servidor] sleep(3 segundos)              → Tiempo de procesamiento SRI
           ↓
[Servidor] POST {fe_url}/api/facturacion/Autorizacion
           → SRI autoriza → devuelve fecha_autorizacion
           ↓
[Servidor] Guarda estado=AUTORIZADO, numero_autorizacion, fecha_autorizacion
           ↓
[Cliente]  Recibe respuesta con datos completos
```

**Diagrama de estados:**

```
PENDIENTE ──→ AUTORIZADO
    │              │
    └──→ NO_AUTORIZADO
    │
    └──→ ANULADO (manual)
```

---

## 20. Ejemplos con Python requests

### Ejemplo completo: Login + Crear factura + Autorizar

```python
import requests

BASE = "http://192.168.1.100:5000"

# 1. Login
resp = requests.post(f"{BASE}/api/auth/login", json={
    "email": "admin@empresa.com",
    "password": "Admin2024#"
})
data = resp.json()
assert data['ok'], data['error']
usuario = data['usuario']
empresa_id = usuario['empresa_id']
usuario_id = usuario['id']
print(f"Conectado como: {usuario['nombre']} | Empresa: {usuario['empresa_nombre']}")

# 2. Buscar cliente por cédula
resp = requests.get(f"{BASE}/api/clientes/{empresa_id}", params={"q": "1712345678"})
clientes = resp.json()['data']
if not clientes:
    # Crear cliente si no existe
    resp = requests.post(f"{BASE}/api/clientes/", json={
        "empresa_id": empresa_id,
        "tipo_identificacion": "05",
        "identificacion": "1712345678",
        "razon_social": "Carlos López",
        "email": "carlos@gmail.com",
        "telefono": "0987654321",
        "direccion": "Av. Amazonas 789"
    })
    cliente_id = resp.json()['data']['id']
else:
    cliente_id = clientes[0]['id']

# 3. Buscar producto por código
resp = requests.get(f"{BASE}/api/productos/{empresa_id}", params={"q": "PROD001"})
producto = resp.json()['data'][0]

# 4. Crear la factura
factura_payload = {
    "empresa_id": empresa_id,
    "usuario_id": usuario_id,
    "cliente_id": cliente_id,
    "fecha_emision": "2024-01-15",
    "forma_pago": "01",
    "detalles": [
        {
            "producto_id": producto['id'],
            "codigo_principal": producto['codigo'],
            "descripcion": producto['nombre'],
            "cantidad": 2,
            "precio_unitario": float(producto['precio_unitario']),
            "descuento": 0,
            "impuesto_codigo": "2",
            "impuesto_codigo_porcentaje": producto['impuesto_codigo_porcentaje'],
            "impuesto_tarifa": float(producto['impuesto_tarifa']),
            "impuesto_valor": round(float(producto['precio_unitario']) * 2 * float(producto['impuesto_tarifa']) / 100, 2)
        }
    ]
}

resp = requests.post(f"{BASE}/api/facturas/", json=factura_payload)
factura = resp.json()
assert factura['ok'], factura.get('error')
factura_id = factura['data']['id']
print(f"Factura creada: {factura['data']['numero_formateado']} | Total: ${factura['data']['total']}")

# 5. Autorizar
resp = requests.post(f"{BASE}/api/facturas/{factura_id}/autorizar")
resultado = resp.json()
if resultado['ok']:
    print(f"Autorizada! Número: {resultado['data']['numero_autorizacion']}")
else:
    print(f"Error: {resultado['error']}")

# 6. Descargar PDF
resp = requests.get(f"{BASE}/api/facturas/{factura_id}/pdf")
if resp.status_code == 200:
    with open(f"RIDE_{factura_id}.pdf", "wb") as f:
        f.write(resp.content)
    print("PDF descargado")
```

---

### Ejemplo: Crear retención

```python
resp = requests.post(f"{BASE}/api/retenciones/", json={
    "empresa_id": 1,
    "usuario_id": 1,
    "proveedor_id": 2,
    "fecha_emision": "2024-01-15",
    "periodo_fiscal": "01/2024",
    "detalles": [
        {
            "codigo_sustento": "01",
            "cod_doc_sustento": "01",
            "num_doc_sustento": "001-001-000000050",
            "fecha_emision_doc_sustento": "2024-01-10",
            "num_aut_doc_sustento": "",
            "base_0_doc": 0,
            "base_iva_doc": 500.00,
            "total_doc": 560.00,
            "codigo_retencion": "303",
            "tipo_retencion": "renta",
            "base_imponible": 500.00,
            "porcentaje_retener": 1.75,
            "valor_retenido": 8.75
        }
    ]
})
print(resp.json())
```

---

### Ejemplo: Listar y filtrar facturas autorizadas

```python
resp = requests.get(f"{BASE}/api/facturas/{empresa_id}", params={
    "estado": "AUTORIZADO",
    "q": "Empresa ABC"
})
facturas = resp.json()['data']
for f in facturas:
    print(f"{f['numero_formateado']} | {f['cliente_nombre']} | ${f['total']} | {f['fecha_emision']}")
```

---

### Ejemplo: Importar compra de proveedor

```python
resp = requests.post(f"{BASE}/api/compras/", json={
    "empresa_id": 1,
    "proveedor_id": 2,
    "tipo_documento": "01",
    "numero_documento": "001-001-000000100",
    "numero_autorizacion": "1001202401...",
    "fecha_emision": "2024-01-10",
    "ruc_proveedor": "1790123456001",
    "razon_social_proveedor": "Proveedor XYZ S.A.",
    "subtotal_sin_iva": 500.00,
    "subtotal_iva_0": 0,
    "subtotal_iva_12": 500.00,
    "iva": 60.00,
    "total": 560.00
})
print(resp.json())
```

---

*Documentación de API — Facturador Electrónico v1.0.0 · SRI Ecuador*
