import os
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialog, QFormLayout,
    QComboBox, QDialogButtonBox, QDoubleSpinBox, QDateEdit, QFileDialog,
    QTextEdit, QProgressBar, QWidget, QScrollArea, QFrame, QSizePolicy
)
from PyQt5.QtCore import QDate, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QColor
from ..widgets import (BaseScreen, make_btn, make_table, table_item,
                       toast, LoadWorker)
from .. import api

TIPOS_DOC = [
    ('01', 'Factura'),
    ('03', 'Liquidación de Compra'),
    ('07', 'Comprobante de Retención'),
]


# ─── Diálogo: Registro manual ─────────────────────────────────────────────────

class CompraDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('Factura de Proveedor')
        self.setMinimumWidth(460)
        self.data = data or {}
        self._proveedores = []
        self._build()
        self._load_data()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.cmb_proveedor = QComboBox()
        self.cmb_proveedor.setEditable(True)
        self.cmb_proveedor.setMinimumWidth(300)

        self.cmb_tipo = QComboBox()
        for c, l in TIPOS_DOC:
            self.cmb_tipo.addItem(l, c)
        if self.data.get('tipo_documento'):
            idx = next((i for i, (c, _) in enumerate(TIPOS_DOC)
                        if c == self.data['tipo_documento']), 0)
            self.cmb_tipo.setCurrentIndex(idx)

        self.txt_num_doc = QLineEdit(self.data.get('numero_documento', ''))
        self.txt_num_doc.setPlaceholderText('001-001-000000001')

        self.txt_num_aut = QLineEdit(self.data.get('numero_autorizacion', ''))
        self.txt_num_aut.setPlaceholderText('Clave de acceso 49 dígitos')

        self.txt_fecha = QDateEdit()
        self.txt_fecha.setCalendarPopup(True)
        self.txt_fecha.setDisplayFormat('yyyy-MM-dd')
        if self.data.get('fecha_emision'):
            self.txt_fecha.setDate(QDate.fromString(
                self.data['fecha_emision'], 'yyyy-MM-dd'))
        else:
            self.txt_fecha.setDate(QDate.currentDate())

        self.spn_subtotal = QDoubleSpinBox()
        self.spn_subtotal.setRange(0, 9_999_999)
        self.spn_subtotal.setDecimals(2)
        self.spn_subtotal.setValue(float(self.data.get('subtotal_sin_iva', 0)))
        self.spn_subtotal.valueChanged.connect(self._recalcular)

        self.spn_iva = QDoubleSpinBox()
        self.spn_iva.setRange(0, 9_999_999)
        self.spn_iva.setDecimals(2)
        self.spn_iva.setValue(float(self.data.get('iva', 0)))
        self.spn_iva.valueChanged.connect(self._recalcular)

        self.spn_total = QDoubleSpinBox()
        self.spn_total.setRange(0, 9_999_999)
        self.spn_total.setDecimals(2)
        self.spn_total.setValue(float(self.data.get('total', 0)))

        self.txt_obs = QLineEdit(self.data.get('observacion', ''))

        form.addRow('Proveedor *:', self.cmb_proveedor)
        form.addRow('Tipo Documento:', self.cmb_tipo)
        form.addRow('N° Documento *:', self.txt_num_doc)
        form.addRow('N° Autorización:', self.txt_num_aut)
        form.addRow('Fecha Emisión:', self.txt_fecha)
        form.addRow('Subtotal sin IVA:', self.spn_subtotal)
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
                self.cmb_proveedor.addItem(
                    f'{p["identificacion"]} - {p["razon_social"]}', p['id'])
            if self.data.get('proveedor_id'):
                idx = next((i for i, p in enumerate(self._proveedores)
                            if p['id'] == self.data['proveedor_id']), -1)
                if idx >= 0:
                    self.cmb_proveedor.setCurrentIndex(idx)

    def _recalcular(self):
        self.spn_total.setValue(
            round(self.spn_subtotal.value() + self.spn_iva.value(), 2))

    def _validate(self):
        if not self.cmb_proveedor.currentData():
            toast(self, 'Seleccione un proveedor', 'warning')
            return
        if not self.txt_num_doc.text().strip():
            toast(self, 'Ingrese el número del documento', 'warning')
            return
        self.accept()

    def get_data(self):
        return {
            'empresa_id': api.empresa_id(),
            'proveedor_id': self.cmb_proveedor.currentData(),
            'tipo_documento': self.cmb_tipo.currentData(),
            'numero_documento': self.txt_num_doc.text().strip(),
            'numero_autorizacion': self.txt_num_aut.text().strip(),
            'fecha_emision': self.txt_fecha.date().toString('yyyy-MM-dd'),
            'subtotal_sin_iva': self.spn_subtotal.value(),
            'subtotal_iva_0': 0,
            'subtotal_iva_12': self.spn_subtotal.value(),
            'iva': self.spn_iva.value(),
            'total': self.spn_total.value(),
            'observacion': self.txt_obs.text().strip(),
        }


