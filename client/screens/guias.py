from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialog, QFormLayout,
    QDialogButtonBox, QDoubleSpinBox, QDateEdit, QWidget,
    QAbstractItemView, QTableWidget, QTableWidgetItem, QFileDialog, QTabWidget
)
from PyQt5.QtCore import QDate
from ..widgets import (BaseScreen, make_btn, make_table, table_item,
                       set_estado_item, show_error, show_info, confirm, SCREEN_STYLE, LoadWorker)
from .. import api


class GuiaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Nueva Guía de Remisión')
        self.setMinimumSize(820, 600)
        self.setStyleSheet(SCREEN_STYLE)
        self._destinatarios = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)

        tabs = QTabWidget()

        # Tab 1: Header
        tab1 = QWidget()
        f1 = QFormLayout(tab1)
        f1.setSpacing(10)
        self.txt_ruc_transp = QLineEdit()
        self.txt_rs_transp = QLineEdit()
        self.txt_placa = QLineEdit()
        self.txt_fecha_ini = QDateEdit(QDate.currentDate())
        self.txt_fecha_ini.setCalendarPopup(True)
        self.txt_fecha_ini.setDisplayFormat('yyyy-MM-dd')
        self.txt_fecha_fin = QDateEdit(QDate.currentDate())
        self.txt_fecha_fin.setCalendarPopup(True)
        self.txt_fecha_fin.setDisplayFormat('yyyy-MM-dd')
        f1.addRow('RUC Transportista *:', self.txt_ruc_transp)
        f1.addRow('Razón Social Transportista *:', self.txt_rs_transp)
        f1.addRow('Placa:', self.txt_placa)
        f1.addRow('Fecha Inicio Transporte:', self.txt_fecha_ini)
        f1.addRow('Fecha Fin Transporte:', self.txt_fecha_fin)
        tabs.addTab(tab1, 'Transporte')

        # Tab 2: Destinatarios
        tab2 = QWidget()
        t2_lay = QVBoxLayout(tab2)

        dest_entry = QHBoxLayout()
        self.txt_id_dest = QLineEdit()
        self.txt_id_dest.setPlaceholderText('RUC/Cédula')
        self.txt_id_dest.setFixedWidth(130)
        self.txt_rs_dest = QLineEdit()
        self.txt_rs_dest.setPlaceholderText('Razón Social')
        self.txt_dir_dest = QLineEdit()
        self.txt_dir_dest.setPlaceholderText('Dirección')
        self.txt_motivo = QLineEdit()
        self.txt_motivo.setPlaceholderText('Motivo traslado')
        self.txt_num_doc_sust = QLineEdit()
        self.txt_num_doc_sust.setPlaceholderText('N° Doc Sustento')
        self.txt_num_doc_sust.setFixedWidth(150)
        btn_add_dest = make_btn('+ Destinatario', 'primary')
        btn_add_dest.clicked.connect(self._add_destinatario)
        dest_entry.addWidget(self.txt_id_dest)
        dest_entry.addWidget(self.txt_rs_dest)
        dest_entry.addWidget(self.txt_dir_dest)
        dest_entry.addWidget(self.txt_motivo)
        dest_entry.addWidget(self.txt_num_doc_sust)
        dest_entry.addWidget(btn_add_dest)
        t2_lay.addLayout(dest_entry)

        self.tbl_dest = QTableWidget(0, 5)
        self.tbl_dest.setHorizontalHeaderLabels(['Identificación', 'Razón Social', 'Dirección', 'Motivo', 'N° Doc'])
        self.tbl_dest.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_dest.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_dest.verticalHeader().setVisible(False)
        self.tbl_dest.horizontalHeader().setStretchLastSection(True)
        t2_lay.addWidget(self.tbl_dest)

        # Detalles del destinatario seleccionado
        lbl_dets = QLabel('Detalles del destinatario seleccionado:')
        lbl_dets.setObjectName('section_title')
        t2_lay.addWidget(lbl_dets)

        det_entry = QHBoxLayout()
        self.txt_cod_prod = QLineEdit()
        self.txt_cod_prod.setPlaceholderText('Código')
        self.txt_cod_prod.setFixedWidth(120)
        self.txt_desc_prod = QLineEdit()
        self.txt_desc_prod.setPlaceholderText('Descripción')
        self.spn_cant = QDoubleSpinBox()
        self.spn_cant.setRange(0.01, 99999)
        self.spn_cant.setValue(1)
        self.spn_cant.setFixedWidth(90)
        btn_add_det = make_btn('+ Detalle', 'secondary')
        btn_add_det.clicked.connect(self._add_detalle)
        det_entry.addWidget(QLabel('Cód.:'))
        det_entry.addWidget(self.txt_cod_prod)
        det_entry.addWidget(QLabel('Desc.:'))
        det_entry.addWidget(self.txt_desc_prod)
        det_entry.addWidget(QLabel('Cant.:'))
        det_entry.addWidget(self.spn_cant)
        det_entry.addWidget(btn_add_det)
        t2_lay.addLayout(det_entry)

        self.tbl_dets = QTableWidget(0, 3)
        self.tbl_dets.setHorizontalHeaderLabels(['Código', 'Descripción', 'Cantidad'])
        self.tbl_dets.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_dets.verticalHeader().setVisible(False)
        self.tbl_dets.horizontalHeader().setStretchLastSection(True)
        self.tbl_dets.setFixedHeight(120)
        t2_lay.addWidget(self.tbl_dets)
        tabs.addTab(tab2, 'Destinatarios')

        lay.addWidget(tabs)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText('Guardar Guía')
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _add_destinatario(self):
        identi = self.txt_id_dest.text().strip()
        rs = self.txt_rs_dest.text().strip()
        if not identi or not rs:
            show_error(self, 'Identificación y Razón Social son requeridos')
            return
        dest = {
            'identificacion_destinatario': identi,
            'razon_social_destinatario': rs,
            'direccion_destinatario': self.txt_dir_dest.text().strip(),
            'motivo_traslado': self.txt_motivo.text().strip(),
            'num_doc_sustento': self.txt_num_doc_sust.text().strip(),
            'doc_aduanero_unico': '',
            'detalles': [],
        }
        self._destinatarios.append(dest)
        r = self.tbl_dest.rowCount()
        self.tbl_dest.insertRow(r)
        self.tbl_dest.setItem(r, 0, QTableWidgetItem(identi))
        self.tbl_dest.setItem(r, 1, QTableWidgetItem(rs))
        self.tbl_dest.setItem(r, 2, QTableWidgetItem(dest['direccion_destinatario']))
        self.tbl_dest.setItem(r, 3, QTableWidgetItem(dest['motivo_traslado']))
        self.tbl_dest.setItem(r, 4, QTableWidgetItem(dest['num_doc_sustento']))
        self.txt_id_dest.clear()
        self.txt_rs_dest.clear()

    def _add_detalle(self):
        row = self.tbl_dest.currentRow()
        if row < 0:
            show_error(self, 'Seleccione un destinatario primero')
            return
        desc = self.txt_desc_prod.text().strip()
        if not desc:
            return
        det = {
            'codigo_interno': self.txt_cod_prod.text().strip(),
            'descripcion': desc,
            'cantidad': self.spn_cant.value(),
        }
        self._destinatarios[row]['detalles'].append(det)
        r = self.tbl_dets.rowCount()
        self.tbl_dets.insertRow(r)
        self.tbl_dets.setItem(r, 0, QTableWidgetItem(det['codigo_interno']))
        self.tbl_dets.setItem(r, 1, QTableWidgetItem(desc))
        self.tbl_dets.setItem(r, 2, QTableWidgetItem(f'{det["cantidad"]:.2f}'))
        self.txt_cod_prod.clear()
        self.txt_desc_prod.clear()

    def _validate(self):
        if not self.txt_ruc_transp.text().strip():
            show_error(self, 'Ingrese el RUC del transportista')
            return
        if not self._destinatarios:
            show_error(self, 'Agregue al menos un destinatario')
            return
        self.accept()

    def get_data(self):
        return {
            'empresa_id': api.empresa_id(), 'usuario_id': api.usuario_id(),
            'ruc_transportista': self.txt_ruc_transp.text().strip(),
            'razon_social_transportista': self.txt_rs_transp.text().strip(),
            'placa': self.txt_placa.text().strip(),
            'fecha_ini_transporte': self.txt_fecha_ini.date().toString('yyyy-MM-dd'),
            'fecha_fin_transporte': self.txt_fecha_fin.date().toString('yyyy-MM-dd'),
            'destinatarios': self._destinatarios,
        }


