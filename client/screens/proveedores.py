from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QDialog, QFormLayout, QComboBox, QDialogButtonBox
)
from ..widgets import (BaseScreen, make_btn, make_table, table_item,
                       show_error, show_info, confirm, SCREEN_STYLE)
from .. import api

TIPO_ID = [('04', 'RUC'), ('05', 'Cédula'), ('06', 'Pasaporte'), ('08', 'Identificación del Exterior')]


class ProveedorDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('Proveedor')
        self.setMinimumWidth(400)
        self.setStyleSheet(SCREEN_STYLE)
        self.data = data or {}
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.tipo = QComboBox()
        for code, label in TIPO_ID:
            self.tipo.addItem(label, code)
        if self.data.get('tipo_identificacion'):
            idx = next((i for i, (c, _) in enumerate(TIPO_ID) if c == self.data['tipo_identificacion']), 0)
            self.tipo.setCurrentIndex(idx)

        self.identificacion = QLineEdit(self.data.get('identificacion', ''))
        self.razon_social = QLineEdit(self.data.get('razon_social', ''))
        self.email = QLineEdit(self.data.get('email', ''))
        self.telefono = QLineEdit(self.data.get('telefono', ''))
        self.direccion = QLineEdit(self.data.get('direccion', ''))

        form.addRow('Tipo ID:', self.tipo)
        form.addRow('Identificación *:', self.identificacion)
        form.addRow('Razón Social *:', self.razon_social)
        form.addRow('Email:', self.email)
        form.addRow('Teléfono:', self.telefono)
        form.addRow('Dirección:', self.direccion)

        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _validate(self):
        if not self.identificacion.text().strip() or not self.razon_social.text().strip():
            show_error(self, 'Identificación y Razón Social son requeridos')
            return
        self.accept()

    def get_data(self):
        return {
            'tipo_identificacion': self.tipo.currentData(),
            'identificacion': self.identificacion.text().strip(),
            'razon_social': self.razon_social.text().strip(),
            'email': self.email.text().strip(),
            'telefono': self.telefono.text().strip(),
            'direccion': self.direccion.text().strip(),
            'empresa_id': api.empresa_id(),
        }


class ProveedoresScreen(BaseScreen):
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        title = QLabel('Proveedores')
        title.setObjectName('page_title')
        lay.addWidget(title)

        toolbar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText('Buscar por nombre o identificación...')
        self.txt_search.setFixedHeight(36)
        self.txt_search.textChanged.connect(self._search)
        btn_new = make_btn('+ Nuevo Proveedor', 'primary')
        btn_new.clicked.connect(self._new)
        toolbar.addWidget(self.txt_search)
        toolbar.addWidget(btn_new)
        lay.addLayout(toolbar)

        self.table = make_table(['ID', 'Tipo', 'Identificación', 'Razón Social', 'Email', 'Acciones'])
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 280)
        self.table.setColumnWidth(4, 180)
        lay.addWidget(self.table)

    def refresh(self):
        self._run(api.get, self._on_data, f'/api/proveedores/{api.empresa_id()}')

    def _search(self, q):
        self._run(api.get, self._on_data, f'/api/proveedores/{api.empresa_id()}', params={'q': q})

    def _on_data(self, result):
        if not result.get('ok'):
            return
        tipo_map = dict(TIPO_ID)
        self.table.setRowCount(0)
        for row in result['data']:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, table_item(row['id'], center=True))
            self.table.setItem(r, 1, table_item(tipo_map.get(row['tipo_identificacion'], row['tipo_identificacion']), center=True))
            self.table.setItem(r, 2, table_item(row['identificacion']))
            self.table.setItem(r, 3, table_item(row['razon_social']))
            self.table.setItem(r, 4, table_item(row['email']))

            from PyQt5.QtWidgets import QWidget, QHBoxLayout
            cell = QWidget()
            cl = QHBoxLayout(cell)
            cl.setContentsMargins(4, 2, 4, 2)
            btn_e = make_btn('Editar', 'secondary')
            btn_e.setFixedHeight(26)
            btn_d = make_btn('Eliminar', 'danger')
            btn_d.setFixedHeight(26)
            btn_e.clicked.connect(lambda _, d=row: self._edit(d))
            btn_d.clicked.connect(lambda _, d=row: self._delete(d))
            cl.addWidget(btn_e)
            cl.addWidget(btn_d)
            self.table.setCellWidget(r, 5, cell)
            self.table.setRowHeight(r, 34)

    def _new(self):
        dlg = ProveedorDialog(self)
        if dlg.exec_() == dlg.Accepted:
            result = api.post('/api/proveedores/', dlg.get_data())
            if result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error al crear'))

    def _edit(self, data):
        dlg = ProveedorDialog(self, data)
        if dlg.exec_() == dlg.Accepted:
            result = api.put(f'/api/proveedores/{data["id"]}', dlg.get_data())
            if result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error'))

    def _delete(self, data):
        if confirm(self, f'¿Eliminar proveedor {data["razon_social"]}?'):
            api.delete(f'/api/proveedores/{data["id"]}')
            self.refresh()
