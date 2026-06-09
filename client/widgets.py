"""Shared widgets used by all screens."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QComboBox, QFrame, QSizePolicy,
    QDialog, QDialogButtonBox, QFormLayout, QAbstractItemView,
    QSpinBox, QDoubleSpinBox, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QColor, QPalette
from .theme import APP_STYLE, C


# ── Screen base style (applied per-screen so dialogs inherit it too) ──────────
SCREEN_STYLE = APP_STYLE


def make_btn(text: str, obj_name: str = 'secondary', parent=None) -> QPushButton:
    b = QPushButton(text, parent)
    b.setObjectName(obj_name)
    b.setCursor(Qt.PointingHandCursor)
    return b


def make_table(cols: list) -> QTableWidget:
    t = QTableWidget(0, len(cols))
    t.setHorizontalHeaderLabels(cols)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setStretchLastSection(True)
    t.horizontalHeader().setHighlightSections(False)
    t.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    t.setShowGrid(False)
    t.setFocusPolicy(Qt.NoFocus)
    return t


def table_item(text: str, center: bool = False) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text))
    if center:
        item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
    else:
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    return item


_ESTADO_COLORS = {
    'AUTORIZADO':    ('#3fb950', '#0d2114'),
    'NO_AUTORIZADO': ('#f85149', '#2d1414'),
    'PENDIENTE':     ('#d29922', '#2d2514'),
    'ANULADO':       ('#7d8590', '#1c2128'),
}


def set_estado_item(table: QTableWidget, row: int, col: int, estado: str):
    fg, bg = _ESTADO_COLORS.get(estado, (C['text'], C['bg_card']))
    item = QTableWidgetItem(estado)
    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
    item.setForeground(QColor(fg))
    item.setBackground(QColor(bg))
    table.setItem(row, col, item)


class LoadWorker(QThread):
    done = pyqtSignal(object)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.done.emit(self.fn(*self.args, **self.kwargs))
        except Exception as e:
            self.done.emit({'ok': False, 'error': str(e)})


# ── Toast notification (non-blocking) ─────────────────────────────────────────

class Toast(QWidget):
    """Floating notification that auto-dismisses."""

    _COLORS = {
        'ok':      (C['accent'],  '#0d2114'),
        'error':   (C['danger'],  '#2d1414'),
        'warning': (C['warning'], '#2d2514'),
        'info':    (C['info'],    '#0d1e3d'),
    }

    def __init__(self, msg: str, kind: str = 'ok', parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)

        border, bg = self._COLORS.get(kind, (C['accent'], '#0d2114'))
        icon = {'ok': '✓', 'error': '✕', 'warning': '⚠', 'info': 'ℹ'}.get(kind, '·')

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)

        inner = QFrame()
        inner.setStyleSheet(
            f'background:{bg}; border:1px solid {border}; border-radius:8px;'
        )
        i_lay = QHBoxLayout(inner)
        i_lay.setContentsMargins(12, 8, 12, 8)
        i_lay.setSpacing(10)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet(f'color:{border}; font-size:15px; font-weight:bold; background:transparent; border:none;')
        lbl_text = QLabel(msg)
        lbl_text.setStyleSheet(f'color:{C["text"]}; font-size:13px; background:transparent; border:none;')
        lbl_text.setWordWrap(True)

        i_lay.addWidget(lbl_icon)
        i_lay.addWidget(lbl_text, 1)
        lay.addWidget(inner)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        inner.setGraphicsEffect(shadow)

        self.adjustSize()

        if parent:
            pw = parent.window()
            pr = pw.geometry()
            self.move(pr.right() - self.width() - 20, pr.bottom() - self.height() - 50)

        QTimer.singleShot(3000, self.close)


def toast(parent, msg: str, kind: str = 'ok'):
    t = Toast(msg, kind, parent)
    t.show()


def confirm(parent, msg: str, title: str = 'Confirmar') -> bool:
    dlg = QMessageBox(parent)
    dlg.setWindowTitle(title)
    dlg.setText(msg)
    dlg.setIcon(QMessageBox.Question)
    dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    dlg.setDefaultButton(QMessageBox.No)
    dlg.setStyleSheet(APP_STYLE)
    return dlg.exec_() == QMessageBox.Yes


def show_error(parent, msg: str, title: str = 'Error'):
    toast(parent, msg, 'error')


def show_info(parent, msg: str, title: str = 'Información'):
    toast(parent, msg, 'ok')


class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet(f'color: {C["border"]}; max-height: 1px; background: {C["border"]};')


class SearchBar(QLineEdit):
    def __init__(self, placeholder: str = 'Buscar...', parent=None):
        super().__init__(parent)
        self.setPlaceholderText(f'  🔍  {placeholder}')
        self.setFixedHeight(36)
        self.setStyleSheet(f'''
            QLineEdit {{
                background: {C["bg_card"]};
                border: 1px solid {C["border"]};
                border-radius: 18px;
                padding: 0 14px;
                font-size: 13px;
                color: {C["text"]};
            }}
            QLineEdit:focus {{ border-color: {C["accent"]}; }}
        ''')


class StatCard(QFrame):
    def __init__(self, title: str, value: str = '—', color: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName('card')
        color = color or C['accent']
        self.setStyleSheet(f'''
            QFrame#card {{
                background: {C["bg_card"]};
                border: 1px solid {C["border"]};
                border-top: 3px solid {color};
                border-radius: 8px;
            }}
        ''')
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f'color:{C["text_muted"]}; font-size:12px; font-weight:600; letter-spacing:0.5px; background:transparent; border:none;')

        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f'color:{color}; font-size:28px; font-weight:700; background:transparent; border:none;')

        lay.addWidget(lbl_title)
        lay.addWidget(self.lbl_value)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def set_value(self, v: str):
        self.lbl_value.setText(v)


class BaseScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(APP_STYLE)
        self._workers = []
        self._setup_ui()

    def _setup_ui(self):
        pass

    def _run(self, fn, callback, *args, **kwargs):
        w = LoadWorker(fn, *args, **kwargs)
        w.done.connect(callback)
        w.start()
        self._workers.append(w)

    def refresh(self):
        pass

    def _page_header(self, title: str, subtitle: str = '') -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.setSpacing(2)
        lbl = QLabel(title)
        lbl.setObjectName('page_title')
        lay.addWidget(lbl)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet(f'color:{C["text_muted"]}; font-size:13px;')
            lay.addWidget(sub)
        lay.addWidget(Divider())
        return lay
