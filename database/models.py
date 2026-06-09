from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db import db


class Empresa(db.Model):
    __tablename__ = 'empresa'
    id = db.Column(db.Integer, primary_key=True)
    ruc = db.Column(db.String(13), nullable=False, unique=True)
    razon_social = db.Column(db.String(300), nullable=False)
    nombre_comercial = db.Column(db.String(300))
    direccion = db.Column(db.String(500), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(200))
    establecimiento = db.Column(db.String(3), nullable=False, default='001')
    punto_emision = db.Column(db.String(3), nullable=False, default='001')
    ambiente = db.Column(db.Integer, nullable=False, default=1)  # 1=pruebas, 2=produccion
    obligado_contabilidad = db.Column(db.Boolean, default=False)
    agente_retencion = db.Column(db.Boolean, default=False)
    contribuyente_especial = db.Column(db.Boolean, default=False)
    num_resolucion_contrib_especial = db.Column(db.String(50))
    contribuyente_rimpe = db.Column(db.Boolean, default=False)
    texto_regimen = db.Column(db.String(100))
    nombre_archivo_firma = db.Column(db.String(255))
    clave_firma = db.Column(db.String(255))
    firma_caduca = db.Column(db.String(20))
    logo_path = db.Column(db.String(500))
    fe_url = db.Column(db.String(500))
    pdf_url = db.Column(db.String(500))
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    usuarios = db.relationship('Usuario', backref='empresa', lazy=True)
    clientes = db.relationship('Cliente', backref='empresa', lazy=True)
    proveedores = db.relationship('Proveedor', backref='empresa', lazy=True)
    categorias = db.relationship('Categoria', backref='empresa', lazy=True)
    productos = db.relationship('Producto', backref='empresa', lazy=True)
    impuestos = db.relationship('Impuesto', backref='empresa', lazy=True)
    facturas = db.relationship('Factura', backref='empresa', lazy=True)
    retenciones = db.relationship('Retencion', backref='empresa', lazy=True)
    notas_credito = db.relationship('NotaCredito', backref='empresa', lazy=True)
    notas_debito = db.relationship('NotaDebito', backref='empresa', lazy=True)
    guias_remision = db.relationship('GuiaRemision', backref='empresa', lazy=True)
    liquidaciones = db.relationship('LiquidacionCompra', backref='empresa', lazy=True)
    compras = db.relationship('CompraProveedor', backref='empresa', lazy=True)

    def get_serie(self):
        return f"{self.establecimiento}-{self.punto_emision}"

    def get_ambiente_nombre(self):
        return 'PRUEBAS' if self.ambiente == 1 else 'PRODUCCIÓN'


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='vendedor')  # superadmin, admin, vendedor
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def es_admin(self):
        return self.rol in ('admin', 'superadmin')

    def es_superadmin(self):
        return self.rol == 'superadmin'


class Categoria(db.Model):
    __tablename__ = 'categoria'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.String(500))
    activo = db.Column(db.Boolean, default=True)

    productos = db.relationship('Producto', backref='categoria', lazy=True)


class Impuesto(db.Model):
    __tablename__ = 'impuesto'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(5), nullable=False, default='2')  # 2=IVA
    codigo_porcentaje = db.Column(db.String(5), nullable=False)    # 0=0%, 2=12%, 5=5%
    porcentaje = db.Column(db.Numeric(5, 2), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    productos = db.relationship('Producto', backref='impuesto', lazy=True)


class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'))
    impuesto_id = db.Column(db.Integer, db.ForeignKey('impuesto.id'))
    codigo = db.Column(db.String(50), nullable=False)
    nombre = db.Column(db.String(300), nullable=False)
    descripcion = db.Column(db.String(500))
    precio_unitario = db.Column(db.Numeric(12, 4), nullable=False, default=0)
    activo = db.Column(db.Boolean, default=True)


class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    tipo_identificacion = db.Column(db.String(5), nullable=False, default='05')
    identificacion = db.Column(db.String(20), nullable=False)
    razon_social = db.Column(db.String(300), nullable=False)
    email = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(500))
    activo = db.Column(db.Boolean, default=True)

    facturas = db.relationship('Factura', backref='cliente', lazy=True)
    notas_credito = db.relationship('NotaCredito', backref='cliente', lazy=True)
    notas_debito = db.relationship('NotaDebito', backref='cliente', lazy=True)

    TIPOS_IDENTIFICACION = {
        '04': 'RUC',
        '05': 'Cédula',
        '06': 'Pasaporte',
        '07': 'Consumidor Final',
        '08': 'Identificación Exterior',
    }

    def get_tipo_nombre(self):
        return self.TIPOS_IDENTIFICACION.get(self.tipo_identificacion, self.tipo_identificacion)


