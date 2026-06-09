from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialog, QFormLayout,
    QComboBox, QDialogButtonBox, QDoubleSpinBox, QDateEdit
)
from PyQt5.QtCore import QDate
from ..widgets import (BaseScreen, make_btn, make_table, table_item,
                       show_error, confirm, SCREEN_STYLE)
from .. import api

TIPOS_DOC = [('01', 'Factura'), ('03', 'Liquidación de Compra'), ('07', 'Comprobante de Retención')]


class CompraDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('Factura de Proveedor')
        self.setMinimumWidth(420)
        self.setStyleSheet(SCREEN_STYLE)
        self.data = data or {}
        self._proveedores = []
        self._build()
        self._load_data()

    def _build(self):
        lay = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.cmb_proveedor = QComboBox()
        self.cmb_proveedor.setEditable(True)
        self.cmb_proveedor.setMinimumWidth(280)

        self.cmb_tipo = QComboBox()
        for c, l in TIPOS_DOC:
            self.cmb_tipo.addItem(l, c)
        if self.data.get('tipo_documento'):
            idx = next((i for i, (c, _) in enumerate(TIPOS_DOC) if c == self.data['tipo_documento']), 0)
            self.cmb_tipo.setCurrentIndex(idx)

        self.txt_num_doc = QLineEdit(self.data.get('numero_documento', ''))
        self.txt_num_doc.setPlaceholderText('001-001-000000001')

        self.txt_fecha = QDateEdit()
        self.txt_fecha.setCalendarPopup(True)
        self.txt_fecha.setDisplayFormat('yyyy-MM-dd')
        if self.data.get('fecha_emision'):
            from PyQt5.QtCore import QDate as QD
            self.txt_fecha.setDate(QD.fromString(self.data['fecha_emision'], 'yyyy-MM-dd'))
        else:
            self.txt_fecha.setDate(QDate.currentDate())

        self.spn_subtotal = QDoubleSpinBox()
        self.spn_subtotal.setRange(0, 9999999)
        self.spn_subtotal.setDecimals(2)
        self.spn_subtotal.setValue(float(self.data.get('subtotal', 0)))

        self.spn_iva = QDoubleSpinBox()
        self.spn_iva.setRange(0, 9999999)
        self.spn_iva.setDecimals(2)
        self.spn_iva.setValue(float(self.data.get('iva', 0)))

        self.spn_total = QDoubleSpinBox()
        self.spn_total.setRange(0, 9999999)
        self.spn_total.setDecimals(2)
        self.spn_total.setValue(float(self.data.get('total', 0)))

        self.txt_obs = QLineEdit(self.data.get('observacion', ''))

        form.addRow('Proveedor *:', self.cmb_proveedor)
        form.addRow('Tipo Documento:', self.cmb_tipo)
        form.addRow('N° Documento *:', self.txt_num_doc)
        form.addRow('Fecha Emisión:', self.txt_fecha)
        form.addRow('Subtotal:', self.spn_subtotal)
        form.addRow('IVA:', self.spn_iva)
        form.addRow('Total *:', self.spn_total)
        form.addRow('Observación:', self.txt_obs)

        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _load_data(self):
        r = api.get(f'/api/proveedores/{api.empresa_id()}')
        if r.get('ok'):
            self._proveedores = r['data']
            for p in self._proveedores:
                self.cmb_proveedor.addItem(f'{p["identificacion"]} - {p["razon_social"]}', p['id'])
            if self.data.get('proveedor_id'):
                idx = next((i for i, p in enumerate(self._proveedores) if p['id'] == self.data['proveedor_id']), -1)
                if idx >= 0:
                    self.cmb_proveedor.setCurrentIndex(idx)

    def _validate(self):
        if not self.cmb_proveedor.currentData():
            show_error(self, 'Seleccione un proveedor')
            return
        if not self.txt_num_doc.text().strip():
            show_error(self, 'Ingrese el número del documento')
            return
        self.accept()

    def get_data(self):
        return {
            'empresa_id': api.empresa_id(),
            'proveedor_id': self.cmb_proveedor.currentData(),
            'tipo_documento': self.cmb_tipo.currentData(),
            'numero_documento': self.txt_num_doc.text().strip(),
            'fecha_emision': self.txt_fecha.date().toString('yyyy-MM-dd'),
            'subtotal': self.spn_subtotal.value(),
            'iva': self.spn_iva.value(),
            'total': self.spn_total.value(),
            'observacion': self.txt_obs.text().strip(),
        }


class ComprasScreen(BaseScreen):
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        title = QLabel('Facturas de Proveedores')
        title.setObjectName('page_title')
        lay.addWidget(title)

        toolbar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText('Buscar por proveedor o número...')
        self.txt_search.setFixedHeight(36)
        self.txt_search.returnPressed.connect(self._search)
        btn_new = make_btn('+ Registrar Compra', 'primary')
        btn_new.clicked.connect(self._new)
        toolbar.addWidget(self.txt_search)
        toolbar.addWidget(btn_new)
        lay.addLayout(toolbar)

        self.table = make_table(['Fecha', 'Proveedor', 'N° Documento', 'Subtotal', 'IVA', 'Total', 'Acciones'])
        self.table.setColumnWidth(0, 95)
        self.table.setColumnWidth(1, 260)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 90)
        lay.addWidget(self.table)

    def refresh(self):
        self._run(api.get, self._on_data, f'/api/compras/{api.empresa_id()}')

    def _search(self):
        q = self.txt_search.text().strip()
        self._run(api.get, self._on_data, f'/api/compras/{api.empresa_id()}', params={'q': q})

    def _on_data(self, result):
        if not result.get('ok'):
            return
        self.table.setRowCount(0)
        for row in result['data']:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, table_item(row['fecha_emision']))
            self.table.setItem(r, 1, table_item(row['proveedor_nombre']))
            self.table.setItem(r, 2, table_item(row['numero_documento']))
            self.table.setItem(r, 3, table_item(f'${row["subtotal"]:.2f}', center=True))
            self.table.setItem(r, 4, table_item(f'${row["iva"]:.2f}', center=True))
            self.table.setItem(r, 5, table_item(f'${row["total"]:.2f}', center=True))

            from PyQt5.QtWidgets import QWidget, QHBoxLayout
            cell = QWidget()
            cl = QHBoxLayout(cell)
            cl.setContentsMargins(2, 2, 2, 2)
            btn_e = make_btn('Editar', 'secondary')
            btn_e.setFixedHeight(26)
            btn_e.clicked.connect(lambda _, d=row: self._edit(d))
            btn_d = make_btn('Eliminar', 'danger')
            btn_d.setFixedHeight(26)
            btn_d.clicked.connect(lambda _, d=row: self._delete(d))
            cl.addWidget(btn_e)
            cl.addWidget(btn_d)
            self.table.setCellWidget(r, 6, cell)
            self.table.setRowHeight(r, 34)

    def _new(self):
        dlg = CompraDialog(self)
        if dlg.exec_() == dlg.Accepted:
            result = api.post('/api/compras/', dlg.get_data())
            if result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error'))

    def _edit(self, data):
        dlg = CompraDialog(self, data)
        if dlg.exec_() == dlg.Accepted:
            result = api.put(f'/api/compras/{data["id"]}', dlg.get_data())
            if result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error'))

    def _delete(self, data):
        if confirm(self, f'¿Eliminar compra N° {data["numero_documento"]}?'):
            api.delete(f'/api/compras/{data["id"]}')
            self.refresh()
