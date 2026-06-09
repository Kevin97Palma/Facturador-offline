"""Central design system for the Facturador desktop app."""

# ── Colour palette ────────────────────────────────────────────────────────────
C = {
    # Backgrounds
    'bg_deep':    '#0d1117',
    'bg_base':    '#161b22',
    'bg_card':    '#1c2128',
    'bg_panel':   '#21262d',
    'bg_hover':   '#2d333b',
    'bg_active':  '#1f4068',

    # Brand
    'accent':     '#2ea043',
    'accent_h':   '#3fb950',
    'accent_d':   '#238636',
    'danger':     '#da3633',
    'danger_h':   '#f85149',
    'warning':    '#d29922',
    'info':       '#388bfd',

    # Text
    'text':       '#e6edf3',
    'text_muted': '#7d8590',
    'text_dim':   '#484f58',

    # Border
    'border':     '#30363d',
    'border_h':   '#484f58',
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
    border-radius: 6px;
    padding: 7px 10px;
    color: {C['text']};
    selection-background-color: {C['accent']};
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {C['accent']};
    background: {C['bg_panel']};
}}
QLineEdit:disabled {{
    background: {C['bg_deep']};
    color: {C['text_dim']};
}}

/* ── Combo / Spin ── */
QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    background: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 6px 10px;
    color: {C['text']};
    min-height: 28px;
}}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
    border: 1px solid {C['accent']};
}}
QComboBox QAbstractItemView {{
    background: {C['bg_panel']};
    border: 1px solid {C['border']};
    color: {C['text']};
    selection-background-color: {C['bg_active']};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: {C['bg_hover']};
    border: none;
    width: 18px;
}}

/* ── Buttons – primary (green) ── */
QPushButton#primary {{
    background: {C['accent']};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: {F['base']};
    min-height: 30px;
}}
QPushButton#primary:hover  {{ background: {C['accent_h']}; }}
QPushButton#primary:pressed {{ background: {C['accent_d']}; }}
QPushButton#primary:disabled {{ background: {C['bg_hover']}; color: {C['text_dim']}; }}

/* ── Buttons – secondary ── */
QPushButton#secondary {{
    background: {C['bg_panel']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 7px 14px;
    font-size: {F['base']};
    min-height: 30px;
}}
QPushButton#secondary:hover  {{ background: {C['bg_hover']}; border-color: {C['border_h']}; }}
QPushButton#secondary:pressed {{ background: {C['bg_active']}; }}

/* ── Buttons – danger ── */
QPushButton#danger {{
    background: transparent;
    color: {C['danger']};
    border: 1px solid {C['danger']};
    border-radius: 6px;
    padding: 7px 14px;
    font-size: {F['base']};
    min-height: 30px;
}}
QPushButton#danger:hover  {{ background: {C['danger']}; color: white; }}

/* ── Buttons – ghost (sidebar nav) ── */
QPushButton#nav_btn {{
    text-align: left;
    padding: 9px 16px 9px 14px;
    border: none;
    border-radius: 6px;
    color: {C['text_muted']};
    font-size: {F['base']};
    background: transparent;
    margin: 1px 6px;
}}
QPushButton#nav_btn:hover  {{ background: {C['bg_hover']}; color: {C['text']}; }}
QPushButton#nav_btn:checked {{
    background: {C['bg_active']};
    color: {C['accent_h']};
    font-weight: 600;
}}

/* ── Tables ── */
QTableWidget {{
    background: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    gridline-color: {C['bg_panel']};
    color: {C['text']};
    alternate-background-color: {C['bg_deep']};
    selection-background-color: {C['bg_active']};
    selection-color: {C['text']};
}}
QTableWidget::item {{ padding: 5px 10px; }}
QTableWidget::item:hover {{ background: {C['bg_hover']}; }}
QHeaderView::section {{
    background: {C['bg_panel']};
    color: {C['text_muted']};
    padding: 8px 10px;
    border: none;
    border-right: 1px solid {C['border']};
    font-weight: 600;
    font-size: {F['sm']};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QHeaderView::section:last {{ border-right: none; }}
QTableWidget QScrollBar:vertical {{
    background: {C['bg_deep']};
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
    background: {C['bg_deep']};
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: {C['border']};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {C['border_h']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1px solid {C['border']};
    border-radius: 0 6px 6px 6px;
    background: {C['bg_card']};
}}
QTabBar::tab {{
    background: {C['bg_deep']};
    color: {C['text_muted']};
    border: 1px solid {C['border']};
    border-bottom: none;
    padding: 7px 18px;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {C['bg_card']};
    color: {C['text']};
    border-bottom: 2px solid {C['accent']};
}}
QTabBar::tab:hover:!selected {{ background: {C['bg_panel']}; color: {C['text']}; }}

/* ── Group / Frame cards ── */
QFrame#card {{
    background: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: 8px;
}}
QGroupBox {{
    border: 1px solid {C['border']};
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px;
    font-weight: 600;
    color: {C['text_muted']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {C['accent_h']};
}}

/* ── Dialog buttons ── */
QDialogButtonBox QPushButton {{
    min-width: 90px;
    padding: 7px 16px;
    border-radius: 6px;
}}

/* ── Labels ── */
QLabel#page_title {{
    font-size: {F['xl']};
    font-weight: 700;
    color: {C['text']};
}}
QLabel#section_title {{
    font-size: {F['md']};
    font-weight: 600;
    color: {C['accent_h']};
}}
QLabel#badge_ok  {{ color: #3fb950; font-weight: 600; }}
QLabel#badge_err {{ color: #f85149; font-weight: 600; }}
QLabel#badge_warn {{ color: #d29922; font-weight: 600; }}
QLabel#muted {{ color: {C['text_muted']}; font-size: {F['sm']}; }}

/* ── Status bar ── */
QStatusBar {{ background: {C['bg_deep']}; color: {C['text_muted']}; font-size: {F['sm']}; }}
QStatusBar::item {{ border: none; }}

/* ── Tooltip ── */
QToolTip {{
    background: {C['bg_panel']};
    color: {C['text']};
    border: 1px solid {C['border']};
    padding: 4px 8px;
    border-radius: 4px;
}}

/* ── Splitter ── */
QSplitter::handle {{ background: {C['border']}; }}
"""

SIDEBAR_STYLE = f"""
QWidget#sidebar {{
    background: {C['bg_deep']};
    border-right: 1px solid {C['border']};
}}
QLabel#logo_text {{
    color: {C['accent_h']};
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel#company_name {{
    color: {C['text']};
    font-size: {F['sm']};
    font-weight: 600;
    padding: 0 14px;
}}
QLabel#user_label {{
    color: {C['text_muted']};
    font-size: {F['xs']};
    padding: 0 14px 8px;
}}
QLabel#section_sep {{
    color: {C['text_dim']};
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
    border-radius: 6px;
    color: {C['danger']};
    font-size: {F['base']};
    background: transparent;
    margin: 1px 6px;
}}
QPushButton#logout_btn:hover {{ background: rgba(218,54,51,0.12); }}
"""