class Proveedor(db.Model):
    __tablename__ = 'proveedor'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    tipo_identificacion = db.Column(db.String(5), nullable=False, default='04')
    identificacion = db.Column(db.String(20), nullable=False)
    razon_social = db.Column(db.String(300), nullable=False)
    email = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(500))
    activo = db.Column(db.Boolean, default=True)

    retenciones = db.relationship('Retencion', backref='proveedor', lazy=True)
    liquidaciones = db.relationship('LiquidacionCompra', backref='proveedor', lazy=True)
    compras = db.relationship('CompraProveedor', backref='proveedor', lazy=True)

    TIPOS_IDENTIFICACION = {
        '04': 'RUC',
        '05': 'Cédula',
        '06': 'Pasaporte',
        '08': 'Identificación Exterior',
    }

    def get_tipo_nombre(self):
        return self.TIPOS_IDENTIFICACION.get(self.tipo_identificacion, self.tipo_identificacion)


# ─── Facturas de Venta ────────────────────────────────────────────────────────

class Factura(db.Model):
    __tablename__ = 'factura'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    clave_acceso = db.Column(db.String(49))
    fecha_emision = db.Column(db.Date, nullable=False)
    subtotal_sin_impuesto = db.Column(db.Numeric(12, 2), default=0)
    subtotal_iva_0 = db.Column(db.Numeric(12, 2), default=0)
    subtotal_iva_5 = db.Column(db.Numeric(12, 2), default=0)
    subtotal_iva_12 = db.Column(db.Numeric(12, 2), default=0)
    subtotal_iva_15 = db.Column(db.Numeric(12, 2), default=0)
    subtotal_no_objeto = db.Column(db.Numeric(12, 2), default=0)
    subtotal_exento = db.Column(db.Numeric(12, 2), default=0)
    iva_5 = db.Column(db.Numeric(12, 2), default=0)
    iva_12 = db.Column(db.Numeric(12, 2), default=0)
    iva_15 = db.Column(db.Numeric(12, 2), default=0)
    descuento_total = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), default=0)
    forma_pago = db.Column(db.String(5), default='01')
    observacion = db.Column(db.Text)
    estado = db.Column(db.String(20), default='PENDIENTE')
    numero_autorizacion = db.Column(db.String(49))
    fecha_autorizacion = db.Column(db.DateTime)
    xml_path = db.Column(db.String(500))
    xml_autorizado_path = db.Column(db.String(500))
    pdf_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    detalles = db.relationship('DetalleFactura', backref='factura', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])

    def get_numero_formateado(self):
        emp = self.empresa
        return f"{emp.establecimiento}-{emp.punto_emision}-{str(self.numero).zfill(9)}"


class DetalleFactura(db.Model):
    __tablename__ = 'detalle_factura'
    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey('factura.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    codigo_principal = db.Column(db.String(50))
    descripcion = db.Column(db.String(300), nullable=False)
    cantidad = db.Column(db.Numeric(12, 4), nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 4), nullable=False)
    descuento = db.Column(db.Numeric(12, 2), default=0)
    precio_total_sin_impuesto = db.Column(db.Numeric(12, 2), nullable=False)
    impuesto_codigo = db.Column(db.String(5), default='2')
    impuesto_codigo_porcentaje = db.Column(db.String(5))
    impuesto_tarifa = db.Column(db.Numeric(5, 2), default=0)
    impuesto_valor = db.Column(db.Numeric(12, 2), default=0)

    producto = db.relationship('Producto', foreign_keys=[producto_id])


