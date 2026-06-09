from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QDialog,
    QFormLayout, QComboBox, QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt
from ..widgets import (BaseScreen, make_btn, make_table, table_item,
                       show_error, show_info, confirm, SCREEN_STYLE)
from .. import api


TIPO_ID = [('04', 'RUC'), ('05', 'Cédula'), ('06', 'Pasaporte'), ('07', 'Consumidor Final')]


class ClienteDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('Cliente')
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
        if not self.identificacion.text().strip():
            show_error(self, 'Ingrese la identificación')
            return
        if not self.razon_social.text().strip():
            show_error(self, 'Ingrese la razón social')
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


class ClientesScreen(BaseScreen):
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        title = QLabel('Clientes')
        title.setObjectName('page_title')
        lay.addWidget(title)

        toolbar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText('Buscar por nombre o identificación...')
        self.txt_search.setFixedHeight(36)
        self.txt_search.textChanged.connect(self._search)
        btn_new = make_btn('+ Nuevo Cliente', 'primary')
        btn_new.clicked.connect(self._new)
        toolbar.addWidget(self.txt_search)
        toolbar.addWidget(btn_new)
        lay.addLayout(toolbar)

        self.table = make_table(['ID', 'Tipo', 'Identificación', 'Razón Social', 'Email', 'Teléfono', 'Acciones'])
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 250)
        self.table.setColumnWidth(4, 170)
        self.table.setColumnWidth(5, 110)
        lay.addWidget(self.table)

        self._data = []

    def refresh(self):
        self._run(api.get, self._on_data, f'/api/clientes/{api.empresa_id()}')

    def _search(self, q):
        self._run(api.get, self._on_data, f'/api/clientes/{api.empresa_id()}', params={'q': q})

    def _on_data(self, result):
        if not result.get('ok'):
            return
        self._data = result['data']
        self._fill_table(self._data)

    def _fill_table(self, rows):
        tipo_map = dict(TIPO_ID)
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, table_item(row['id'], center=True))
            self.table.setItem(r, 1, table_item(tipo_map.get(row['tipo_identificacion'], row['tipo_identificacion']), center=True))
            self.table.setItem(r, 2, table_item(row['identificacion']))
            self.table.setItem(r, 3, table_item(row['razon_social']))
            self.table.setItem(r, 4, table_item(row['email']))
            self.table.setItem(r, 5, table_item(row['telefono']))

            from PyQt5.QtWidgets import QWidget, QHBoxLayout
            cell = QWidget()
            cell_lay = QHBoxLayout(cell)
            cell_lay.setContentsMargins(4, 2, 4, 2)
            btn_edit = make_btn('Editar', 'secondary')
            btn_edit.setFixedHeight(26)
            btn_del = make_btn('Eliminar', 'danger')
            btn_del.setFixedHeight(26)
            btn_edit.clicked.connect(lambda _, d=row: self._edit(d))
            btn_del.clicked.connect(lambda _, d=row: self._delete(d))
            cell_lay.addWidget(btn_edit)
            cell_lay.addWidget(btn_del)
            self.table.setCellWidget(r, 6, cell)
            self.table.setRowHeight(r, 34)

    def _new(self):
        dlg = ClienteDialog(self)
        if dlg.exec_() == dlg.Accepted:
            result = api.post('/api/clientes/', dlg.get_data())
            if result.get('ok'):
                show_info(self, 'Cliente creado correctamente')
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error al crear cliente'))

    def _edit(self, data):
        dlg = ClienteDialog(self, data)
        if dlg.exec_() == dlg.Accepted:
            result = api.put(f'/api/clientes/{data["id"]}', dlg.get_data())
            if result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error al actualizar'))

    def _delete(self, data):
        if confirm(self, f'¿Eliminar cliente {data["razon_social"]}?'):
            result = api.delete(f'/api/clientes/{data["id"]}')
            if result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error al eliminar'))
