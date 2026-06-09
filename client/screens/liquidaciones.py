from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialog, QFormLayout,
    QComboBox, QDialogButtonBox, QDoubleSpinBox, QDateEdit, QWidget,
    QAbstractItemView, QTableWidget, QTableWidgetItem, QFileDialog
)
from PyQt5.QtCore import QDate
from ..widgets import (BaseScreen, make_btn, make_table, table_item,
                       set_estado_item, show_error, show_info, confirm, SCREEN_STYLE, LoadWorker)
from .. import api

FORMAS_PAGO = [('01', 'Sin utilización del sistema financiero'), ('19', 'Tarjeta de crédito')]


class LiquidacionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Nueva Liquidación de Compra')
        self.setMinimumSize(860, 600)
        self.setStyleSheet(SCREEN_STYLE)
        self._proveedores = []
        self._impuestos = []
        self._detalles = []
        self._build()
        self._load_data()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        form = QHBoxLayout()
        left = QFormLayout()
        right = QFormLayout()

        self.cmb_proveedor = QComboBox()
        self.cmb_proveedor.setEditable(True)
        self.cmb_proveedor.setMinimumWidth(280)
        self.txt_fecha = QDateEdit(QDate.currentDate())
        self.txt_fecha.setCalendarPopup(True)
        self.txt_fecha.setDisplayFormat('yyyy-MM-dd')
        self.cmb_forma_pago = QComboBox()
        for c, l in FORMAS_PAGO:
            self.cmb_forma_pago.addItem(l, c)
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText('Observación')

        left.addRow('Proveedor *:', self.cmb_proveedor)
        left.addRow('Fecha Emisión:', self.txt_fecha)
        right.addRow('Forma de Pago:', self.cmb_forma_pago)
        right.addRow('Observación:', self.txt_obs)

        form.addLayout(left)
        form.addLayout(right)
        lay.addLayout(form)

        entry = QHBoxLayout()
        self.txt_cod = QLineEdit()
        self.txt_cod.setPlaceholderText('Código')
        self.txt_cod.setFixedWidth(110)
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText('Descripción')
        self.txt_desc.setMinimumWidth(180)
        self.spn_cant = QDoubleSpinBox()
        self.spn_cant.setRange(0.01, 99999)
        self.spn_cant.setValue(1)
        self.spn_cant.setFixedWidth(80)
        self.spn_precio = QDoubleSpinBox()
        self.spn_precio.setRange(0, 999999)
        self.spn_precio.setDecimals(4)
        self.spn_precio.setFixedWidth(110)
        self.cmb_iva = QComboBox()
        self.cmb_iva.setFixedWidth(100)
        btn_add = make_btn('+ Agregar', 'primary')
        btn_add.clicked.connect(self._add_item)

        entry.addWidget(QLabel('Cód.:'))
        entry.addWidget(self.txt_cod)
        entry.addWidget(QLabel('Desc.:'))
        entry.addWidget(self.txt_desc)
        entry.addWidget(QLabel('Cant.:'))
        entry.addWidget(self.spn_cant)
        entry.addWidget(QLabel('Precio:'))
        entry.addWidget(self.spn_precio)
        entry.addWidget(QLabel('IVA:'))
        entry.addWidget(self.cmb_iva)
        entry.addWidget(btn_add)
        lay.addLayout(entry)

        self.tbl = QTableWidget(0, 5)
        self.tbl.setHorizontalHeaderLabels(['Código', 'Descripción', 'Cant.', 'Precio', 'Subtotal'])
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self.tbl.setFixedHeight(200)
        lay.addWidget(self.tbl)

        btn_del = make_btn('Quitar seleccionado', 'danger')
        btn_del.clicked.connect(self._remove_item)
        lay.addWidget(btn_del, alignment=0x0002)

        self.lbl_total = QLabel('TOTAL: $0.00')
        self.lbl_total.setStyleSheet('font-size: 15px; font-weight: bold; color: #e94560;')
        lay.addWidget(self.lbl_total, alignment=0x0002)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText('Guardar Liquidación')
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _load_data(self):
        r = api.get(f'/api/proveedores/{api.empresa_id()}')
        if r.get('ok'):
            self._proveedores = r['data']
            for p in self._proveedores:
                self.cmb_proveedor.addItem(f'{p["identificacion"]} - {p["razon_social"]}', p['id'])
        r = api.get(f'/api/impuestos/{api.empresa_id()}')
        if r.get('ok'):
            self._impuestos = r['data']
            for i in self._impuestos:
                self.cmb_iva.addItem(i['nombre'], i)

    def _add_item(self):
        desc = self.txt_desc.text().strip()
        imp = self.cmb_iva.currentData()
        if not desc or not imp:
            return
        cant = self.spn_cant.value()
        precio = self.spn_precio.value()
        subtotal = round(cant * precio, 2)
        iva_val = round(subtotal * float(imp['porcentaje']) / 100, 2)
        self._detalles.append({
            'codigo_principal': self.txt_cod.text().strip(),
            'descripcion': desc, 'cantidad': cant, 'precio_unitario': precio,
            'descuento': 0, 'precio_total_sin_impuesto': subtotal,
            'impuesto_codigo': imp['codigo'],
            'impuesto_codigo_porcentaje': imp['codigo_porcentaje'],
            'impuesto_tarifa': float(imp['porcentaje']), 'impuesto_valor': iva_val,
        })
        self._refresh_table()
        self.txt_cod.clear()
        self.txt_desc.clear()

    def _remove_item(self):
        row = self.tbl.currentRow()
        if row >= 0:
            self._detalles.pop(row)
            self._refresh_table()

    def _refresh_table(self):
        self.tbl.setRowCount(0)
        total = 0
        for d in self._detalles:
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            self.tbl.setItem(r, 0, QTableWidgetItem(d['codigo_principal']))
            self.tbl.setItem(r, 1, QTableWidgetItem(d['descripcion']))
            self.tbl.setItem(r, 2, QTableWidgetItem(f'{d["cantidad"]:.2f}'))
            self.tbl.setItem(r, 3, QTableWidgetItem(f'${d["precio_unitario"]:.4f}'))
            sub_iva = d['precio_total_sin_impuesto'] + d['impuesto_valor']
            self.tbl.setItem(r, 4, QTableWidgetItem(f'${sub_iva:.2f}'))
            total += sub_iva
        self.lbl_total.setText(f'TOTAL: ${total:.2f}')

    def _validate(self):
        if not self.cmb_proveedor.currentData():
            show_error(self, 'Seleccione un proveedor')
            return
        if not self._detalles:
            show_error(self, 'Agregue al menos un ítem')
            return
        self.accept()

    def get_data(self):
        return {
            'empresa_id': api.empresa_id(), 'usuario_id': api.usuario_id(),
            'proveedor_id': self.cmb_proveedor.currentData(),
            'fecha_emision': self.txt_fecha.date().toString('yyyy-MM-dd'),
            'forma_pago': self.cmb_forma_pago.currentData(),
            'observacion': self.txt_obs.text().strip(),
            'detalles': self._detalles,
        }


