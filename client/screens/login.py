from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QApplication, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QColor
from .. import api, config as cfg
from ..theme import APP_STYLE, C


class LoginWorker(QThread):
    done = pyqtSignal(dict)

    def __init__(self, email, password):
        super().__init__()
        self.email = email
        self.password = password

    def run(self):
        self.done.emit(api.login(self.email, self.password))


class LoginScreen(QWidget):
    login_success = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(APP_STYLE + f'''
            QWidget {{ background: {C['bg_deep']}; }}
        ''')
        self.setMinimumSize(460, 560)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)
        outer.setContentsMargins(0, 0, 0, 0)

        # ── Card ──────────────────────────────────────────────
        card = QFrame()
        card.setFixedWidth(380)
        card.setStyleSheet(f'''
            QFrame {{
                background: {C['bg_card']};
                border: 1px solid {C['border']};
                border-radius: 12px;
            }}
        ''')
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(37, 46, 63, 60))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(36, 32, 36, 32)
        card_lay.setSpacing(0)

        # Logo block
        logo_row = QHBoxLayout()
        logo_icon = QLabel('⚡')
        logo_icon.setStyleSheet(f'font-size:28px; background:transparent; border:none;')
        logo_text = QLabel('FACTURADOR')
        logo_text.setStyleSheet(f'''
            color:{C['accent_h']}; font-size:20px; font-weight:700;
            letter-spacing:2px; background:transparent; border:none;
        ''')
        logo_row.addStretch()
        logo_row.addWidget(logo_icon)
        logo_row.addSpacing(8)
        logo_row.addWidget(logo_text)
        logo_row.addStretch()
        card_lay.addLayout(logo_row)

        card_lay.addSpacing(6)
        sub = QLabel('Sistema de Facturación Electrónica')
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f'color:{C["text_muted"]}; font-size:12px; background:transparent; border:none;')
        card_lay.addWidget(sub)

        card_lay.addSpacing(28)

        # Email
        lbl_email = QLabel('Correo electrónico')
        lbl_email.setStyleSheet(f'color:{C["text_muted"]}; font-size:12px; font-weight:600; background:transparent; border:none;')
        card_lay.addWidget(lbl_email)
        card_lay.addSpacing(4)
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText('usuario@empresa.com')
        self.txt_email.setFixedHeight(40)
        card_lay.addWidget(self.txt_email)

        card_lay.addSpacing(14)

        # Password
        lbl_pass = QLabel('Contraseña')
        lbl_pass.setStyleSheet(f'color:{C["text_muted"]}; font-size:12px; font-weight:600; background:transparent; border:none;')
        card_lay.addWidget(lbl_pass)
        card_lay.addSpacing(4)
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.setPlaceholderText('••••••••')
        self.txt_pass.setFixedHeight(40)
        self.txt_pass.returnPressed.connect(self._do_login)
        card_lay.addWidget(self.txt_pass)

        card_lay.addSpacing(20)

        # Login button
        self.btn_login = QPushButton('Ingresar al sistema')
        self.btn_login.setObjectName('primary')
        self.btn_login.setFixedHeight(42)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setStyleSheet(f'''
            QPushButton#primary {{
                background: {C['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
            QPushButton#primary:hover {{ background: {C['accent_h']}; }}
            QPushButton#primary:pressed {{ background: {C['accent_d']}; }}
            QPushButton#primary:disabled {{ background: {C['bg_hover']}; color: {C['text_dim']}; }}
        ''')
        self.btn_login.clicked.connect(self._do_login)
        card_lay.addWidget(self.btn_login)

        # Error
        self.lbl_error = QLabel('')
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setStyleSheet(f'color:{C["danger"]}; font-size:12px; background:transparent; border:none;')
        self.lbl_error.setFixedHeight(22)
        card_lay.addSpacing(8)
        card_lay.addWidget(self.lbl_error)

        # Server URL
        server_url = cfg.get('server_url', 'http://localhost:5000')
        lbl_server = QLabel(f'🖥  {server_url}')
        lbl_server.setAlignment(Qt.AlignCenter)
        lbl_server.setStyleSheet(f'color:{C["text_dim"]}; font-size:11px; background:transparent; border:none;')
        card_lay.addSpacing(12)
        card_lay.addWidget(lbl_server)

        outer.addWidget(card, alignment=Qt.AlignCenter)

    def _do_login(self):
        email = self.txt_email.text().strip()
        password = self.txt_pass.text()
        if not email or not password:
            self.lbl_error.setText('Ingrese correo y contraseña')
            return

        self.btn_login.setEnabled(False)
        self.btn_login.setText('Verificando...')
        self.lbl_error.setText('')

        self._worker = LoginWorker(email, password)
        self._worker.done.connect(self._on_done)
        self._worker.start()

    def _on_done(self, result):
        self.btn_login.setEnabled(True)
        self.btn_login.setText('Ingresar al sistema')
        if result.get('ok'):
            api.set_session(
                result.get('token', ''),
                result.get('usuario'),
                result.get('empresa'),
            )
            self.login_success.emit()
        else:
            self.lbl_error.setText(result.get('error', 'Credenciales incorrectas'))
