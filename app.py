"""
Entry point for the Facturador application.
- In 'servidor' mode: starts the Flask API server in a background thread, then launches the Qt GUI.
- In 'cliente' mode: launches the Qt GUI only (connects to a remote server).
"""
import sys
import os


def _ensure_dirs():
    base = os.path.dirname(os.path.abspath(__file__))
    for d in ['data/xml', 'data/firmas', 'data/logos']:
        os.makedirs(os.path.join(base, d), exist_ok=True)


def _start_server():
    import threading
    from server.main import run_server
    t = threading.Thread(target=run_server, args=('0.0.0.0', 5000), daemon=True)
    t.start()
    # Give the server a moment to start
    import time
    time.sleep(1.5)


def main():
    _ensure_dirs()

    from client import config as cfg
    mode = cfg.get('mode', 'servidor')

    if mode == 'servidor':
        _start_server()

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt

    app = QApplication(sys.argv)
    app.setApplicationName('Facturador Electrónico')
    app.setStyle('Fusion')

    from client.screens.login import LoginScreen
    from client.main_window import MainWindow

    login = LoginScreen()

    def on_login():
        login.hide()
        window = MainWindow()
        window.show()
        app._main_window = window

    login.login_success.connect(on_login)
    login.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
