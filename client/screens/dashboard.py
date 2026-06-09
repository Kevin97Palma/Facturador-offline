from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QWidget
from PyQt5.QtCore import Qt
from ..widgets import BaseScreen, StatCard, Divider, LoadWorker
from ..theme import C
from .. import api


CARDS = [
    ('facturas',      'FACTURAS',       '🧾', C['accent']),
    ('retenciones',   'RETENCIONES',    '🔖', '#388bfd'),
    ('notas_credito', 'N. CRÉDITO',     '📋', '#3fb950'),
    ('notas_debito',  'N. DÉBITO',      '📌', '#d29922'),
    ('guias',         'G. REMISIÓN',    '🚚', '#9b59b6'),
    ('liquidaciones', 'LIQUIDACIONES',  '🛒', '#1abc9c'),
]

ENDPOINTS = {
    'facturas':      '/api/facturas/{}',
    'retenciones':   '/api/retenciones/{}',
    'notas_credito': '/api/notas-credito/{}',
    'notas_debito':  '/api/notas-debito/{}',
    'guias':         '/api/guias/{}',
    'liquidaciones': '/api/liquidaciones/{}',
}


class DashboardScreen(BaseScreen):
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(20)

        empresa = api.get_empresa() or {}
        user = api.get_user() or {}

        # ── Header ──────────────────────────────────────────
        header = QWidget()
        header.setStyleSheet('background:transparent;')
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(0, 0, 0, 0)

        vl = QVBoxLayout()
        lbl_hi = QLabel(f"Bienvenido, {user.get('nombre', user.get('email', ''))}")
        lbl_hi.setObjectName('page_title')
        vl.addWidget(lbl_hi)
        lbl_rs = QLabel(empresa.get('razon_social', ''))
        lbl_rs.setStyleSheet(f'color:{C["text_muted"]}; font-size:13px;')
        vl.addWidget(lbl_rs)
        h_lay.addLayout(vl)

        h_lay.addStretch()

        # Ambiente pill
        amb = empresa.get('ambiente', '1')
        amb_txt = '⚡  PRODUCCIÓN' if amb == '2' else '🧪  PRUEBAS'
        amb_bg  = 'rgba(46,160,67,0.15)' if amb == '2' else 'rgba(210,153,34,0.15)'
        amb_fg  = C['accent_h'] if amb == '2' else C['warning']
        pill = QLabel(amb_txt)
        pill.setStyleSheet(f'''
            background:{amb_bg}; color:{amb_fg};
            border:1px solid {amb_fg}; border-radius:12px;
            font-size:12px; font-weight:700;
            padding:4px 14px;
        ''')
        h_lay.addWidget(pill)

        lay.addWidget(header)
        lay.addWidget(Divider())

        # ── Stats grid ──────────────────────────────────────
        lbl_stats = QLabel('Documentos del período')
        lbl_stats.setStyleSheet(f'color:{C["text_muted"]}; font-size:12px; font-weight:600; letter-spacing:0.5px;')
        lay.addWidget(lbl_stats)

        grid = QGridLayout()
        grid.setSpacing(14)
        self._cards = {}

        for i, (key, label, icon, color) in enumerate(CARDS):
            card = StatCard(f'{icon}  {label}', '—', color)
            self._cards[key] = card
            grid.addWidget(card, i // 3, i % 3)

        lay.addLayout(grid)

        # ── Info strip ──────────────────────────────────────
        lay.addStretch()
        info_strip = QFrame()
        info_strip.setStyleSheet(f'''
            background:{C["bg_card"]}; border:1px solid {C["border"]};
            border-radius:8px; padding:4px;
        ''')
        strip_lay = QHBoxLayout(info_strip)
        strip_lay.setContentsMargins(16, 10, 16, 10)

        for label, value in [
            ('RUC', empresa.get('ruc', '—')),
            ('Establecimiento', empresa.get('establecimiento', '001')),
            ('Punto de Emisión', empresa.get('punto_emision', '001')),
            ('Rol', (api.get_user() or {}).get('rol', '').capitalize()),
        ]:
            vb = QVBoxLayout()
            l1 = QLabel(label)
            l1.setStyleSheet(f'color:{C["text_muted"]}; font-size:11px; font-weight:600; background:transparent;border:none;')
            l2 = QLabel(value)
            l2.setStyleSheet(f'color:{C["text"]}; font-size:13px; font-weight:600; background:transparent;border:none;')
            vb.addWidget(l1)
            vb.addWidget(l2)
            strip_lay.addLayout(vb)
            strip_lay.addStretch()

        lay.addWidget(info_strip)

    def refresh(self):
        eid = api.empresa_id()
        if not eid:
            return
        for key, endpoint_tpl in ENDPOINTS.items():
            self._run(api.get, lambda r, k=key: self._update(k, r), endpoint_tpl.format(eid))

    def _update(self, key, result):
        card = self._cards.get(key)
        if card and result.get('ok'):
            data = result.get('data', [])
            total = len(data)
            auth = sum(1 for d in data if d.get('estado') == 'AUTORIZADO')
            card.set_value(str(total))
            card.setToolTip(f'{auth} autorizados de {total}')