class LiquidacionesScreen(BaseScreen):
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        title = QLabel('Liquidaciones de Compra')
        title.setObjectName('page_title')
        lay.addWidget(title)

        toolbar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText('Buscar por proveedor...')
        self.txt_search.setFixedHeight(36)
        self.txt_search.returnPressed.connect(self._search)
        btn_new = make_btn('+ Nueva Liquidación', 'primary')
        btn_new.clicked.connect(self._new)
        toolbar.addWidget(self.txt_search)
        toolbar.addWidget(btn_new)
        lay.addLayout(toolbar)

        self.table = make_table(['#', 'Fecha', 'Proveedor', 'Total', 'Estado', 'Acciones'])
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 95)
        self.table.setColumnWidth(2, 280)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 100)
        lay.addWidget(self.table)

    def refresh(self):
        self._run(api.get, self._on_data, f'/api/liquidaciones/{api.empresa_id()}')

    def _search(self):
        q = self.txt_search.text().strip()
        self._run(api.get, self._on_data, f'/api/liquidaciones/{api.empresa_id()}', params={'q': q})

    def _on_data(self, result):
        if not result.get('ok'):
            return
        self.table.setRowCount(0)
        for row in result['data']:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, table_item(row['numero_formateado']))
            self.table.setItem(r, 1, table_item(row['fecha_emision']))
            self.table.setItem(r, 2, table_item(row['proveedor_nombre']))
            self.table.setItem(r, 3, table_item(f'${row["total"]:.2f}', center=True))
            set_estado_item(self.table, r, 4, row['estado'])

            cell = QWidget()
            cl = QHBoxLayout(cell)
            cl.setContentsMargins(2, 2, 2, 2)
            if row['estado'] == 'PENDIENTE':
                btn_a = make_btn('Autorizar', 'primary')
                btn_a.setFixedHeight(26)
                btn_a.clicked.connect(lambda _, d=row: self._autorizar_id(d['id']))
                cl.addWidget(btn_a)
            if row['estado'] == 'AUTORIZADO':
                btn_pdf = make_btn('PDF', 'secondary')
                btn_pdf.setFixedHeight(26)
                btn_pdf.clicked.connect(lambda _, d=row: self._pdf(d))
                cl.addWidget(btn_pdf)
            self.table.setCellWidget(r, 5, cell)
            self.table.setRowHeight(r, 34)

    def _new(self):
        dlg = LiquidacionDialog(self)
        if dlg.exec_() == dlg.Accepted:
            result = api.post('/api/liquidaciones/', dlg.get_data())
            if result.get('ok') and confirm(self, '¿Autorizar ahora?'):
                self._autorizar_id(result['data']['id'])
            elif result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error'))

    def _autorizar_id(self, lid):
        def do():
            return api.post(f'/api/liquidaciones/{lid}/autorizar')
        w = LoadWorker(do)
        w.done.connect(lambda r: (show_info(self, 'Autorizada') if r.get('ok') else show_error(self, r.get('error', '')), self.refresh()))
        w.start()
        self._workers.append(w)

    def _pdf(self, data):
        content, err = api.download(f'/api/liquidaciones/{data["id"]}/pdf')
        if err:
            show_error(self, err)
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Guardar PDF', f'LC_{data["clave_acceso"]}.pdf', 'PDF (*.pdf)')
        if path:
            with open(path, 'wb') as f:
                f.write(content)
