"""Central design system for the Facturador desktop app.

Identidad visual Socket Studio (socket-studio.com):
- Rojo coral #db4d4f como color primario de marca
- Azul marino #252e3f para sidebar y textos
- Base clara y limpia con acentos vivos
"""

# ── Colour palette ────────────────────────────────────────────────────────────
C = {
    # Backgrounds (tema claro)
    'bg_deep':    '#f0f2f5',
    'bg_base':    '#f7f8fa',
    'bg_card':    '#ffffff',
    'bg_panel':   '#f1f3f6',
    'bg_hover':   '#e9edf2',
    'bg_active':  '#fdeaea',

    # Brand Socket Studio
    'accent':     '#db4d4f',
    'accent_h':   '#e66365',
    'accent_d':   '#c43a3c',
    'navy':       '#252e3f',
    'navy_2':     '#2b3e4d',
    'success':    '#27ae60',
    'danger':     '#d93025',
    'danger_h':   '#f05545',
    'warning':    '#e8a13c',
    'info':       '#2b6cb0',

    # Text
    'text':       '#252e3f',
    'text_muted': '#6b7686',
    'text_dim':   '#9aa4b2',

    # Border
    'border':     '#e2e6eb',
    'border_h':   '#c9ced6',
}

# ── Font sizes ────────────────────────────────────────────────────────────────
F = {
    'xs':   '11px',
    'sm':   '12px',
    'base': '13px',
    'md':   '14px',
    'lg':   '16px',
    'xl':   '20px',
    'h1':   '24px',
}

