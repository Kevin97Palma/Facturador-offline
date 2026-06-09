# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — one-DIR build (easier to maintain and update).
Produces: dist/Facturador/Facturador.exe
"""
import sys, os

block_cipher = None

# Collect all data files
datas = [
    ('server',  'server'),
    ('client',  'client'),
]

# Hidden imports needed by the app
hidden = [
    # Flask stack
    'flask', 'flask.cli', 'flask_cors', 'flask_sqlalchemy',
    'sqlalchemy', 'sqlalchemy.dialects.sqlite',
    'werkzeug', 'werkzeug.serving', 'werkzeug.middleware.proxy_fix',
    'jinja2', 'click',
    # Qt
    'PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui',
    'PyQt5.sip',
    # Networking / utils
    'requests', 'urllib3', 'certifi', 'charset_normalizer',
    'python_dateutil', 'dateutil',
    # ESC/POS (optional – don't fail if usb not present)
    'escpos', 'escpos.printer', 'escpos.capabilities',
    # Windows printing
    'win32print', 'win32api', 'pywintypes',
]

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'PIL',
              'unittest', 'test', 'distutils'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Facturador',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,         # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Facturador',
)
