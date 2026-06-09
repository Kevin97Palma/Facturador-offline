from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy,
    QStatusBar, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from . import api
from .theme import APP_STYLE, C, SIDEBAR_STYLE

# (icon, key, label, section)
MENU = [
    ('🏠', 'dashboard',    'Inicio',                   'INICIO'),
    ('🧾', 'facturas',     'Facturas',                  'VENTAS'),
    ('🔖', 'retenciones',  'Retenciones',               None),
    ('📋', 'notas_credito','Notas de Crédito',           None),
    ('📌', 'notas_debito', 'Notas de Débito',            None),
    ('🚚', 'guias',        'Guías de Remisión',          None),
    ('🛒', 'liquidaciones','Liquidaciones de Compra',    None),
    ('👥', 'clientes',     'Clientes',                  'CATÁLOGOS'),
    ('🏭', 'proveedores',  'Proveedores',                None),
    ('📦', 'productos',    'Productos',                  None),
    ('🗂',  'categorias',  'Categorías',                 None),
    ('📥', 'compras',      'Facturas Proveedores',       'COMPRAS'),
    ('⚙',  'config',      'Configuración',             'SISTEMA'),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Facturador Electrónico')
        self.setMinimumSize(1150, 720)
        self.setStyleSheet(APP_STYLE)
        self._nav_buttons = {}
        self._setup_ui()
        self._load_screens()
        self._setup_statusbar()
        self._navigate('dashboard')

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._sidebar = self._build_sidebar()
        root.addWidget(self._sidebar)

        # Content area
        content_wrap = QWidget()
        content_wrap.setStyleSheet(f'background:{C["bg_base"]};')
        cw_lay = QVBoxLayout(content_wrap)
        cw_lay.setContentsMargins(0, 0, 0, 0)
        cw_lay.setSpacing(0)

        self._stack = QStackedWidget()
        cw_lay.addWidget(self._stack)

        root.addWidget(content_wrap)
        root.setStretchFactor(content_wrap, 1)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(APP_STYLE + SIDEBAR_STYLE)

        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Logo header ─────────────────────────────────────
        header = QWidget()
        header.setStyleSheet(f'background:{C["bg_deep"]}; border-bottom: 1px solid {C["border"]};')
        h_lay = QVBoxLayout(header)
        h_lay.setContentsMargins(14, 16, 14, 14)

        logo_row = QHBoxLayout()
        logo_icon = QLabel('⚡')
        logo_icon.setStyleSheet(f'font-size:18px; background:transparent; border:none;')
        logo_name = QLabel('FACTURADOR')
        logo_name.setObjectName('logo_text')
        logo_row.addWidget(logo_icon)
        logo_row.addWidget(logo_name)
        logo_row.addStretch()
        h_lay.addLayout(logo_row)

        empresa = api.get_empresa() or {}
        user = api.get_user() or {}

        self.lbl_company = QLabel(empresa.get('razon_social', '')[:28])
        self.lbl_company.setObjectName('company_name')
        self.lbl_company.setWordWrap(True)
        h_lay.addSpacing(8)
        h_lay.addWidget(self.lbl_company)

        self.lbl_user = QLabel(f"👤  {user.get('nombre', user.get('email', ''))}")
        self.lbl_user.setObjectName('user_label')
        h_lay.addWidget(self.lbl_user)

        # Ambiente badge
        amb = empresa.get('ambiente', '1')
        amb_txt = '⚡ PRODUCCIÓN' if amb == '2' else '🧪 PRUEBAS'
        amb_color = C['accent'] if amb == '2' else C['warning']
        lbl_amb = QLabel(amb_txt)
        lbl_amb.setStyleSheet(f'color:{amb_color}; font-size:11px; font-weight:700; background:transparent; border:none; padding:0 14px 4px;')
        h_lay.addWidget(lbl_amb)

        lay.addWidget(header)

        # ── Nav items ─────────────────────────────────────────
        nav_scroll = QWidget()
        nav_lay = QVBoxLayout(nav_scroll)
        nav_lay.setContentsMargins(0, 8, 0, 8)
        nav_lay.setSpacing(0)

        last_section = None
        for icon, key, label, section in MENU:
            if section and section != last_section:
                sep_lbl = QLabel(section)
                sep_lbl.setObjectName('section_sep')
                nav_lay.addWidget(sep_lbl)
                last_section = section

            btn = QPushButton(f'  {icon}  {label}')
            btn.setObjectName('nav_btn')
            btn.setCheckable(True)
            btn.setFixedHeight(36)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._navigate(k))
            self._nav_buttons[key] = btn
            nav_lay.addWidget(btn)

        nav_lay.addStretch()
        lay.addWidget(nav_scroll, 1)

        # ── Footer ───────────────────────────────────────────
        footer = QWidget()
        footer.setStyleSheet(f'background:{C["bg_deep"]}; border-top: 1px solid {C["border"]};')
        f_lay = QVBoxLayout(footer)
        f_lay.setContentsMargins(0, 6, 0, 6)

        btn_logout = QPushButton('  🚪  Cerrar sesión')
        btn_logout.setObjectName('logout_btn')
        btn_logout.setFixedHeight(36)
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.clicked.connect(self._logout)
        f_lay.addWidget(btn_logout)

        lbl_ver = QLabel('v1.0.0  ·  SRI Ecuador')
        lbl_ver.setAlignment(Qt.AlignCenter)
        lbl_ver.setStyleSheet(f'color:{C["text_dim"]}; font-size:10px; background:transparent; border:none; padding-bottom:4px;')
        f_lay.addWidget(lbl_ver)

        lay.addWidget(footer)
        return sidebar

    def _load_screens(self):
        from .screens.dashboard import DashboardScreen
        from .screens.facturas import FacturasScreen
        from .screens.retenciones import RetencionesScreen
        from .screens.notas_credito import NotasCreditoScreen
        from .screens.notas_debito import NotasDebitoScreen
        from .screens.guias import GuiasScreen
        from .screens.liquidaciones import LiquidacionesScreen
        from .screens.clientes import ClientesScreen
        from .screens.proveedores import ProveedoresScreen
        from .screens.productos import ProductosScreen
        from .screens.categorias import CategoriasScreen
        from .screens.compras import ComprasScreen
        from .screens.configuracion import ConfiguracionScreen

        self._screens = {
            'dashboard':    DashboardScreen(),
            'facturas':     FacturasScreen(),
            'retenciones':  RetencionesScreen(),
            'notas_credito': NotasCreditoScreen(),
            'notas_debito': NotasDebitoScreen(),
            'guias':        GuiasScreen(),
            'liquidaciones': LiquidacionesScreen(),
            'clientes':     ClientesScreen(),
            'proveedores':  ProveedoresScreen(),
            'productos':    ProductosScreen(),
            'categorias':   CategoriasScreen(),
            'compras':      ComprasScreen(),
            'config':       ConfiguracionScreen(),
        }
        for screen in self._screens.values():
            self._stack.addWidget(screen)

    def _setup_statusbar(self):
        sb = self.statusBar()
        self.lbl_status = QLabel('● Conectado')
        self.lbl_status.setStyleSheet(f'color:{C["accent"]}; font-size:11px; padding:0 8px;')
        sb.addWidget(self.lbl_status)

        self.lbl_empresa_status = QLabel()
        empresa = api.get_empresa() or {}
        self.lbl_empresa_status.setText(
            f'{empresa.get("ruc", "")}  ·  {empresa.get("establecimiento", "001")}-{empresa.get("punto_emision", "001")}'
        )
        self.lbl_empresa_status.setStyleSheet(f'color:{C["text_muted"]}; font-size:11px; padding:0 8px;')
        sb.addPermanentWidget(self.lbl_empresa_status)

    def _navigate(self, key):
        for k, btn in self._nav_buttons.items():
            btn.setChecked(k == key)
        screen = self._screens.get(key)
        if screen:
            self._stack.setCurrentWidget(screen)
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _logout(self):
        from .screens.login import LoginScreen
        from PyQt5.QtWidgets import QApplication
        api.clear_session()
        self.close()
        self._login_win = LoginScreen()
        self._login_win.setWindowTitle('Facturador — Iniciar sesión')
        self._login_win.resize(460, 560)
        self._login_win.login_success.connect(self._on_relogin)
        self._login_win.show()

    def _on_relogin(self):
        self._login_win.close()
        new_win = MainWindow()
        new_win.show()
        QApplication.instance()._main_window = new_win