# ── Full app stylesheet ───────────────────────────────────────────────────────
APP_STYLE = f"""
/* ── Global ── */
QWidget {{
    background: {C['bg_base']};
    color: {C['text']};
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: {F['base']};
}}
QMainWindow, QDialog {{
    background: {C['bg_base']};
}}

/* ── Inputs ── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 7px 10px;
    color: {C['text']};
    selection-background-color: {C['accent']};
    selection-color: #ffffff;
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 2px solid {C['accent']};
    background: #ffffff;
}}
QLineEdit:disabled {{
    background: {C['bg_panel']};
    color: {C['text_dim']};
}}

/* ── Combo / Spin ── */
QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    background: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 6px 10px;
    color: {C['text']};
    min-height: 28px;
}}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
    border: 2px solid {C['accent']};
}}
QComboBox QAbstractItemView {{
    background: #ffffff;
    border: 1px solid {C['border']};
    color: {C['text']};
    selection-background-color: {C['bg_active']};
    selection-color: {C['accent_d']};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: {C['bg_panel']};
    border: none;
    width: 18px;
}}

/* ── Buttons – primary (rojo Socket) ── */
QPushButton#primary {{
    background: {C['accent']};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 700;
    font-size: {F['base']};
    min-height: 32px;
}}
QPushButton#primary:hover  {{ background: {C['accent_h']}; }}
QPushButton#primary:pressed {{ background: {C['accent_d']}; }}
QPushButton#primary:disabled {{ background: {C['bg_hover']}; color: {C['text_dim']}; }}

/* ── Buttons – secondary ── */
QPushButton#secondary {{
    background: #ffffff;
    color: {C['navy']};
    border: 1px solid {C['border_h']};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: {F['base']};
    min-height: 32px;
}}
QPushButton#secondary:hover  {{ background: {C['bg_hover']}; border-color: {C['accent']}; color: {C['accent_d']}; }}
QPushButton#secondary:pressed {{ background: {C['bg_active']}; }}

/* ── Buttons – danger ── */
QPushButton#danger {{
    background: transparent;
    color: {C['danger']};
    border: 1px solid {C['danger']};
    border-radius: 8px;
    padding: 8px 16px;
    font-size: {F['base']};
    min-height: 32px;
}}
QPushButton#danger:hover  {{ background: {C['danger']}; color: white; }}

/* ── Buttons – ghost (sidebar nav) ── */
QPushButton#nav_btn {{
    text-align: left;
    padding: 9px 16px 9px 14px;
    border: none;
    border-radius: 8px;
    color: #aab4c4;
    font-size: {F['base']};
    background: transparent;
    margin: 1px 8px;
}}
QPushButton#nav_btn:hover  {{ background: rgba(255,255,255,0.08); color: #ffffff; }}
QPushButton#nav_btn:checked {{
    background: {C['accent']};
    color: #ffffff;
    font-weight: 700;
}}

/* ── Tables ── */
QTableWidget {{
    background: #ffffff;
    border: 1px solid {C['border']};
    border-radius: 10px;
    gridline-color: {C['bg_panel']};
    color: {C['text']};
    alternate-background-color: {C['bg_base']};
    selection-background-color: {C['bg_active']};
    selection-color: {C['navy']};
}}
QTableWidget::item {{ padding: 6px 10px; }}
QTableWidget::item:hover {{ background: {C['bg_hover']}; }}
QHeaderView::section {{
    background: {C['navy']};
    color: #ffffff;
    padding: 9px 10px;
    border: none;
    border-right: 1px solid {C['navy_2']};
    font-weight: 700;
    font-size: {F['sm']};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QHeaderView::section:last {{ border-right: none; }}
QTableWidget QScrollBar:vertical {{
    background: {C['bg_panel']};
    width: 8px;
    margin: 0;
}}
QTableWidget QScrollBar::handle:vertical {{
    background: {C['border_h']};
    border-radius: 4px;
    min-height: 24px;
}}

/* ── Scrollbars global ── */
QScrollBar:vertical {{
    background: {C['bg_panel']};
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: {C['border_h']};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {C['accent']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1px solid {C['border']};
    border-radius: 0 10px 10px 10px;
    background: #ffffff;
}}
QTabBar::tab {{
    background: {C['bg_panel']};
    color: {C['text_muted']};
    border: 1px solid {C['border']};
    border-bottom: none;
    padding: 8px 20px;
    border-radius: 8px 8px 0 0;
    margin-right: 3px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    background: #ffffff;
    color: {C['accent_d']};
    border-bottom: 3px solid {C['accent']};
}}
QTabBar::tab:hover:!selected {{ background: {C['bg_hover']}; color: {C['navy']}; }}

/* ── Group / Frame cards ── */
QFrame#card {{
    background: #ffffff;
    border: 1px solid {C['border']};
    border-radius: 10px;
}}
QGroupBox {{
    background: #ffffff;
    border: 1px solid {C['border']};
    border-radius: 10px;
    margin-top: 14px;
    padding: 10px;
    font-weight: 700;
    color: {C['text_muted']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {C['accent']};
}}

/* ── Dialog buttons ── */
QDialogButtonBox QPushButton {{
    min-width: 90px;
    padding: 7px 16px;
    border-radius: 8px;
}}

/* ── Labels ── */
QLabel#page_title {{
    font-size: {F['xl']};
    font-weight: 800;
    color: {C['navy']};
}}
QLabel#section_title {{
    font-size: {F['md']};
    font-weight: 700;
    color: {C['accent_d']};
}}
QLabel#badge_ok  {{ color: {C['success']}; font-weight: 700; }}
QLabel#badge_err {{ color: {C['danger']}; font-weight: 700; }}
QLabel#badge_warn {{ color: {C['warning']}; font-weight: 700; }}
QLabel#muted {{ color: {C['text_muted']}; font-size: {F['sm']}; }}

/* ── Status bar ── */
QStatusBar {{ background: {C['navy']}; color: #aab4c4; font-size: {F['sm']}; }}
QStatusBar::item {{ border: none; }}

/* ── Tooltip ── */
QToolTip {{
    background: {C['navy']};
    color: #ffffff;
    border: none;
    padding: 5px 9px;
    border-radius: 6px;
}}

/* ── Splitter ── */
QSplitter::handle {{ background: {C['border']}; }}
"""

SIDEBAR_STYLE = f"""
QWidget#sidebar {{
    background: {C['navy']};
    border-right: none;
}}
QWidget#sidebar QWidget {{
    background: transparent;
}}
QLabel#logo_text {{
    color: {C['accent']};
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 1px;
}}
QLabel#company_name {{
    color: #ffffff;
    font-size: {F['sm']};
    font-weight: 700;
    padding: 0 14px;
}}
QLabel#user_label {{
    color: #8a94a6;
    font-size: {F['xs']};
    padding: 0 14px 8px;
}}
QLabel#section_sep {{
    color: #5d6b80;
    font-size: {F['xs']};
    font-weight: 700;
    letter-spacing: 1px;
    padding: 8px 18px 2px;
    text-transform: uppercase;
}}
QPushButton#logout_btn {{
    text-align: left;
    padding: 8px 16px;
    border: none;
    border-radius: 8px;
    color: #ff9b9c;
    font-size: {F['base']};
    background: transparent;
    margin: 1px 8px;
}}
QPushButton#logout_btn:hover {{ background: rgba(219,77,79,0.25); color: #ffffff; }}
"""
