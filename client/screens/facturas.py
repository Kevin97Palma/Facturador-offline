from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QDialog, QFormLayout, QComboBox, QDialogButtonBox,
    QDoubleSpinBox, QDateEdit, QLineEdit, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QFileDialog, QFrame,
    QSplitter, QGroupBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from ..widgets import (BaseScreen, make_btn, make_table, table_item,
                       set_estado_item, show_error, show_info, confirm,
                       SearchBar, Divider, LoadWorker, APP_STYLE, toast)
from ..theme import C
from .. import api
from ..printer import imprimir_ticket_factura

FORMAS_PAGO = [
    ('01', 'Sin utilización del sistema financiero'),
    ('16', 'Tarjeta de débito'),
    ('19', 'Tarjeta de crédito'),
    ('17', 'Dinero electrónico'),
    ('20', 'Otros con utilización del sistema financiero'),
]


class NuevaFacturaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Nueva Factura')
        self.setMinimumSize(960, 680)
        self.setStyleSheet(APP_STYLE)
        self._clientes = []
        self._productos = []
        self._impuestos = []
        self._detalles = []
        self._build()
        self._load_data()

    def _build(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(20, 18, 20, 18)
        main.setSpacing(14)

        # ── Header fields ────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(20)

        # Left: cliente + fecha
        left_grp = QGroupBox('Datos del comprobante')
        left_form = QFormLayout(left_grp)
        left_form.setSpacing(10)

        self.cmb_cliente = QComboBox()
        self.cmb_cliente.setEditable(True)
        self.cmb_cliente.setMinimumWidth(300)
        self.txt_fecha = QDateEdit(QDate.currentDate())
        self.txt_fecha.setCalendarPopup(True)
        self.txt_fecha.setDisplayFormat('yyyy-MM-dd')

        left_form.addRow('Cliente *:', self.cmb_cliente)
        left_form.addRow('Fecha Emisión *:', self.txt_fecha)

        # Right: forma pago + obs
        right_grp = QGroupBox('Opciones')
        right_form = QFormLayout(right_grp)
        right_form.setSpacing(10)

        self.cmb_forma_pago = QComboBox()
        for code, label in FORMAS_PAGO:
            self.cmb_forma_pago.addItem(label, code)
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText('Observación (opcional)')

        right_form.addRow('Forma de Pago:', self.cmb_forma_pago)
        right_form.addRow('Observación:', self.txt_obs)

        top.addWidget(left_grp, 3)
        top.addWidget(right_grp, 2)
        main.addLayout(top)

        # ── Item entry ───────────────────────────────────────
        item_grp = QGroupBox('Agregar ítem')
        item_lay = QHBoxLayout(item_grp)
        item_lay.setSpacing(10)

        self.txt_scanner = QLineEdit()
        self.txt_scanner.setPlaceholderText('🔍 Código barras...')
        self.txt_scanner.setFixedWidth(150)
        self.txt_scanner.returnPressed.connect(self._scanner_lookup)

        self.cmb_producto = QComboBox()
        self.cmb_producto.setEditable(True)
        self.cmb_producto.setMinimumWidth(240)
        self.cmb_producto.currentIndexChanged.connect(self._on_product_select)

        self.spn_cantidad = QDoubleSpinBox()
        self.spn_cantidad.setRange(0.01, 99999)
        self.spn_cantidad.setValue(1)
        self.spn_cantidad.setDecimals(2)
        self.spn_cantidad.setFixedWidth(90)

        self.spn_precio = QDoubleSpinBox()
        self.spn_precio.setRange(0, 999999)
        self.spn_precio.setDecimals(4)
        self.spn_precio.setFixedWidth(110)

        self.spn_desc = QDoubleSpinBox()
        self.spn_desc.setRange(0, 99999)
        self.spn_desc.setDecimals(2)
        self.spn_desc.setFixedWidth(90)

        self.cmb_iva = QComboBox()
        self.cmb_iva.setFixedWidth(110)

        btn_add = make_btn('+ Agregar', 'primary')
        btn_add.setFixedHeight(34)
        btn_add.clicked.connect(self._add_item)

        for lbl, w in [('Barras:', self.txt_scanner), ('Producto:', self.cmb_producto),
                        ('Cant.:', self.spn_cantidad), ('Precio:', self.spn_precio),
                        ('Desc.:', self.spn_desc), ('IVA:', self.cmb_iva)]:
            l = QLabel(lbl)
            l.setStyleSheet(f'color:{C["text_muted"]}; font-size:12px; background:transparent;border:none;')
            item_lay.addWidget(l)
            item_lay.addWidget(w)

        item_lay.addWidget(btn_add)
        main.addWidget(item_grp)

        # ── Detail table ─────────────────────────────────────
        self.tbl_dets = make_table(['Código', 'Descripción', 'Cant.', 'P.Unit.', 'Desc.', 'IVA%', 'Subtotal'])
        self.tbl_dets.setFixedHeight(180)
        self.tbl_dets.setColumnWidth(0, 90)
        self.tbl_dets.setColumnWidth(1, 260)
        self.tbl_dets.setColumnWidth(2, 70)
        self.tbl_dets.setColumnWidth(3, 90)
        self.tbl_dets.setColumnWidth(4, 70)
        self.tbl_dets.setColumnWidth(5, 60)
        main.addWidget(self.tbl_dets)

        # Row: remove + totals
        bot = QHBoxLayout()
        btn_del = make_btn('✕  Quitar seleccionado', 'danger')
        btn_del.setFixedHeight(30)
        btn_del.clicked.connect(self._remove_item)
        bot.addWidget(btn_del)
        bot.addStretch()

        for attr, label in [('lbl_sub', 'Subtotal'), ('lbl_iva', 'IVA'), ('lbl_total', 'TOTAL')]:
            lbl = QLabel(f'{label}: $0.00')
            lbl.setStyleSheet(
                f'color:{C["accent_h"] if label == "TOTAL" else C["text_muted"]}; '
                f'font-size:{"16px" if label == "TOTAL" else "13px"}; '
                f'font-weight:{"700" if label == "TOTAL" else "400"}; '
                'background:transparent; border:none;'
            )
            setattr(self, attr, lbl)
            bot.addWidget(lbl)
            if label != 'TOTAL':
                bot.addSpacing(20)

        main.addLayout(bot)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText('💾  Guardar Factura')
        btns.button(QDialogButtonBox.Ok).setObjectName('primary')
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        main.addWidget(btns)

    def _load_data(self):
        eid = api.empresa_id()
        r = api.get(f'/api/clientes/{eid}')
        if r.get('ok'):
            self._clientes = r['data']
            for c in self._clientes:
                self.cmb_cliente.addItem(f'{c["identificacion"]} — {c["razon_social"]}', c['id'])

        r = api.get(f'/api/impuestos/{eid}')
        if r.get('ok'):
            self._impuestos = r['data']
            for i in self._impuestos:
                self.cmb_iva.addItem(i['nombre'], i)

        r = api.get(f'/api/productos/{eid}')
        if r.get('ok'):
            self._productos = r['data']
            self.cmb_producto.addItem('— Seleccionar —', None)
            for p in self._productos:
                self.cmb_producto.addItem(f'{p["codigo"]}  {p["nombre"]}', p)

    def _scanner_lookup(self):
        codigo = self.txt_scanner.text().strip()
        if not codigo:
            return
        r = api.get(f'/api/productos/codigo/{api.empresa_id()}/{codigo}')
        if r.get('ok'):
            prod = r['data']
            idx = next((i for i, p in enumerate(self._productos) if p['id'] == prod['id']), -1)
            if idx >= 0:
                self.cmb_producto.setCurrentIndex(idx + 1)
        else:
            show_error(self, f'Código {codigo} no encontrado')
        self.txt_scanner.clear()

    def _on_product_select(self, idx):
        prod = self.cmb_producto.currentData()
        if not prod:
            return
        self.spn_precio.setValue(float(prod.get('precio_unitario', 0)))
        imp_id = prod.get('impuesto_id')
        if imp_id:
            for i, imp in enumerate(self._impuestos):
                if imp['id'] == imp_id:
                    self.cmb_iva.setCurrentIndex(i)
                    break

    def _add_item(self):
        prod = self.cmb_producto.currentData()
        imp = self.cmb_iva.currentData()
        cant = self.spn_cantidad.value()
        precio = self.spn_precio.value()
        desc = self.spn_desc.value()
        if not imp or precio <= 0:
            show_error(self, 'Seleccione impuesto e ingrese precio')
            return
        subtotal = round(cant * precio - desc, 2)
        iva_val = round(subtotal * float(imp['porcentaje']) / 100, 2)
        item = {
            'producto_id': prod['id'] if prod else None,
            'codigo_principal': prod['codigo'] if prod else '',
            'descripcion': prod['nombre'] if prod else 'Producto',
            'cantidad': cant, 'precio_unitario': precio, 'descuento': desc,
            'precio_total_sin_impuesto': subtotal,
            'impuesto_codigo': imp['codigo'],
            'impuesto_codigo_porcentaje': imp['codigo_porcentaje'],
            'impuesto_tarifa': float(imp['porcentaje']),
            'impuesto_valor': iva_val,
        }
        self._detalles.append(item)
        self._refresh_table()
        self.spn_cantidad.setValue(1)
        self.spn_desc.setValue(0)

    def _remove_item(self):
        row = self.tbl_dets.currentRow()
        if row >= 0:
            self._detalles.pop(row)
            self._refresh_table()

    def _refresh_table(self):
        self.tbl_dets.setRowCount(0)
        sub_t = iva_t = 0
        for it in self._detalles:
            r = self.tbl_dets.rowCount()
            self.tbl_dets.insertRow(r)
            self.tbl_dets.setItem(r, 0, table_item(it['codigo_principal']))
            self.tbl_dets.setItem(r, 1, table_item(it['descripcion']))
            self.tbl_dets.setItem(r, 2, table_item(f'{it["cantidad"]:.2f}', True))
            self.tbl_dets.setItem(r, 3, table_item(f'${it["precio_unitario"]:.4f}', True))
            self.tbl_dets.setItem(r, 4, table_item(f'${it["descuento"]:.2f}', True))
            self.tbl_dets.setItem(r, 5, table_item(f'{it["impuesto_tarifa"]:.0f}%', True))
            self.tbl_dets.setItem(r, 6, table_item(f'${it["precio_total_sin_impuesto"]:.2f}', True))
            sub_t += it['precio_total_sin_impuesto']
            iva_t += it['impuesto_valor']
        self.lbl_sub.setText(f'Subtotal: ${sub_t:.2f}')
        self.lbl_iva.setText(f'IVA: ${iva_t:.2f}')
        self.lbl_total.setText(f'TOTAL: ${sub_t + iva_t:.2f}')

    def _validate(self):
        if self.cmb_cliente.currentData() is None:
            show_error(self, 'Seleccione un cliente')
            return
        if not self._detalles:
            show_error(self, 'Agregue al menos un ítem')
            return
        self.accept()

    def get_data(self):
        return {
            'empresa_id': api.empresa_id(), 'usuario_id': api.usuario_id(),
            'cliente_id': self.cmb_cliente.currentData(),
            'fecha_emision': self.txt_fecha.date().toString('yyyy-MM-dd'),
            'forma_pago': self.cmb_forma_pago.currentData(),
            'observacion': self.txt_obs.text().strip(),
            'detalles': self._detalles,
        }


class FacturasScreen(BaseScreen):
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 16)
        lay.setSpacing(14)

        for w in self._page_header('🧾  Facturas', 'Gestión de comprobantes de venta').children():
            pass
        header_lay = self._page_header('🧾  Facturas', 'Comprobantes de venta electrónicos')
        lay.addLayout(header_lay)

        # Toolbar
        tb = QHBoxLayout()
        self.txt_search = SearchBar('Buscar por cliente, identificación...')
        self.txt_search.setFixedWidth(340)
        self.txt_search.returnPressed.connect(self._search)
        btn_new = make_btn('+ Nueva Factura', 'primary')
        btn_new.setFixedHeight(36)
        btn_new.clicked.connect(self._new)
        tb.addWidget(self.txt_search)
        tb.addStretch()
        tb.addWidget(btn_new)
        lay.addLayout(tb)

        self.table = make_table(['N° Factura', 'Fecha', 'Cliente', 'RUC/CI', 'Total', 'Estado', 'Autorización', 'Acciones'])
        self.table.setColumnWidth(0, 130)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 220)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 105)
        self.table.setColumnWidth(6, 140)
        self.table.verticalHeader().setDefaultSectionSize(38)
        lay.addWidget(self.table)

    def refresh(self):
        self._run(api.get, self._on_data, f'/api/facturas/{api.empresa_id()}')

    def _search(self):
        q = self.txt_search.text().strip()
        self._run(api.get, self._on_data, f'/api/facturas/{api.empresa_id()}', params={'q': q})

    def _on_data(self, result):
        if not result.get('ok'):
            return
        self.table.setRowCount(0)
        for row in result['data']:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, table_item(row['numero_formateado']))
            self.table.setItem(r, 1, table_item(row['fecha_emision']))
            self.table.setItem(r, 2, table_item(row['cliente_nombre']))
            self.table.setItem(r, 3, table_item(row['cliente_identificacion']))
            self.table.setItem(r, 4, table_item(f'${row["total"]:.2f}', True))
            set_estado_item(self.table, r, 5, row['estado'])
            auth = row['numero_autorizacion']
            self.table.setItem(r, 6, table_item(auth[:18] + '…' if len(auth) > 18 else auth))
            self.table.setCellWidget(r, 7, self._make_actions(row))

    def _make_actions(self, row):
        cell = QWidget()
        cl = QHBoxLayout(cell)
        cl.setContentsMargins(4, 3, 4, 3)
        cl.setSpacing(4)
        if row['estado'] == 'PENDIENTE':
            b = make_btn('▶ Autorizar', 'primary')
            b.setFixedHeight(28)
            b.clicked.connect(lambda _, d=row: self._autorizar_id(d['id']))
            cl.addWidget(b)
        if row['estado'] == 'AUTORIZADO':
            for lbl, cb in [('PDF', self._pdf), ('XML', self._xml), ('🖨', self._ticket)]:
                b = make_btn(lbl, 'secondary')
                b.setFixedHeight(28)
                b.clicked.connect(lambda _, d=row, fn=cb: fn(d))
                cl.addWidget(b)
        return cell

    def _new(self):
        dlg = NuevaFacturaDialog(self)
        if dlg.exec_() == dlg.Accepted:
            result = api.post('/api/facturas/', dlg.get_data())
            if result.get('ok'):
                fid = result['data']['id']
                if confirm(self, '¿Autorizar la factura ahora?'):
                    self._autorizar_id(fid)
                else:
                    toast(self, 'Factura guardada como PENDIENTE', 'warning')
                    self.refresh()
            else:
                show_error(self, result.get('error', 'Error al crear factura'))

    def _autorizar_id(self, fid):
        toast(self, 'Enviando al SRI…', 'info')
        def do():
            return api.post(f'/api/facturas/{fid}/autorizar')
        w = LoadWorker(do)
        w.done.connect(self._on_auth_done)
        w.start()
        self._workers.append(w)

    def _on_auth_done(self, result):
        if result.get('ok'):
            toast(self, '✓ Factura autorizada por el SRI', 'ok')
        else:
            toast(self, f'No autorizada: {result.get("error", "Error")}', 'error')
        self.refresh()

    def _pdf(self, data):
        content, err = api.download(f'/api/facturas/{data["id"]}/pdf')
        if err:
            show_error(self, err)
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Guardar PDF', f'RIDE_{data["clave_acceso"]}.pdf', 'PDF (*.pdf)')
        if path:
            with open(path, 'wb') as f:
                f.write(content)
            toast(self, f'PDF guardado', 'ok')

    def _xml(self, data):
        content, err = api.download(f'/api/facturas/{data["id"]}/xml')
        if err:
            show_error(self, err)
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Guardar XML', f'{data["clave_acceso"]}.xml', 'XML (*.xml)')
        if path:
            with open(path, 'wb') as f:
                f.write(content)
            toast(self, 'XML guardado', 'ok')

    def _ticket(self, data):
        r = api.get(f'/api/facturas/{data["id"]}')
        if not r.get('ok'):
            show_error(self, 'Error al obtener datos')
            return
        try:
            imprimir_ticket_factura(r['data'])
            toast(self, 'Ticket enviado a la impresora', 'ok')
        except Exception as e:
            show_error(self, f'Error de impresión: {e}')