# ─── Retenciones ─────────────────────────────────────────────────────────────

class Retencion(db.Model):
    __tablename__ = 'retencion'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    clave_acceso = db.Column(db.String(49))
    fecha_emision = db.Column(db.Date, nullable=False)
    periodo_fiscal = db.Column(db.String(7))  # MM/YYYY
    estado = db.Column(db.String(20), default='PENDIENTE')
    numero_autorizacion = db.Column(db.String(49))
    fecha_autorizacion = db.Column(db.DateTime)
    xml_path = db.Column(db.String(500))
    xml_autorizado_path = db.Column(db.String(500))
    pdf_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    detalles = db.relationship('DetalleRetencion', backref='retencion', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])

    def get_numero_formateado(self):
        emp = self.empresa
        return f"{emp.establecimiento}-{emp.punto_emision}-{str(self.numero).zfill(9)}"


class DetalleRetencion(db.Model):
    __tablename__ = 'detalle_retencion'
    id = db.Column(db.Integer, primary_key=True)
    retencion_id = db.Column(db.Integer, db.ForeignKey('retencion.id'), nullable=False)
    codigo_sustento = db.Column(db.String(5), nullable=False)
    cod_doc_sustento = db.Column(db.String(5), nullable=False)
    num_doc_sustento = db.Column(db.String(20), nullable=False)
    fecha_emision_doc_sustento = db.Column(db.Date, nullable=False)
    num_aut_doc_sustento = db.Column(db.String(49))
    base_0_doc = db.Column(db.Numeric(12, 2), default=0)
    base_iva_doc = db.Column(db.Numeric(12, 2), default=0)
    total_doc = db.Column(db.Numeric(12, 2), default=0)
    codigo_retencion = db.Column(db.String(10), nullable=False)
    tipo_retencion = db.Column(db.String(10), nullable=False)  # renta, iva
    base_imponible = db.Column(db.Numeric(12, 2), nullable=False)
    porcentaje_retener = db.Column(db.Numeric(5, 2), nullable=False)
    valor_retenido = db.Column(db.Numeric(12, 2), nullable=False)


# ─── Notas de Crédito ────────────────────────────────────────────────────────

class NotaCredito(db.Model):
    __tablename__ = 'nota_credito'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    clave_acceso = db.Column(db.String(49))
    fecha_emision = db.Column(db.Date, nullable=False)
    tipo_doc_modificado = db.Column(db.String(5), default='01')
    num_doc_modificado = db.Column(db.String(20), nullable=False)
    fecha_doc_sustento = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(300), nullable=False)
    subtotal_sin_impuesto = db.Column(db.Numeric(12, 2), default=0)
    subtotal_iva_0 = db.Column(db.Numeric(12, 2), default=0)
    subtotal_iva_12 = db.Column(db.Numeric(12, 2), default=0)
    iva_12 = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), default=0)
    estado = db.Column(db.String(20), default='PENDIENTE')
    numero_autorizacion = db.Column(db.String(49))
    fecha_autorizacion = db.Column(db.DateTime)
    xml_path = db.Column(db.String(500))
    xml_autorizado_path = db.Column(db.String(500))
    pdf_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    detalles = db.relationship('DetalleNotaCredito', backref='nota_credito', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])

    def get_numero_formateado(self):
        emp = self.empresa
        return f"{emp.establecimiento}-{emp.punto_emision}-{str(self.numero).zfill(9)}"


