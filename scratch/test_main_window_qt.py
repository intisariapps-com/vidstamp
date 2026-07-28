"""
scratch/test_main_window_qt.py - Tes Bootstrap VideoAppController (QMainWindow) PySide6
"""
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vidstamp.ui.main_window import VideoAppController

def test():
    print("Memulai tes bootstrap VideoAppController (QMainWindow) PySide6...")
    app = QApplication(sys.argv)
    
    # Coba inisialisasi controller
    controller = VideoAppController(os.getcwd())
    controller.show()
    
    # Tutup otomatis setelah 2 detik
    def close():
        print("Menutup jendela utama test. Sukses!")
        controller.close()
        app.quit()
        
    QTimer.singleShot(2000, close)
    app.exec()

if __name__ == "__main__":
    test()
