from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialog,
    QFormLayout, QComboBox, QDialogButtonBox, QDoubleSpinBox,
    QDateEdit, QTableWidget, QTableWidgetItem, QWidget, QAbstractItemView,
    QFileDialog
)
from PyQt5.QtCore import QDate
from ..widgets import (BaseScreen, make_btn, make_table, table_item,
                       set_estado_item, show_error, show_info, confirm, SCREEN_STYLE, LoadWorker)
from .. import api

CODIGOS_SUSTENTO = [
    ('01', '01 - Crédito tributario para declaración de IVA'),
    ('02', '02 - Costo o Gasto para declaración de IR'),
    ('03', '03 - Activo Fijo'),
    ('04', '04 - Liquidación de compras de bienes'),
    ('05', '05 - Puede sustentar crédito tributario y costo/gasto'),
    ('06', '06 - Sustento de gastos personales'),
]

TIPOS_DOC = [
    ('01', '01 - Factura'), ('03', '03 - Liquidación de Compra'),
    ('04', '04 - N. Crédito'), ('05', '05 - N. Débito'),
]


class DetalleRetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Agregar Retención')
        self.setMinimumWidth(450)
        self.setStyleSheet(SCREEN_STYLE)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.cod_sustento = QComboBox()
        for c, l in CODIGOS_SUSTENTO:
            self.cod_sustento.addItem(l, c)

        self.cod_doc_sustento = QComboBox()
        for c, l in TIPOS_DOC:
            self.cod_doc_sustento.addItem(l, c)

        self.num_doc = QLineEdit()
        self.num_doc.setPlaceholderText('001-001-000000001')
        self.fecha_doc = QDateEdit(QDate.currentDate())
        self.fecha_doc.setCalendarPopup(True)
        self.fecha_doc.setDisplayFormat('yyyy-MM-dd')

        self.codigo = QLineEdit()
        self.codigo.setPlaceholderText('Ej: 303, 304, 703...')
        self.descripcion = QLineEdit()

        self.base = QDoubleSpinBox()
        self.base.setRange(0.01, 9999999)
        self.base.setDecimals(2)

        self.porcentaje = QDoubleSpinBox()
        self.porcentaje.setRange(0.01, 100)
        self.porcentaje.setDecimals(2)

        form.addRow('Código Sustento:', self.cod_sustento)
        form.addRow('Tipo Doc. Sustento:', self.cod_doc_sustento)
        form.addRow('N° Doc. Sustento:', self.num_doc)
        form.addRow('Fecha Doc. Sustento:', self.fecha_doc)
        form.addRow('Código Retención *:', self.codigo)
        form.addRow('Descripción:', self.descripcion)
        form.addRow('Base Imponible *:', self.base)
        form.addRow('Porcentaje *:', self.porcentaje)
        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self):
        return {
            'codigo_sustento': self.cod_sustento.currentData(),
            'cod_doc_sustento': self.cod_doc_sustento.currentData(),
            'num_doc_sustento': self.num_doc.text().strip(),
            'fecha_emision_doc_sustento': self.fecha_doc.date().toString('yyyy-MM-dd'),
            'codigo': self.codigo.text().strip(),
            'descripcion': self.descripcion.text().strip(),
            'base_imponible': self.base.value(),
            'porcentaje': self.porcentaje.value(),
        }


class NuevaRetencionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Nueva Retención')
        self.setMinimumSize(800, 560)
        self.setStyleSheet(SCREEN_STYLE)
        self._proveedores = []
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
        self.txt_periodo = QLineEdit()
        self.txt_periodo.setPlaceholderText('MM/YYYY ej: 06/2024')

        left.addRow('Proveedor *:', self.cmb_proveedor)
        left.addRow('Fecha Emisión:', self.txt_fecha)
        right.addRow('Período Fiscal:', self.txt_periodo)

        form.addLayout(left)
        form.addLayout(right)
        lay.addLayout(form)

        toolbar = QHBoxLayout()
        btn_add = make_btn('+ Agregar Retención', 'primary')
        btn_add.clicked.connect(self._add_det)
        toolbar.addStretch()
        toolbar.addWidget(btn_add)
        lay.addLayout(toolbar)

        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels(['Cód.Ret.', 'Descripción', 'Base', '%', 'Valor', 'Doc Sustento'])
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self.tbl.setFixedHeight(200)
        lay.addWidget(self.tbl)

        btn_del = make_btn('Quitar seleccionado', 'danger')
        btn_del.clicked.connect(self._remove_det)
        lay.addWidget(btn_del, alignment=0x0002)  # AlignRight

        self.lbl_total = QLabel('Total retenido: $0.00')
        self.lbl_total.setStyleSheet('font-size: 15px; font-weight: bold; color: #e94560;')
        lay.addWidget(self.lbl_total, alignment=0x0002)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText('Guardar Retención')
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _load_data(self):
        r = api.get(f'/api/proveedores/{api.empresa_id()}')
        if r.get('ok'):
            self._proveedores = r['data']
            for p in self._proveedores:
                self.cmb_proveedor.addItem(f'{p["identificacion"]} - {p["razon_social"]}', p['id'])

    def _add_det(self):
        dlg = DetalleRetDialog(self)
        if dlg.exec_() == dlg.Accepted:
            d = dlg.get_data()
            d['valor_retenido'] = round(d['base_imponible'] * d['porcentaje'] / 100, 2)
            self._detalles.append(d)
            self._refresh_table()

    def _remove_det(self):
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
            self.tbl.setItem(r, 0, QTableWidgetItem(d['codigo']))
            self.tbl.setItem(r, 1, QTableWidgetItem(d['descripcion']))
            self.tbl.setItem(r, 2, QTableWidgetItem(f'${d["base_imponible"]:.2f}'))
            self.tbl.setItem(r, 3, QTableWidgetItem(f'{d["porcentaje"]:.2f}%'))
            self.tbl.setItem(r, 4, QTableWidgetItem(f'${d["valor_retenido"]:.2f}'))
            self.tbl.setItem(r, 5, QTableWidgetItem(d['num_doc_sustento']))
            total += d['valor_retenido']
        self.lbl_total.setText(f'Total retenido: ${total:.2f}')

    def _validate(self):
        if not self.cmb_proveedor.currentData():
            show_error(self, 'Seleccione un proveedor')
            return
        if not self._detalles:
            show_error(self, 'Agregue al menos una retención')
            return
        self.accept()

    def get_data(self):
        return {
            'empresa_id': api.empresa_id(),
            'usuario_id': api.usuario_id(),
            'proveedor_id': self.cmb_proveedor.currentData(),
            'fecha_emision': self.txt_fecha.date().toString('yyyy-MM-dd'),
            'periodo_fiscal': self.txt_periodo.text().strip(),
            'detalles': self._detalles,
        }


