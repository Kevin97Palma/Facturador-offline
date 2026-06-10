import os, sys, traceback, faulthandler
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
faulthandler.enable()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
try:
    from client.main_window import MainWindow
    w = MainWindow()
    print('MAINWINDOW OK', flush=True)
except Exception:
    traceback.print_exc()
    sys.exit(1)
