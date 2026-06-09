from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QFrame, QTabWidget, QWidget, QFormLayout,
    QFileDialog, QMessageBox, QSpinBox
)
from PyQt5.QtCore import Qt
from ..widgets import BaseScreen, make_btn, show_info, show_error, SCREEN_STYLE
from .. import api, config as cfg


class ConfiguracionScreen(BaseScreen):
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        title = QLabel('Configuración')
        title.setObjectName('page_title')
        lay.addWidget(title)

        tabs = QTabWidget()

        # Tab: Conexión
        tab_conn = QWidget()
        f_conn = QFormLayout(tab_conn)
        f_conn.setSpacing(12)

        self.txt_server_url = QLineEdit(cfg.get('server_url', 'http://localhost:5000'))
        self.txt_server_url.setPlaceholderText('http://192.168.1.100:5000')

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItem('Servidor (ejecuta base de datos)', 'servidor')
        self.cmb_mode.addItem('Cliente (se conecta al servidor)', 'cliente')
        mode = cfg.get('mode', 'servidor')
        self.cmb_mode.setCurrentIndex(0 if mode == 'servidor' else 1)

        btn_test = make_btn('Probar conexión', 'secondary')
        btn_test.clicked.connect(self._test_connection)

        f_conn.addRow('URL del Servidor:', self.txt_server_url)
        f_conn.addRow('Modo de este equipo:', self.cmb_mode)
        f_conn.addRow('', btn_test)
        self.lbl_conn_status = QLabel('')
        f_conn.addRow('Estado:', self.lbl_conn_status)
        tabs.addTab(tab_conn, 'Conexión')

        # Tab: Impresora
        tab_print = QWidget()
        f_print = QFormLayout(tab_print)
        f_print.setSpacing(12)

        self.cmb_printer_type = QComboBox()
        self.cmb_printer_type.addItem('Sin impresora de tickets', 'none')
        self.cmb_printer_type.addItem('ESC/POS USB', 'escpos_usb')
        self.cmb_printer_type.addItem('ESC/POS Red (TCP)', 'escpos_network')
        self.cmb_printer_type.addItem('Impresora Windows', 'windows')
        pt = cfg.get('printer_type', 'none')
        idx = {'none': 0, 'escpos_usb': 1, 'escpos_network': 2, 'windows': 3}.get(pt, 0)
        self.cmb_printer_type.setCurrentIndex(idx)
        self.cmb_printer_type.currentIndexChanged.connect(self._on_printer_type_change)

        self.txt_printer_name = QLineEdit(cfg.get('printer_name', ''))
        self.txt_printer_name.setPlaceholderText('Nombre de la impresora Windows')

        self.txt_printer_ip = QLineEdit(cfg.get('printer_ip', ''))
        self.txt_printer_ip.setPlaceholderText('192.168.1.50')

        self.spn_printer_port = QSpinBox()
        self.spn_printer_port.setRange(1, 65535)
        self.spn_printer_port.setValue(int(cfg.get('printer_port', 9100)))

        f_print.addRow('Tipo de impresora:', self.cmb_printer_type)
        f_print.addRow('Nombre (Windows):', self.txt_printer_name)
        f_print.addRow('IP (red TCP):', self.txt_printer_ip)
        f_print.addRow('Puerto:', self.spn_printer_port)

        btn_test_print = make_btn('Imprimir prueba', 'secondary')
        btn_test_print.clicked.connect(self._test_print)
        f_print.addRow('', btn_test_print)
        tabs.addTab(tab_print, 'Impresora Tickets')

        # Tab: Empresa
        tab_empresa = QWidget()
        f_emp = QVBoxLayout(tab_empresa)
        f_emp.setSpacing(10)

        empresa = api.get_empresa() or {}
        lbl_e = QLabel(f'RUC: {empresa.get("ruc", "")}')
        lbl_rs = QLabel(f'Razón Social: {empresa.get("razon_social", "")}')
        lbl_fe = QLabel(f'URL Firma/SRI: {empresa.get("fe_url", "No configurada")}')
        lbl_pdf = QLabel(f'URL PDF: {empresa.get("pdf_url", "No configurada")}')
        lbl_amb = QLabel(f'Ambiente: {"PRODUCCIÓN" if empresa.get("ambiente") == "2" else "PRUEBAS"}')
        for lbl in [lbl_e, lbl_rs, lbl_fe, lbl_pdf, lbl_amb]:
            lbl.setStyleSheet('font-size: 13px; padding: 4px 0;')
            f_emp.addWidget(lbl)

        f_emp.addStretch()
        tabs.addTab(tab_empresa, 'Empresa')

        lay.addWidget(tabs)

        btn_save = make_btn('Guardar Configuración', 'primary')
        btn_save.clicked.connect(self._save)
        lay.addWidget(btn_save, alignment=Qt.AlignLeft)

        self._on_printer_type_change()

    def _on_printer_type_change(self):
        pt = self.cmb_printer_type.currentData()
        self.txt_printer_name.setEnabled(pt == 'windows')
        self.txt_printer_ip.setEnabled(pt == 'escpos_network')
        self.spn_printer_port.setEnabled(pt == 'escpos_network')

    def _test_connection(self):
        url = self.txt_server_url.text().strip()
        try:
            import requests
            r = requests.get(f'{url}/api/auth/empresas', timeout=5)
            self.lbl_conn_status.setText('Conectado correctamente')
            self.lbl_conn_status.setStyleSheet('color: #2ecc71;')
        except Exception as e:
            self.lbl_conn_status.setText(f'Error: {e}')
            self.lbl_conn_status.setStyleSheet('color: #e94560;')

    def _test_print(self):
        from ..printer import imprimir_prueba
        try:
            imprimir_prueba()
            show_info(self, 'Impresión de prueba enviada')
        except Exception as e:
            show_error(self, f'Error de impresión: {e}')

    def _save(self):
        c = cfg.load_config()
        c['server_url'] = self.txt_server_url.text().strip()
        c['mode'] = self.cmb_mode.currentData()
        c['printer_type'] = self.cmb_printer_type.currentData()
        c['printer_name'] = self.txt_printer_name.text().strip()
        c['printer_ip'] = self.txt_printer_ip.text().strip()
        c['printer_port'] = self.spn_printer_port.value()
        cfg.save_config(c)
        show_info(self, 'Configuración guardada.\nReinicie la aplicación para aplicar cambios de URL.')

    def refresh(self):
        pass
