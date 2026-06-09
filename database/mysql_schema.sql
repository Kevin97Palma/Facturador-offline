-- ============================================================
--  ESQUEMA MySQL CLOUD — Facturador Electrónico SRI Ecuador
--  Versión 1.0.0
-- ============================================================
--
--  PROPÓSITO:
--    1. bk_*  — Tablas de respaldo (espejo de las SQLite locales)
--    2. licencias / equipos_registrados — Control de licencias
--    3. bk_sync_log — Historial de sincronizaciones
--
--  CÓMO INSTALAR:
--    mysql -u root -p < mysql_schema.sql
--    O ejecutarlo desde phpMyAdmin / MySQL Workbench
-- ============================================================

CREATE DATABASE IF NOT EXISTS facturador_cloud
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE facturador_cloud;

-- ────────────────────────────────────────────────────────────
--  LICENCIAS
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS licencias (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    ruc                 VARCHAR(13)   NOT NULL UNIQUE COMMENT 'RUC de la empresa cliente',
    razon_social        VARCHAR(300)  NOT NULL,
    email_contacto      VARCHAR(200),
    telefono_contacto   VARCHAR(20),
    plan                ENUM('basico','profesional','enterprise') NOT NULL DEFAULT 'basico'
                        COMMENT 'basico=1 PC, profesional=5 PCs, enterprise=ilimitado',
    activo              TINYINT(1)    NOT NULL DEFAULT 1,
    fecha_inicio        DATE          NOT NULL DEFAULT (CURDATE()),
    fecha_vencimiento   DATE          NOT NULL,
    max_equipos         INT           NOT NULL DEFAULT 1
                        COMMENT 'Número máximo de equipos permitidos',
    observaciones       TEXT,
    created_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_ruc (ruc),
    INDEX idx_activo (activo),
    INDEX idx_vencimiento (fecha_vencimiento)
) ENGINE=InnoDB COMMENT='Licencias por empresa (RUC)';

-- Datos de ejemplo
-- INSERT INTO licencias (ruc, razon_social, plan, fecha_vencimiento, max_equipos)
-- VALUES ('1234567890001', 'Mi Empresa S.A.', 'profesional', '2025-12-31', 5);


