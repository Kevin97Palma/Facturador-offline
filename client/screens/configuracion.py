from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QFrame, QTabWidget, QWidget, QFormLayout,
    QFileDialog, QMessageBox, QSpinBox, QGroupBox
)
from PyQt5.QtCore import Qt
from ..widgets import BaseScreen, make_btn, toast, LoadWorker
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

        # ── Tab: Nube / Backup MySQL ──────────────────────────────────────────
        tab_cloud = QWidget()
        f_cloud = QVBoxLayout(tab_cloud)
        f_cloud.setSpacing(14)
        f_cloud.setContentsMargins(16, 16, 16, 16)

        # Conexión MySQL
        grp_mysql = QGroupBox('Conexión MySQL en la Nube')
        fm = QFormLayout(grp_mysql)
        fm.setSpacing(10)

        self.txt_mysql_host = QLineEdit(cfg.get('mysql_host', ''))
        self.txt_mysql_host.setPlaceholderText('db.miservidor.com  ó  192.168.1.200')

        self.spn_mysql_port = QSpinBox()
        self.spn_mysql_port.setRange(1, 65535)
        self.spn_mysql_port.setValue(int(cfg.get('mysql_port', 3306)))

        self.txt_mysql_user = QLineEdit(cfg.get('mysql_user', ''))
        self.txt_mysql_user.setPlaceholderText('facturador_app')

        self.txt_mysql_pass = QLineEdit(cfg.get('mysql_password', ''))
        self.txt_mysql_pass.setEchoMode(QLineEdit.Password)
        self.txt_mysql_pass.setPlaceholderText('Contraseña MySQL')

        self.txt_mysql_db = QLineEdit(cfg.get('mysql_database', 'facturador_cloud'))
        self.txt_mysql_db.setPlaceholderText('facturador_cloud')

        self.spn_hora_backup = QSpinBox()
        self.spn_hora_backup.setRange(0, 23)
        self.spn_hora_backup.setValue(int(cfg.get('hora_backup', 2)))
        self.spn_hora_backup.setSuffix(':00 hrs')

        fm.addRow('Host MySQL:', self.txt_mysql_host)
        fm.addRow('Puerto:', self.spn_mysql_port)
        fm.addRow('Usuario:', self.txt_mysql_user)
        fm.addRow('Contraseña:', self.txt_mysql_pass)
        fm.addRow('Base de datos:', self.txt_mysql_db)
        fm.addRow('Hora backup diario:', self.spn_hora_backup)
        f_cloud.addWidget(grp_mysql)

        # Acciones
        btn_row = QHBoxLayout()
        btn_test_mysql = make_btn('🔌 Probar Conexión', 'secondary')
        btn_test_mysql.clicked.connect(self._test_mysql)
        btn_backup_now = make_btn('☁  Respaldar Ahora', 'secondary')
        btn_backup_now.clicked.connect(self._backup_now)
        btn_save_mysql = make_btn('Guardar Config. Nube', 'primary')
        btn_save_mysql.clicked.connect(self._save_mysql)
        btn_row.addWidget(btn_test_mysql)
        btn_row.addWidget(btn_backup_now)
        btn_row.addWidget(btn_save_mysql)
        btn_row.addStretch()
        f_cloud.addLayout(btn_row)

        # Estado del backup
        grp_estado = QGroupBox('Estado del Backup')
        fe = QFormLayout(grp_estado)
        fe.setSpacing(8)
        self.lbl_backup_estado = QLabel('Consultando...')
        self.lbl_backup_ultima = QLabel('—')
        self.lbl_backup_registros = QLabel('—')
        self.lbl_licencia = QLabel('—')
        fe.addRow('Último resultado:', self.lbl_backup_estado)
        fe.addRow('Última vez:', self.lbl_backup_ultima)
        fe.addRow('Registros respaldados:', self.lbl_backup_registros)
        fe.addRow('Licencia:', self.lbl_licencia)
        f_cloud.addWidget(grp_estado)
        f_cloud.addStretch()

        tabs.addTab(tab_cloud, '☁ Nube')

        # ─────────────────────────────────────────────────────────────────────
        lay.addWidget(tabs)

        btn_save = make_btn('Guardar Configuración Local', 'primary')
        btn_save.clicked.connect(self._save)
        lay.addWidget(btn_save, alignment=Qt.AlignLeft)

        self._on_printer_type_change()
        self._cargar_estado_cloud()

    def _on_printer_type_change(self):
        pt = self.cmb_printer_type.currentData()
        self.txt_printer_name.setEnabled(pt == 'windows')
        self.txt_printer_ip.setEnabled(pt == 'escpos_network')
        self.spn_printer_port.setEnabled(pt == 'escpos_network')

    def _test_connection(self):
        url = self.txt_server_url.text().strip()
        try:
            import requests
            requests.get(f'{url}/api/auth/empresas', timeout=5)
            self.lbl_conn_status.setText('Conectado correctamente')
            self.lbl_conn_status.setStyleSheet('color: #2ea043;')
        except Exception as e:
            self.lbl_conn_status.setText(f'Error: {e}')
            self.lbl_conn_status.setStyleSheet('color: #da3633;')

    def _test_print(self):
        from ..printer import imprimir_prueba
        try:
            imprimir_prueba()
            toast(self, 'Impresión de prueba enviada', 'ok')
        except Exception as e:
            toast(self, f'Error de impresión: {e}', 'error')

    def _save(self):
        c = cfg.load_config()
        c['server_url'] = self.txt_server_url.text().strip()
        c['mode'] = self.cmb_mode.currentData()
        c['printer_type'] = self.cmb_printer_type.currentData()
        c['printer_name'] = self.txt_printer_name.text().strip()
        c['printer_ip'] = self.txt_printer_ip.text().strip()
        c['printer_port'] = self.spn_printer_port.value()
        cfg.save_config(c)
        toast(self, 'Configuración guardada. Reinicie para aplicar cambios de URL.', 'ok')

    # ── Cloud / MySQL ─────────────────────────────────────────────────────────

    def _get_mysql_payload(self):
        return {
            'mysql_host':     self.txt_mysql_host.text().strip(),
            'mysql_port':     self.spn_mysql_port.value(),
            'mysql_user':     self.txt_mysql_user.text().strip(),
            'mysql_password': self.txt_mysql_pass.text().strip(),
            'mysql_database': self.txt_mysql_db.text().strip(),
            'hora_backup':    self.spn_hora_backup.value(),
        }

    def _test_mysql(self):
        payload = self._get_mysql_payload()
        if not payload['mysql_host']:
            toast(self, 'Ingrese el host MySQL', 'warning')
            return

        def _do():
            return api.post('/api/cloud/config', payload)

        worker = LoadWorker(_do)
        worker.done.connect(lambda r: (
            toast(self, r.get('mensaje', 'Conexión exitosa'), 'ok')
            if r.get('ok')
            else toast(self, r.get('error', 'Error'), 'error')
        ))
        worker.start()

    def _save_mysql(self):
        payload = self._get_mysql_payload()
        if not payload['mysql_host']:
            toast(self, 'Ingrese el host MySQL', 'warning')
            return

        def _do():
            return api.post('/api/cloud/config', payload)

        worker = LoadWorker(_do)
        worker.done.connect(self._on_mysql_saved)
        worker.start()

    def _on_mysql_saved(self, result):
        if result.get('ok'):
            # Guardar también en config.json local para el cliente
            c = cfg.load_config()
            c.update({
                'mysql_host':     self.txt_mysql_host.text().strip(),
                'mysql_port':     self.spn_mysql_port.value(),
                'mysql_user':     self.txt_mysql_user.text().strip(),
                'mysql_password': self.txt_mysql_pass.text().strip(),
                'mysql_database': self.txt_mysql_db.text().strip(),
                'hora_backup':    self.spn_hora_backup.value(),
            })
            cfg.save_config(c)
            toast(self, 'Configuración MySQL guardada correctamente', 'ok')
            self._cargar_estado_cloud()
        else:
            toast(self, result.get('error', 'Error al guardar'), 'error')

    def _backup_now(self):
        toast(self, 'Iniciando backup...', 'info')

        def _do():
            return api.post('/api/cloud/backup/ejecutar', {})

        worker = LoadWorker(_do)
        worker.done.connect(lambda r: (
            toast(self,
                  f'Backup completo: {r.get("registros", 0)} registros', 'ok')
            if r.get('ok')
            else toast(self, r.get('error', 'Error en backup'), 'error')
        ))
        worker.start()

    def _cargar_estado_cloud(self):
        def _do():
            return api.get('/api/cloud/backup/estado')

        worker = LoadWorker(_do)
        worker.done.connect(self._on_estado_cloud)
        worker.start()

        empresa = api.get_empresa()
        if empresa and empresa.get('ruc'):
            def _lic():
                return api.get(f'/api/cloud/licencia/{empresa["ruc"]}')
            wl = LoadWorker(_lic)
            wl.done.connect(self._on_licencia)
            wl.start()

    def _on_estado_cloud(self, result):
        if not result.get('ok'):
            self.lbl_backup_estado.setText('No configurado')
            return
        ult = result.get('ultimo_backup') or {}
        ok = ult.get('ok')
        if ok is None:
            self.lbl_backup_estado.setText('Sin backup ejecutado aún')
        elif ok:
            self.lbl_backup_estado.setText('✅ OK')
            self.lbl_backup_estado.setStyleSheet('color: #2ea043;')
        else:
            self.lbl_backup_estado.setText(f'❌ {ult.get("error", "Error")}')
            self.lbl_backup_estado.setStyleSheet('color: #da3633;')
        self.lbl_backup_ultima.setText(ult.get('ultima_vez') or '—')
        self.lbl_backup_registros.setText(str(ult.get('registros', '—')))

    def _on_licencia(self, result):
        if not result.get('ok'):
            self.lbl_licencia.setText('Sin información')
            return
        valida = result.get('valida', False)
        plan = result.get('plan', '—')
        venc = result.get('fecha_vencimiento', '')
        modo = result.get('modo', '')
        if valida:
            texto = f'✅ {plan.upper()} — vence {venc} ({modo})'
            self.lbl_licencia.setStyleSheet('color: #2ea043;')
        else:
            texto = f'❌ {result.get("mensaje", "Sin licencia")}'
            self.lbl_licencia.setStyleSheet('color: #da3633;')
        self.lbl_licencia.setText(texto)

    def refresh(self):
        self._cargar_estado_cloud()