class RetencionesScreen(BaseScreen):
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        title = QLabel('Retenciones')
        title.setObjectName('page_title')
        lay.addWidget(title)

        toolbar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText('Buscar por proveedor...')
        self.txt_search.setFixedHeight(36)
        self.txt_search.returnPressed.connect(self._search)
        btn_new = make_btn('+ Nueva Retención', 'primary')
        btn_new.clicked.connect(self._new)
        toolbar.addWidget(self.txt_search)
        toolbar.addWidget(btn_new)
        lay.addLayout(toolbar)

        self.table = make_table(['#', 'Fecha', 'Proveedor', 'Total Ret.', 'Estado', 'Acciones'])
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 95)
        self.table.setColumnWidth(2, 280)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 100)
        lay.addWidget(self.table)

    def refresh(self):
        self._run(api.get, self._on_data, f'/api/retenciones/{api.empresa_id()}')

    def _search(self):
        q = self.txt_search.text().strip()
        self._run(api.get, self._on_data, f'/api/retenciones/{api.empresa_id()}', params={'q': q})

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
            self.table.setItem(r, 3, table_item(f'${row["total_retenido"]:.2f}', center=True))
            set_estado_item(self.table, r, 4, row['estado'])

            cell = QWidget()
            cl = QHBoxLayout(cell)
            cl.setContentsMargins(2, 2, 2, 2)
            cl.setSpacing(3)
            if row['estado'] == 'PENDIENTE':
                btn_a = make_btn('Autorizar', 'primary')
                btn_a.setFixedHeight(26)
                btn_a.clicked.connect(lambda _, d=row: self._autorizar(d))
                cl.addWidget(btn_a)
            if row['estado'] == 'AUTORIZADO':
                btn_pdf = make_btn('PDF', 'secondary')
                btn_pdf.setFixedHeight(26)
                btn_pdf.clicked.connect(lambda _, d=row: self._pdf(d))
                btn_xml = make_btn('XML', 'secondary')
                btn_xml.setFixedHeight(26)
                btn_xml.clicked.connect(lambda _, d=row: self._xml(d))
                cl.addWidget(btn_pdf)
                cl.addWidget(btn_xml)
            self.table.setCellWidget(r, 5, cell)
            self.table.setRowHeight(r, 34)

    def _new(self):
        dlg = NuevaRetencionDialog(self)
        if dlg.exec_() == dlg.Accepted:
            result = api.post('/api/retenciones/', dlg.get_data())
            if result.get('ok'):
                rid = result['data']['id']
                if confirm(self, '¿Autorizar ahora?'):
                    self._autorizar_id(rid)
                else:
                    self.refresh()
            else:
                show_error(self, result.get('error', 'Error'))

    def _autorizar(self, data):
        self._autorizar_id(data['id'])

    def _autorizar_id(self, rid):
        def do_auth():
            return api.post(f'/api/retenciones/{rid}/autorizar')
        w = LoadWorker(do_auth)
        w.done.connect(lambda r: (show_info(self, 'Autorizada') if r.get('ok') else show_error(self, r.get('error', 'Error')), self.refresh()))
        w.start()
        self._workers.append(w)

    def _pdf(self, data):
        content, err = api.download(f'/api/retenciones/{data["id"]}/pdf')
        if err:
            show_error(self, err)
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Guardar PDF', f'RET_{data["clave_acceso"]}.pdf', 'PDF (*.pdf)')
        if path:
            with open(path, 'wb') as f:
                f.write(content)

    def _xml(self, data):
        content, err = api.download(f'/api/retenciones/{data["id"]}/xml')
        if err:
            show_error(self, err)
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Guardar XML', f'{data["clave_acceso"]}.xml', 'XML (*.xml)')
        if path:
            with open(path, 'wb') as f:
                f.write(content)
