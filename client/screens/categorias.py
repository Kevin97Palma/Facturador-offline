from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDialog, QFormLayout, QDialogButtonBox
)
from ..widgets import (BaseScreen, make_btn, make_table, table_item,
                       show_error, confirm, SCREEN_STYLE)
from .. import api


class CategoriaDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('Categoría')
        self.setMinimumWidth(350)
        self.setStyleSheet(SCREEN_STYLE)
        self.data = data or {}
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.nombre = QLineEdit(self.data.get('nombre', ''))
        self.descripcion = QLineEdit(self.data.get('descripcion', ''))
        form.addRow('Nombre *:', self.nombre)
        form.addRow('Descripción:', self.descripcion)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _validate(self):
        if not self.nombre.text().strip():
            show_error(self, 'Ingrese el nombre')
            return
        self.accept()

    def get_data(self):
        return {
            'nombre': self.nombre.text().strip(),
            'descripcion': self.descripcion.text().strip(),
            'empresa_id': api.empresa_id(),
        }


class CategoriasScreen(BaseScreen):
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        title = QLabel('Categorías')
        title.setObjectName('page_title')
        lay.addWidget(title)

        toolbar = QHBoxLayout()
        btn_new = make_btn('+ Nueva Categoría', 'primary')
        btn_new.clicked.connect(self._new)
        toolbar.addStretch()
        toolbar.addWidget(btn_new)
        lay.addLayout(toolbar)

        self.table = make_table(['ID', 'Nombre', 'Descripción', 'Acciones'])
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 300)
        lay.addWidget(self.table)

    def refresh(self):
        self._run(api.get, self._on_data, f'/api/categorias/{api.empresa_id()}')

    def _on_data(self, result):
        if not result.get('ok'):
            return
        self.table.setRowCount(0)
        for row in result['data']:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, table_item(row['id'], center=True))
            self.table.setItem(r, 1, table_item(row['nombre']))
            self.table.setItem(r, 2, table_item(row['descripcion']))

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
            self.table.setCellWidget(r, 3, cell)
            self.table.setRowHeight(r, 34)

    def _new(self):
        dlg = CategoriaDialog(self)
        if dlg.exec_() == dlg.Accepted:
            result = api.post('/api/categorias/', dlg.get_data())
            if result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error'))

    def _edit(self, data):
        dlg = CategoriaDialog(self, data)
        if dlg.exec_() == dlg.Accepted:
            result = api.put(f'/api/categorias/{data["id"]}', dlg.get_data())
            if result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error'))

    def _delete(self, data):
        if confirm(self, f'¿Eliminar categoría {data["nombre"]}?'):
            api.delete(f'/api/categorias/{data["id"]}')
            self.refresh()
