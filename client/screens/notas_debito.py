from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialog, QFormLayout,
    QComboBox, QDialogButtonBox, QDoubleSpinBox, QDateEdit, QWidget,
    QAbstractItemView, QTableWidget, QTableWidgetItem, QFileDialog
)
from PyQt5.QtCore import QDate
from ..widgets import (BaseScreen, make_btn, make_table, table_item,
                       set_estado_item, show_error, show_info, confirm, SCREEN_STYLE, LoadWorker)
from .. import api

TIPOS_DOC = [('01', '01 - Factura'), ('03', '03 - Liquidación')]


class NotaDebitoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Nueva Nota de Débito')
        self.setMinimumSize(700, 520)
        self.setStyleSheet(SCREEN_STYLE)
        self._clientes = []
        self._razones = []
        self._build()
        self._load_data()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        form = QHBoxLayout()
        left = QFormLayout()
        right = QFormLayout()

        self.cmb_cliente = QComboBox()
        self.cmb_cliente.setEditable(True)
        self.cmb_cliente.setMinimumWidth(260)
        self.txt_fecha = QDateEdit(QDate.currentDate())
        self.txt_fecha.setCalendarPopup(True)
        self.txt_fecha.setDisplayFormat('yyyy-MM-dd')
        self.cmb_tipo_doc = QComboBox()
        for c, l in TIPOS_DOC:
            self.cmb_tipo_doc.addItem(l, c)
        self.txt_num_doc = QLineEdit()
        self.txt_num_doc.setPlaceholderText('001-001-000000001')
        self.txt_fecha_doc = QDateEdit(QDate.currentDate())
        self.txt_fecha_doc.setCalendarPopup(True)
        self.txt_fecha_doc.setDisplayFormat('yyyy-MM-dd')

        left.addRow('Cliente *:', self.cmb_cliente)
        left.addRow('Fecha Emisión:', self.txt_fecha)
        right.addRow('Tipo Doc. Modificado:', self.cmb_tipo_doc)
        right.addRow('N° Doc. Modificado *:', self.txt_num_doc)
        right.addRow('Fecha Doc. Sustento:', self.txt_fecha_doc)

        form.addLayout(left)
        form.addLayout(right)
        lay.addLayout(form)

        entry = QHBoxLayout()
        self.txt_razon = QLineEdit()
        self.txt_razon.setPlaceholderText('Razón del débito')
        self.txt_razon.setMinimumWidth(260)
        self.spn_valor = QDoubleSpinBox()
        self.spn_valor.setRange(0.01, 9999999)
        self.spn_valor.setDecimals(2)
        self.spn_valor.setFixedWidth(120)
        btn_add = make_btn('+ Agregar', 'primary')
        btn_add.clicked.connect(self._add_item)
        entry.addWidget(QLabel('Razón:'))
        entry.addWidget(self.txt_razon)
        entry.addWidget(QLabel('Valor:'))
        entry.addWidget(self.spn_valor)
        entry.addWidget(btn_add)
        lay.addLayout(entry)

        self.tbl = QTableWidget(0, 2)
        self.tbl.setHorizontalHeaderLabels(['Razón', 'Valor'])
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self.tbl.setFixedHeight(160)
        lay.addWidget(self.tbl)

        btn_del = make_btn('Quitar seleccionado', 'danger')
        btn_del.clicked.connect(self._remove_item)
        lay.addWidget(btn_del, alignment=0x0002)

        self.lbl_total = QLabel('TOTAL: $0.00')
        self.lbl_total.setStyleSheet('font-size: 15px; font-weight: bold; color: #e94560;')
        lay.addWidget(self.lbl_total, alignment=0x0002)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText('Guardar Nota de Débito')
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _load_data(self):
        r = api.get(f'/api/clientes/{api.empresa_id()}')
        if r.get('ok'):
            self._clientes = r['data']
            for c in self._clientes:
                self.cmb_cliente.addItem(f'{c["identificacion"]} - {c["razon_social"]}', c['id'])

    def _add_item(self):
        razon = self.txt_razon.text().strip()
        valor = self.spn_valor.value()
        if not razon:
            return
        self._razones.append({'razon': razon, 'valor': valor})
        self._refresh_table()
        self.txt_razon.clear()
        self.spn_valor.setValue(0)

    def _remove_item(self):
        row = self.tbl.currentRow()
        if row >= 0:
            self._razones.pop(row)
            self._refresh_table()

    def _refresh_table(self):
        self.tbl.setRowCount(0)
        total = 0
        for d in self._razones:
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            self.tbl.setItem(r, 0, QTableWidgetItem(d['razon']))
            self.tbl.setItem(r, 1, QTableWidgetItem(f'${d["valor"]:.2f}'))
            total += d['valor']
        self.lbl_total.setText(f'TOTAL: ${total:.2f}')

    def _validate(self):
        if not self.cmb_cliente.currentData():
            show_error(self, 'Seleccione un cliente')
            return
        if not self.txt_num_doc.text().strip():
            show_error(self, 'Ingrese el número del documento modificado')
            return
        if not self._razones:
            show_error(self, 'Agregue al menos una razón')
            return
        self.accept()

    def get_data(self):
        return {
            'empresa_id': api.empresa_id(), 'usuario_id': api.usuario_id(),
            'cliente_id': self.cmb_cliente.currentData(),
            'fecha_emision': self.txt_fecha.date().toString('yyyy-MM-dd'),
            'cod_doc_modificado': self.cmb_tipo_doc.currentData(),
            'num_doc_modificado': self.txt_num_doc.text().strip(),
            'fecha_emision_doc_sustento': self.txt_fecha_doc.date().toString('yyyy-MM-dd'),
            'detalles': self._razones,
        }