# ─── Diálogo: Importar XMLs del SRI ──────────────────────────────────────────

class ImportarXmlDialog(QDialog):
    """
    Permite seleccionar uno o más archivos XML de comprobantes recibidos
    del SRI y los importa automáticamente parseando su contenido.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Importar Facturas desde XML')
        self.setMinimumSize(600, 480)
        self._xmls = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        # Cabecera informativa
        info = QLabel(
            '📂  Seleccione los archivos XML de comprobantes electrónicos '
            'recibidos de sus proveedores. El sistema los procesará '
            'automáticamente y registrará los datos.'
        )
        info.setWordWrap(True)
        info.setStyleSheet('color: #8b949e; font-size: 12px; padding: 8px 0;')
        lay.addWidget(info)

        # Botón seleccionar
        btn_row = QHBoxLayout()
        self.btn_seleccionar = make_btn('📂  Seleccionar archivos XML', 'secondary')
        self.btn_seleccionar.clicked.connect(self._seleccionar)
        self.lbl_conteo = QLabel('0 archivos seleccionados')
        self.lbl_conteo.setStyleSheet('color: #8b949e; font-size: 12px;')
        btn_row.addWidget(self.btn_seleccionar)
        btn_row.addWidget(self.lbl_conteo)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        # Lista de archivos
        self.txt_lista = QTextEdit()
        self.txt_lista.setReadOnly(True)
        self.txt_lista.setPlaceholderText('Los archivos seleccionados aparecerán aquí...')
        self.txt_lista.setMaximumHeight(120)
        lay.addWidget(self.txt_lista)

        # Barra de progreso
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(True)
        lay.addWidget(self.progress)

        # Resultados
        self.txt_resultados = QTextEdit()
        self.txt_resultados.setReadOnly(True)
        self.txt_resultados.setPlaceholderText('Los resultados de la importación aparecerán aquí...')
        lay.addWidget(self.txt_resultados)

        # Botones
        btn_box = QHBoxLayout()
        self.btn_importar = make_btn('⬆  Importar', 'primary')
        self.btn_importar.setEnabled(False)
        self.btn_importar.clicked.connect(self._importar)
        btn_cerrar = make_btn('Cerrar', 'secondary')
        btn_cerrar.clicked.connect(self.accept)
        btn_box.addStretch()
        btn_box.addWidget(self.btn_importar)
        btn_box.addWidget(btn_cerrar)
        lay.addLayout(btn_box)

    def _seleccionar(self):
        archivos, _ = QFileDialog.getOpenFileNames(
            self,
            'Seleccionar archivos XML',
            '',
            'Archivos XML (*.xml);;Todos los archivos (*.*)'
        )
        if not archivos:
            return
        self._xmls = []
        nombres = []
        for ruta in archivos:
            try:
                with open(ruta, 'r', encoding='utf-8', errors='replace') as f:
                    self._xmls.append(f.read())
                nombres.append(os.path.basename(ruta))
            except Exception as e:
                nombres.append(f'ERROR: {os.path.basename(ruta)} — {e}')

        self.lbl_conteo.setText(f'{len(self._xmls)} archivos seleccionados')
        self.txt_lista.setPlainText('\n'.join(nombres))
        self.btn_importar.setEnabled(len(self._xmls) > 0)
        self.txt_resultados.clear()

    def _importar(self):
        if not self._xmls:
            return
        self.btn_importar.setEnabled(False)
        self.btn_seleccionar.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.progress.setMaximum(len(self._xmls))
        self.txt_resultados.clear()

        payload = {
            'empresa_id': api.empresa_id(),
            'xmls': self._xmls,
        }

        self._worker = LoadWorker(api.post, '/api/compras/importar-xml', payload)
        self._worker.done.connect(self._on_resultado)
        self._worker.start()

    def _on_resultado(self, result):
        self.progress.setValue(self.progress.maximum())
        self.btn_importar.setEnabled(True)
        self.btn_seleccionar.setEnabled(True)

        if not result.get('ok'):
            self.txt_resultados.setPlainText(
                f'❌  Error: {result.get("error", "Error desconocido")}')
            return

        importados = result.get('importados', 0)
        errores = result.get('errores', 0)
        lineas = [
            f'✅  Importados: {importados}   ❌  Errores: {errores}',
            '─' * 50,
        ]
        for r in result.get('resultados', []):
            if r['ok']:
                lineas.append(
                    f'  ✓  {r["numero_documento"]}  |  {r["proveedor"]}  |  ${r["total"]:.2f}'
                )
            else:
                lineas.append(f'  ✗  {r.get("numero_documento", "?")}  →  {r["error"]}')

        self.txt_resultados.setPlainText('\n'.join(lineas))
        if importados > 0:
            self._imported = True


# ─── Pantalla principal ───────────────────────────────────────────────────────

class ComprasScreen(BaseScreen):

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        # Cabecera
        hdr = self._page_header(
            'Facturas de Proveedores',
            'Registra compras y retenciones recibidas'
        )
        lay.addWidget(hdr)

        # Toolbar
        toolbar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText('Buscar por proveedor o número...')
        self.txt_search.setFixedHeight(36)
        self.txt_search.returnPressed.connect(self._search)
        self.txt_search.textChanged.connect(self._on_search_change)

        btn_importar_xml = make_btn('📂 Importar XML', 'secondary')
        btn_importar_xml.setToolTip('Importar facturas desde archivos XML del SRI')
        btn_importar_xml.clicked.connect(self._importar_xml)

        btn_new = make_btn('+ Registrar Manual', 'primary')
        btn_new.clicked.connect(self._new)

        toolbar.addWidget(self.txt_search, 1)
        toolbar.addWidget(btn_importar_xml)
        toolbar.addWidget(btn_new)
        lay.addLayout(toolbar)

        # Tabla
        self.table = make_table([
            'Fecha', 'Tipo', 'Proveedor', 'N° Documento',
            'Subtotal', 'IVA', 'Total', 'Acciones'
        ])
        self.table.setColumnWidth(0, 95)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 240)
        self.table.setColumnWidth(3, 155)
        self.table.setColumnWidth(4, 85)
        self.table.setColumnWidth(5, 75)
        self.table.setColumnWidth(6, 85)
        lay.addWidget(self.table)

    def refresh(self):
        self._run(api.get, self._on_data, f'/api/compras/{api.empresa_id()}')

    def _search(self):
        q = self.txt_search.text().strip()
        self._run(api.get, self._on_data,
                  f'/api/compras/{api.empresa_id()}', params={'q': q})

    def _on_search_change(self, text):
        if not text:
            self.refresh()

    def _on_data(self, result):
        if not result.get('ok'):
            return
        self.table.setRowCount(0)

        TIPO_NOMBRES = {
            '01': 'Factura', '03': 'Liquidación',
            '04': 'N. Crédito', '05': 'N. Débito', '07': 'Retención',
        }

        for row in result['data']:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, table_item(row['fecha_emision']))
            tipo_nom = TIPO_NOMBRES.get(row.get('tipo_documento', '01'), row.get('tipo_documento', ''))
            self.table.setItem(r, 1, table_item(tipo_nom, center=True))
            self.table.setItem(r, 2, table_item(row['proveedor_nombre']))
            self.table.setItem(r, 3, table_item(row['numero_documento']))
            self.table.setItem(r, 4, table_item(
                f'${row.get("subtotal_sin_iva", row.get("subtotal", 0)):.2f}', center=True))
            self.table.setItem(r, 5, table_item(f'${row["iva"]:.2f}', center=True))
            self.table.setItem(r, 6, table_item(f'${row["total"]:.2f}', center=True))

            cell = QWidget()
            cl = QHBoxLayout(cell)
            cl.setContentsMargins(2, 2, 2, 2)
            cl.setSpacing(4)
            btn_e = make_btn('Editar', 'secondary')
            btn_e.setFixedHeight(26)
            btn_e.clicked.connect(lambda _, d=row: self._edit(d))
            btn_d = make_btn('Eliminar', 'danger')
            btn_d.setFixedHeight(26)
            btn_d.clicked.connect(lambda _, d=row: self._delete(d))
            cl.addWidget(btn_e)
            cl.addWidget(btn_d)
            self.table.setCellWidget(r, 7, cell)
            self.table.setRowHeight(r, 34)

    def _new(self):
        dlg = CompraDialog(self)
        if dlg.exec_() == dlg.Accepted:
            result = api.post('/api/compras/', dlg.get_data())
            if result.get('ok'):
                toast(self, 'Compra registrada correctamente', 'ok')
                self.refresh()
            else:
                toast(self, result.get('error', 'Error'), 'error')

    def _edit(self, data):
        dlg = CompraDialog(self, data)
        if dlg.exec_() == dlg.Accepted:
            result = api.put(f'/api/compras/{data["id"]}', dlg.get_data())
            if result.get('ok'):
                toast(self, 'Compra actualizada', 'ok')
                self.refresh()
            else:
                toast(self, result.get('error', 'Error'), 'error')

    def _delete(self, data):
        from PyQt5.QtWidgets import QMessageBox
        resp = QMessageBox.question(
            self, 'Confirmar',
            f'¿Eliminar compra N° {data["numero_documento"]}?',
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            api.delete(f'/api/compras/{data["id"]}')
            toast(self, 'Compra eliminada', 'ok')
            self.refresh()

    def _importar_xml(self):
        dlg = ImportarXmlDialog(self)
        dlg.exec_()
        if getattr(dlg, '_imported', False):
            toast(self, 'XMLs importados. Recargando lista...', 'ok')
            self.refresh()