-- ────────────────────────────────────────────────────────────
--  EQUIPOS REGISTRADOS (por empresa)
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS equipos_registrados (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    ruc             VARCHAR(13)  NOT NULL COMMENT 'RUC de la empresa',
    nombre_pc       VARCHAR(200) NOT NULL COMMENT 'Hostname del equipo (socket.gethostname)',
    primer_acceso   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_ruc_pc (ruc, nombre_pc),
    INDEX idx_ruc_acceso (ruc, ultimo_acceso),
    FOREIGN KEY (ruc) REFERENCES licencias(ruc)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='PCs activas por empresa';


-- ────────────────────────────────────────────────────────────
--  LOG DE SINCRONIZACIONES
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bk_sync_log (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    source_pc           VARCHAR(200) NOT NULL COMMENT 'PC origen del backup',
    backup_at           DATETIME     NOT NULL,
    total_registros     INT          DEFAULT 0,
    resultado           ENUM('OK','ERROR') NOT NULL DEFAULT 'OK',
    detalle_error       TEXT,
    INDEX idx_pc_fecha (source_pc, backup_at)
) ENGINE=InnoDB COMMENT='Historial de backups';


-- ────────────────────────────────────────────────────────────
--  TABLAS DE RESPALDO (bk_*)
--  Espejo de las tablas SQLite + campos source_pc y backup_at
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bk_empresa (
    id                              INT           NOT NULL,
    ruc                             VARCHAR(13)   NOT NULL,
    razon_social                    VARCHAR(300)  NOT NULL,
    nombre_comercial                VARCHAR(300),
    direccion                       VARCHAR(500),
    telefono                        VARCHAR(20),
    email                           VARCHAR(200),
    establecimiento                 VARCHAR(3),
    punto_emision                   VARCHAR(3),
    ambiente                        INT           DEFAULT 1,
    obligado_contabilidad           TINYINT(1)    DEFAULT 0,
    agente_retencion                TINYINT(1)    DEFAULT 0,
    contribuyente_especial          TINYINT(1)    DEFAULT 0,
    contribuyente_rimpe             TINYINT(1)    DEFAULT 0,
    activo                          TINYINT(1)    DEFAULT 1,
    created_at                      DATETIME,
    source_pc                       VARCHAR(200)  NOT NULL,
    backup_at                       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB COMMENT='Respaldo de empresas';


CREATE TABLE IF NOT EXISTS bk_usuario (
    id              INT           NOT NULL,
    empresa_id      INT           NOT NULL,
    nombre          VARCHAR(100)  NOT NULL,
    apellido        VARCHAR(100)  NOT NULL,
    email           VARCHAR(200)  NOT NULL,
    rol             VARCHAR(20),
    activo          TINYINT(1)    DEFAULT 1,
    created_at      DATETIME,
    source_pc       VARCHAR(200)  NOT NULL,
    backup_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_cliente (
    id                      INT           NOT NULL,
    empresa_id              INT           NOT NULL,
    tipo_identificacion     VARCHAR(5),
    identificacion          VARCHAR(20),
    razon_social            VARCHAR(300),
    email                   VARCHAR(200),
    telefono                VARCHAR(20),
    direccion               VARCHAR(500),
    activo                  TINYINT(1)    DEFAULT 1,
    source_pc               VARCHAR(200)  NOT NULL,
    backup_at               DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_proveedor (
    id                      INT           NOT NULL,
    empresa_id              INT           NOT NULL,
    tipo_identificacion     VARCHAR(5),
    identificacion          VARCHAR(20),
    razon_social            VARCHAR(300),
    email                   VARCHAR(200),
    telefono                VARCHAR(20),
    direccion               VARCHAR(500),
    activo                  TINYINT(1)    DEFAULT 1,
    source_pc               VARCHAR(200)  NOT NULL,
    backup_at               DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_categoria (
    id              INT           NOT NULL,
    empresa_id      INT           NOT NULL,
    nombre          VARCHAR(200),
    descripcion     VARCHAR(500),
    activo          TINYINT(1)    DEFAULT 1,
    source_pc       VARCHAR(200)  NOT NULL,
    backup_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_impuesto (
    id                      INT           NOT NULL,
    empresa_id              INT           NOT NULL,
    nombre                  VARCHAR(100),
    codigo                  VARCHAR(5),
    codigo_porcentaje       VARCHAR(5),
    porcentaje              DECIMAL(5,2),
    activo                  TINYINT(1)    DEFAULT 1,
    source_pc               VARCHAR(200)  NOT NULL,
    backup_at               DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_producto (
    id                  INT             NOT NULL,
    empresa_id          INT             NOT NULL,
    categoria_id        INT,
    impuesto_id         INT,
    codigo              VARCHAR(50),
    nombre              VARCHAR(300),
    descripcion         VARCHAR(500),
    precio_unitario     DECIMAL(12,4)   DEFAULT 0,
    activo              TINYINT(1)      DEFAULT 1,
    source_pc           VARCHAR(200)    NOT NULL,
    backup_at           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_factura (
    id                          INT           NOT NULL,
    empresa_id                  INT           NOT NULL,
    usuario_id                  INT,
    cliente_id                  INT,
    numero                      INT,
    clave_acceso                VARCHAR(49),
    fecha_emision               DATE,
    subtotal_sin_impuesto       DECIMAL(12,2) DEFAULT 0,
    subtotal_iva_0              DECIMAL(12,2) DEFAULT 0,
    subtotal_iva_5              DECIMAL(12,2) DEFAULT 0,
    subtotal_iva_12             DECIMAL(12,2) DEFAULT 0,
    subtotal_iva_15             DECIMAL(12,2) DEFAULT 0,
    iva_5                       DECIMAL(12,2) DEFAULT 0,
    iva_12                      DECIMAL(12,2) DEFAULT 0,
    iva_15                      DECIMAL(12,2) DEFAULT 0,
    descuento_total             DECIMAL(12,2) DEFAULT 0,
    total                       DECIMAL(12,2) DEFAULT 0,
    forma_pago                  VARCHAR(5),
    observacion                 TEXT,
    estado                      VARCHAR(20),
    numero_autorizacion         VARCHAR(49),
    fecha_autorizacion          DATETIME,
    created_at                  DATETIME,
    source_pc                   VARCHAR(200)  NOT NULL,
    backup_at                   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc),
    INDEX idx_empresa_fecha (empresa_id, fecha_emision),
    INDEX idx_estado (estado)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_detalle_factura (
    id                              INT           NOT NULL,
    factura_id                      INT           NOT NULL,
    producto_id                     INT,
    codigo_principal                VARCHAR(50),
    descripcion                     VARCHAR(300),
    cantidad                        DECIMAL(12,4),
    precio_unitario                 DECIMAL(12,4),
    descuento                       DECIMAL(12,2) DEFAULT 0,
    precio_total_sin_impuesto       DECIMAL(12,2),
    impuesto_codigo                 VARCHAR(5),
    impuesto_codigo_porcentaje      VARCHAR(5),
    impuesto_tarifa                 DECIMAL(5,2),
    impuesto_valor                  DECIMAL(12,2),
    source_pc                       VARCHAR(200)  NOT NULL,
    backup_at                       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_retencion (
    id                      INT           NOT NULL,
    empresa_id              INT           NOT NULL,
    usuario_id              INT,
    proveedor_id            INT,
    numero                  INT,
    clave_acceso            VARCHAR(49),
    fecha_emision           DATE,
    periodo_fiscal          VARCHAR(7),
    estado                  VARCHAR(20),
    numero_autorizacion     VARCHAR(49),
    fecha_autorizacion      DATETIME,
    created_at              DATETIME,
    source_pc               VARCHAR(200)  NOT NULL,
    backup_at               DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_nota_credito (
    id                          INT           NOT NULL,
    empresa_id                  INT           NOT NULL,
    usuario_id                  INT,
    cliente_id                  INT,
    numero                      INT,
    clave_acceso                VARCHAR(49),
    fecha_emision               DATE,
    tipo_doc_modificado         VARCHAR(5),
    num_doc_modificado          VARCHAR(20),
    fecha_doc_sustento          DATE,
    motivo                      VARCHAR(300),
    total                       DECIMAL(12,2) DEFAULT 0,
    estado                      VARCHAR(20),
    numero_autorizacion         VARCHAR(49),
    created_at                  DATETIME,
    source_pc                   VARCHAR(200)  NOT NULL,
    backup_at                   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_nota_debito (
    id                          INT           NOT NULL,
    empresa_id                  INT           NOT NULL,
    usuario_id                  INT,
    cliente_id                  INT,
    numero                      INT,
    clave_acceso                VARCHAR(49),
    fecha_emision               DATE,
    num_doc_modificado          VARCHAR(20),
    total                       DECIMAL(12,2) DEFAULT 0,
    estado                      VARCHAR(20),
    numero_autorizacion         VARCHAR(49),
    created_at                  DATETIME,
    source_pc                   VARCHAR(200)  NOT NULL,
    backup_at                   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_guia_remision (
    id                              INT           NOT NULL,
    empresa_id                      INT           NOT NULL,
    numero                          INT,
    clave_acceso                    VARCHAR(49),
    fecha_emision                   DATE,
    dir_partida                     VARCHAR(300),
    ruc_transportista               VARCHAR(13),
    razon_social_transportista      VARCHAR(300),
    placa                           VARCHAR(20),
    fecha_ini_transporte            DATE,
    fecha_fin_transporte            DATE,
    estado                          VARCHAR(20),
    numero_autorizacion             VARCHAR(49),
    created_at                      DATETIME,
    source_pc                       VARCHAR(200)  NOT NULL,
    backup_at                       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_liquidacion_compra (
    id                          INT           NOT NULL,
    empresa_id                  INT           NOT NULL,
    usuario_id                  INT,
    proveedor_id                INT,
    numero                      INT,
    clave_acceso                VARCHAR(49),
    fecha_emision               DATE,
    subtotal_sin_impuesto       DECIMAL(12,2) DEFAULT 0,
    total                       DECIMAL(12,2) DEFAULT 0,
    estado                      VARCHAR(20),
    numero_autorizacion         VARCHAR(49),
    created_at                  DATETIME,
    source_pc                   VARCHAR(200)  NOT NULL,
    backup_at                   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS bk_compra_proveedor (
    id                          INT           NOT NULL,
    empresa_id                  INT           NOT NULL,
    proveedor_id                INT,
    tipo_documento              VARCHAR(5),
    numero_documento            VARCHAR(20),
    numero_autorizacion         VARCHAR(49),
    fecha_emision               DATE,
    ruc_proveedor               VARCHAR(13),
    razon_social_proveedor      VARCHAR(300),
    subtotal_sin_iva            DECIMAL(12,2) DEFAULT 0,
    subtotal_iva_0              DECIMAL(12,2) DEFAULT 0,
    subtotal_iva_12             DECIMAL(12,2) DEFAULT 0,
    iva                         DECIMAL(12,2) DEFAULT 0,
    total                       DECIMAL(12,2) DEFAULT 0,
    observacion                 TEXT,
    created_at                  DATETIME,
    source_pc                   VARCHAR(200)  NOT NULL,
    backup_at                   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, source_pc)
) ENGINE=InnoDB;


-- ────────────────────────────────────────────────────────────
--  USUARIO DE ACCESO RESTRINGIDO PARA EL SISTEMA
--  (Solo los permisos mínimos necesarios)
-- ────────────────────────────────────────────────────────────

-- Crear usuario con acceso solo a facturador_cloud
-- REEMPLAZAR 'CONTRASEÑA_SEGURA' con una contraseña real
-- CREATE USER 'facturador_app'@'%' IDENTIFIED BY 'CONTRASEÑA_SEGURA';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.licencias TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.equipos_registrados TO 'facturador_app'@'%';
-- GRANT INSERT ON facturador_cloud.bk_sync_log TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_empresa TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_usuario TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_cliente TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_proveedor TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_factura TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_detalle_factura TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_retencion TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_nota_credito TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_nota_debito TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_guia_remision TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_liquidacion_compra TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_compra_proveedor TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_categoria TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_impuesto TO 'facturador_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON facturador_cloud.bk_producto TO 'facturador_app'@'%';
-- FLUSH PRIVILEGES;

-- ============================================================
--  FIN DEL ESQUEMA
-- ============================================================
