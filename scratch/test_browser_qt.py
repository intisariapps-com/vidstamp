"""
scratch/test_browser_qt.py - Tes Bootstrap LeftBrowserPanel PySide6
"""
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vidstamp.ui.browser_qt import LeftBrowserPanel

def test():
    print("Memulai tes bootstrap LeftBrowserPanel PySide6...")
    app = QApplication(sys.argv)
    
    dummy_select = lambda path: print(f"Video terpilih: {path}")
    dummy_dir = lambda: os.getcwd()
    
    # Instansiasi panel browser
    panel = LeftBrowserPanel(None, dummy_select, dummy_dir)
    panel.setWindowTitle("Test File Browser")
    panel.resize(300, 500)
    panel.show()
    
    # Pindah ke folder saat ini
    panel.navigate_to(os.getcwd())
    
    # Tutup otomatis setelah 1.5 detik
    def close():
        print("Menutup browser test. Sukses!")
        panel.close()
        app.quit()
        
    QTimer.singleShot(1500, close)
    app.exec()

if __name__ == "__main__":
    test()
