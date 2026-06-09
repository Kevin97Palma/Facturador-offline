from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDialog, QFormLayout, QComboBox, QDialogButtonBox, QDoubleSpinBox
)
from ..widgets import (BaseScreen, make_btn, make_table, table_item,
                       show_error, confirm, SCREEN_STYLE)
from .. import api


class ProductoDialog(QDialog):
    def __init__(self, parent=None, data=None, categorias=None, impuestos=None):
        super().__init__(parent)
        self.setWindowTitle('Producto')
        self.setMinimumWidth(400)
        self.setStyleSheet(SCREEN_STYLE)
        self.data = data or {}
        self.categorias = categorias or []
        self.impuestos = impuestos or []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.codigo = QLineEdit(self.data.get('codigo', ''))
        self.nombre = QLineEdit(self.data.get('nombre', ''))
        self.descripcion = QLineEdit(self.data.get('descripcion', ''))

        self.categoria = QComboBox()
        self.categoria.addItem('-- Sin categoría --', None)
        for c in self.categorias:
            self.categoria.addItem(c['nombre'], c['id'])
        if self.data.get('categoria_id'):
            idx = next((i+1 for i, c in enumerate(self.categorias) if c['id'] == self.data['categoria_id']), 0)
            self.categoria.setCurrentIndex(idx)

        self.impuesto = QComboBox()
        self.impuesto.addItem('-- Sin impuesto --', None)
        for imp in self.impuestos:
            self.impuesto.addItem(imp['nombre'], imp['id'])
        if self.data.get('impuesto_id'):
            idx = next((i+1 for i, imp in enumerate(self.impuestos) if imp['id'] == self.data['impuesto_id']), 0)
            self.impuesto.setCurrentIndex(idx)

        self.precio = QDoubleSpinBox()
        self.precio.setRange(0, 999999.99)
        self.precio.setDecimals(4)
        self.precio.setValue(float(self.data.get('precio_unitario', 0)))

        form.addRow('Código *:', self.codigo)
        form.addRow('Nombre *:', self.nombre)
        form.addRow('Descripción:', self.descripcion)
        form.addRow('Categoría:', self.categoria)
        form.addRow('Impuesto:', self.impuesto)
        form.addRow('Precio Unitario:', self.precio)

        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _validate(self):
        if not self.codigo.text().strip():
            show_error(self, 'Ingrese el código del producto')
            return
        if not self.nombre.text().strip():
            show_error(self, 'Ingrese el nombre del producto')
            return
        self.accept()

    def get_data(self):
        return {
            'codigo': self.codigo.text().strip(),
            'nombre': self.nombre.text().strip(),
            'descripcion': self.descripcion.text().strip(),
            'categoria_id': self.categoria.currentData(),
            'impuesto_id': self.impuesto.currentData(),
            'precio_unitario': self.precio.value(),
            'empresa_id': api.empresa_id(),
        }


class ProductosScreen(BaseScreen):
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        title = QLabel('Productos')
        title.setObjectName('page_title')
        lay.addWidget(title)

        toolbar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText('Buscar por nombre o código...')
        self.txt_search.setFixedHeight(36)
        self.txt_search.textChanged.connect(self._search)
        btn_new = make_btn('+ Nuevo Producto', 'primary')
        btn_new.clicked.connect(self._new)
        toolbar.addWidget(self.txt_search)
        toolbar.addWidget(btn_new)
        lay.addLayout(toolbar)

        self.table = make_table(['Código', 'Nombre', 'Impuesto', 'Precio', 'Acciones'])
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 280)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 100)
        lay.addWidget(self.table)

        self._categorias = []
        self._impuestos = []

    def refresh(self):
        eid = api.empresa_id()
        self._run(api.get, self._on_cats, f'/api/categorias/{eid}')
        self._run(api.get, self._on_imps, f'/api/impuestos/{eid}')
        self._run(api.get, self._on_data, f'/api/productos/{eid}')

    def _search(self, q):
        self._run(api.get, self._on_data, f'/api/productos/{api.empresa_id()}', params={'q': q})

    def _on_cats(self, r):
        if r.get('ok'):
            self._categorias = r['data']

    def _on_imps(self, r):
        if r.get('ok'):
            self._impuestos = r['data']

    def _on_data(self, result):
        if not result.get('ok'):
            return
        self.table.setRowCount(0)
        for row in result['data']:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, table_item(row['codigo']))
            self.table.setItem(r, 1, table_item(row['nombre']))
            tarifa = row.get('impuesto_tarifa', 0)
            self.table.setItem(r, 2, table_item(f'{tarifa}%', center=True))
            self.table.setItem(r, 3, table_item(f'${row["precio_unitario"]:.4f}', center=True))

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
            self.table.setCellWidget(r, 4, cell)
            self.table.setRowHeight(r, 34)

    def _new(self):
        dlg = ProductoDialog(self, categorias=self._categorias, impuestos=self._impuestos)
        if dlg.exec_() == dlg.Accepted:
            result = api.post('/api/productos/', dlg.get_data())
            if result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error'))

    def _edit(self, data):
        dlg = ProductoDialog(self, data=data, categorias=self._categorias, impuestos=self._impuestos)
        if dlg.exec_() == dlg.Accepted:
            result = api.put(f'/api/productos/{data["id"]}', dlg.get_data())
            if result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error'))

    def _delete(self, data):
        if confirm(self, f'¿Desactivar producto {data["nombre"]}?'):
            api.delete(f'/api/productos/{data["id"]}')
            self.refresh()