class GuiasScreen(BaseScreen):
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        title = QLabel('Guías de Remisión')
        title.setObjectName('page_title')
        lay.addWidget(title)

        toolbar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText('Buscar por transportista...')
        self.txt_search.setFixedHeight(36)
        btn_new = make_btn('+ Nueva Guía', 'primary')
        btn_new.clicked.connect(self._new)
        toolbar.addWidget(self.txt_search)
        toolbar.addWidget(btn_new)
        lay.addLayout(toolbar)

        self.table = make_table(['#', 'Fecha Ini', 'Transportista', 'Placa', 'Estado', 'Acciones'])
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 280)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 100)
        lay.addWidget(self.table)

    def refresh(self):
        self._run(api.get, self._on_data, f'/api/guias/{api.empresa_id()}')

    def _on_data(self, result):
        if not result.get('ok'):
            return
        self.table.setRowCount(0)
        for row in result['data']:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, table_item(row['numero_formateado']))
            self.table.setItem(r, 1, table_item(row['fecha_ini_transporte']))
            self.table.setItem(r, 2, table_item(row['razon_social_transportista']))
            self.table.setItem(r, 3, table_item(row['placa']))
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
        dlg = GuiaDialog(self)
        if dlg.exec_() == dlg.Accepted:
            result = api.post('/api/guias/', dlg.get_data())
            if result.get('ok') and confirm(self, '¿Autorizar ahora?'):
                self._autorizar_id(result['data']['id'])
            elif result.get('ok'):
                self.refresh()
            else:
                show_error(self, result.get('error', 'Error'))

    def _autorizar_id(self, gid):
        def do():
            return api.post(f'/api/guias/{gid}/autorizar')
        w = LoadWorker(do)
        w.done.connect(lambda r: (show_info(self, 'Autorizada') if r.get('ok') else show_error(self, r.get('error', '')), self.refresh()))
        w.start()
        self._workers.append(w)

    def _pdf(self, data):
        content, err = api.download(f'/api/guias/{data["id"]}/pdf')
        if err:
            show_error(self, err)
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Guardar PDF', f'GR_{data["clave_acceso"]}.pdf', 'PDF (*.pdf)')
        if path:
            with open(path, 'wb') as f:
                f.write(content)