class DetalleNotaCredito(db.Model):
    __tablename__ = 'detalle_nota_credito'
    id = db.Column(db.Integer, primary_key=True)
    nota_credito_id = db.Column(db.Integer, db.ForeignKey('nota_credito.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    codigo_principal = db.Column(db.String(50))
    descripcion = db.Column(db.String(300), nullable=False)
    cantidad = db.Column(db.Numeric(12, 4), nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 4), nullable=False)
    descuento = db.Column(db.Numeric(12, 2), default=0)
    precio_total_sin_impuesto = db.Column(db.Numeric(12, 2), nullable=False)
    impuesto_codigo = db.Column(db.String(5), default='2')
    impuesto_codigo_porcentaje = db.Column(db.String(5))
    impuesto_tarifa = db.Column(db.Numeric(5, 2), default=0)
    impuesto_valor = db.Column(db.Numeric(12, 2), default=0)

    producto = db.relationship('Producto', foreign_keys=[producto_id])


# ─── Notas de Débito ─────────────────────────────────────────────────────────

class NotaDebito(db.Model):
    __tablename__ = 'nota_debito'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    clave_acceso = db.Column(db.String(49))
    fecha_emision = db.Column(db.Date, nullable=False)
    tipo_doc_modificado = db.Column(db.String(5), default='01')
    num_doc_modificado = db.Column(db.String(20), nullable=False)
    fecha_doc_sustento = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(300))
    subtotal_sin_impuesto = db.Column(db.Numeric(12, 2), default=0)
    subtotal_iva_0 = db.Column(db.Numeric(12, 2), default=0)
    subtotal_iva_12 = db.Column(db.Numeric(12, 2), default=0)
    iva_12 = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), default=0)
    estado = db.Column(db.String(20), default='PENDIENTE')
    numero_autorizacion = db.Column(db.String(49))
    fecha_autorizacion = db.Column(db.DateTime)
    xml_path = db.Column(db.String(500))
    xml_autorizado_path = db.Column(db.String(500))
    pdf_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    detalles = db.relationship('DetalleNotaDebito', backref='nota_debito', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])

    def get_numero_formateado(self):
        emp = self.empresa
        return f"{emp.establecimiento}-{emp.punto_emision}-{str(self.numero).zfill(9)}"


class DetalleNotaDebito(db.Model):
    __tablename__ = 'detalle_nota_debito'
    id = db.Column(db.Integer, primary_key=True)
    nota_debito_id = db.Column(db.Integer, db.ForeignKey('nota_debito.id'), nullable=False)
    razon = db.Column(db.String(300), nullable=False)
    valor = db.Column(db.Numeric(12, 2), nullable=False)


# ─── Guías de Remisión ───────────────────────────────────────────────────────

class GuiaRemision(db.Model):
    __tablename__ = 'guia_remision'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    clave_acceso = db.Column(db.String(49))
    fecha_emision = db.Column(db.Date, nullable=False)
    dir_partida = db.Column(db.String(300), nullable=False)
    ruc_transportista = db.Column(db.String(13), nullable=False)
    razon_social_transportista = db.Column(db.String(300), nullable=False)
    tipo_identificacion_transportista = db.Column(db.String(5), default='04')
    fecha_ini_transporte = db.Column(db.Date, nullable=False)
    fecha_fin_transporte = db.Column(db.Date, nullable=False)
    placa = db.Column(db.String(20), nullable=False)
    estado = db.Column(db.String(20), default='PENDIENTE')
    numero_autorizacion = db.Column(db.String(49))
    fecha_autorizacion = db.Column(db.DateTime)
    xml_path = db.Column(db.String(500))
    xml_autorizado_path = db.Column(db.String(500))
    pdf_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    destinatarios = db.relationship('DestinatarioGuia', backref='guia', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])

    def get_numero_formateado(self):
        emp = self.empresa
        return f"{emp.establecimiento}-{emp.punto_emision}-{str(self.numero).zfill(9)}"


class DestinatarioGuia(db.Model):
    __tablename__ = 'destinatario_guia'
    id = db.Column(db.Integer, primary_key=True)
    guia_remision_id = db.Column(db.Integer, db.ForeignKey('guia_remision.id'), nullable=False)
    tipo_identificacion = db.Column(db.String(5), default='04')
    identificacion = db.Column(db.String(20), nullable=False)
    razon_social = db.Column(db.String(300), nullable=False)
    direccion_destino = db.Column(db.String(300), nullable=False)
    motivo_traslado = db.Column(db.String(300), nullable=False)
    num_doc_sustento = db.Column(db.String(20))
    num_aut_doc_sustento = db.Column(db.String(49))
    fecha_emision_doc_sustento = db.Column(db.Date)
    cod_doc_sustento = db.Column(db.String(5), default='01')

    detalles = db.relationship('DetalleGuia', backref='destinatario', lazy=True, cascade='all, delete-orphan')