class NotasDebitoScreen(BaseScreen):
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        title = QLabel('Notas de Débito')
        title.setObjectName('page_title')
        lay.addWidget(title)

        toolbar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText('Buscar por cliente...')
        self.txt_search.setFixedHeight(36)
        self.txt_search.returnPressed.connect(self._search)
        btn_new = make_btn('+ Nueva N. Débito', 'primary')
        btn_new.clicked.connect(self._new)
        toolbar.addWidget(self.txt_search)
        toolbar.addWidget(btn_new)
        lay.addLayout(toolbar)

        self.table = make_table(['#', 'Fecha', 'Cliente', 'Doc. Mod.', 'Total', 'Estado', 'Acciones'])
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 95)
        self.table.setColumnWidth(2, 220)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 100)
        lay.addWidget(self.table)

    def refresh(self):
        self._run(api.get, self._on_data, f'/api/notas-debito/{api.empresa_id()}')

    def _search(self):
        q = self.txt_search.text().strip()
        self._run(api.get, self._on_data, f'/api/notas-debito/{api.empresa_id()}', params={'q': q})

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
            self.table.setItem(r, 3, table_item(row['num_doc_modificado']))
            self.table.setItem(r, 4, table_item(f'${row["total"]:.2f}', center=True))
            set_estado_item(self.table, r, 5, row['estado'])

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
            self.table.setCellWidget(r, 6, cell)
            self.table.setRowHeight(r, 34)

    def _new(self):
        dlg = NotaDebitoDialog(self)
        if dlg.exec_() == dlg.Accepted:
            result = api.post('/api/notas-debito/', dlg.get_data())
            if result.get('ok') and confirm(self, '¿Autorizar ahora?'):
                self._autorizar_id(result['data']['id'])
            elif result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error'))

    def _autorizar_id(self, nid):
        def do():
            return api.post(f'/api/notas-debito/{nid}/autorizar')
        w = LoadWorker(do)
        w.done.connect(lambda r: (show_info(self, 'Autorizada') if r.get('ok') else show_error(self, r.get('error', '')), self.refresh()))
        w.start()
        self._workers.append(w)

    def _pdf(self, data):
        content, err = api.download(f'/api/notas-debito/{data["id"]}/pdf')
        if err:
            show_error(self, err)
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Guardar PDF', f'ND_{data["clave_acceso"]}.pdf', 'PDF (*.pdf)')
        if path:
            with open(path, 'wb') as f:
                f.write(content)