class DetalleGuia(db.Model):
    __tablename__ = 'detalle_guia'
    id = db.Column(db.Integer, primary_key=True)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('destinatario_guia.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    codigo_interno = db.Column(db.String(50))
    descripcion = db.Column(db.String(300), nullable=False)
    cantidad = db.Column(db.Numeric(12, 4), nullable=False)

    producto = db.relationship('Producto', foreign_keys=[producto_id])


# ─── Liquidaciones de Compra ─────────────────────────────────────────────────

class LiquidacionCompra(db.Model):
    __tablename__ = 'liquidacion_compra'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    clave_acceso = db.Column(db.String(49))
    fecha_emision = db.Column(db.Date, nullable=False)
    subtotal_sin_impuesto = db.Column(db.Numeric(12, 2), default=0)
    subtotal_iva_0 = db.Column(db.Numeric(12, 2), default=0)
    subtotal_iva_12 = db.Column(db.Numeric(12, 2), default=0)
    iva_12 = db.Column(db.Numeric(12, 2), default=0)
    descuento_total = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), default=0)
    forma_pago = db.Column(db.String(5), default='01')
    observacion = db.Column(db.Text)
    estado = db.Column(db.String(20), default='PENDIENTE')
    numero_autorizacion = db.Column(db.String(49))
    fecha_autorizacion = db.Column(db.DateTime)
    xml_path = db.Column(db.String(500))
    xml_autorizado_path = db.Column(db.String(500))
    pdf_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    detalles = db.relationship('DetalleLiquidacion', backref='liquidacion', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])

    def get_numero_formateado(self):
        emp = self.empresa
        return f"{emp.establecimiento}-{emp.punto_emision}-{str(self.numero).zfill(9)}"


class DetalleLiquidacion(db.Model):
    __tablename__ = 'detalle_liquidacion'
    id = db.Column(db.Integer, primary_key=True)
    liquidacion_id = db.Column(db.Integer, db.ForeignKey('liquidacion_compra.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    codigo_principal = db.Column(db.String(50))
    descripcion = db.Column(db.String(300), nullable=False)
    cantidad = db.Column(db.Numeric(12, 4), nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 4), nullable=False)
    descuento = db.Column(db.Numeric(12, 2), default=0)
    precio_total_sin_impuesto = db.Column(db.Numeric(12, 2), nullable=False)
    impuesto_codigo = db.Column(db.String(5), default='2')
    impuesto_codigo_porcentaje = db.Column(db.String(5))
    impuesto_tarifa = db.Column(db.Numeric(5, 2), default=0)
    impuesto_valor = db.Column(db.Numeric(12, 2), default=0)

    producto = db.relationship('Producto', foreign_keys=[producto_id])


# ─── Compras de Proveedores (importadas) ─────────────────────────────────────

class CompraProveedor(db.Model):
    __tablename__ = 'compra_proveedor'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'))
    tipo_documento = db.Column(db.String(5), default='01')  # 01=factura, 03=liquidacion, etc
    numero_documento = db.Column(db.String(20), nullable=False)
    numero_autorizacion = db.Column(db.String(49))
    fecha_emision = db.Column(db.Date, nullable=False)
    ruc_proveedor = db.Column(db.String(13))
    razon_social_proveedor = db.Column(db.String(300))
    subtotal_sin_iva = db.Column(db.Numeric(12, 2), default=0)
    subtotal_iva_0 = db.Column(db.Numeric(12, 2), default=0)
    subtotal_iva_12 = db.Column(db.Numeric(12, 2), default=0)
    iva = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), default=0)
    xml_content = db.Column(db.Text)
    observacion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    TIPOS_DOCUMENTO = {
        '01': 'Factura',
        '03': 'Liquidación de Compra',
        '04': 'Nota de Crédito',
        '05': 'Nota de Débito',
    }

    def get_tipo_nombre(self):
        return self.TIPOS_DOCUMENTO.get(self.tipo_documento, self.tipo_documento)
