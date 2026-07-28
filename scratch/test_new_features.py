"""
scratch/test_new_features.py - Uji Bootstrap Visual Jendela Baru (Launcher & Extractor)
"""
import os
import sys
# Tambahkan root proyek ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_launcher_bootstrap():
    print("Memulai tes bootstrap LauncherWindow...")
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from vidstamp.ui.launcher import LauncherWindow
    
    app = QApplication(sys.argv)
    
    dummy_fn = lambda *args: print("Callback terpicu")
    launcher = LauncherWindow(dummy_fn, dummy_fn, lambda: os.getcwd())
    launcher.show()
    
    def close():
        print("Menutup Launcher. Sukses!")
        launcher.close()
        app.quit()
        
    QTimer.singleShot(1500, close)
    app.exec()

def test_extractor_bootstrap():
    print("Memulai tes bootstrap AudioSubExtractorWizard...")
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from vidstamp.ui.extractor_tool import AudioSubExtractorWizard
    
    app = QApplication(sys.argv) if QApplication.instance() is None else QApplication.instance()
    
    extractor = AudioSubExtractorWizard(None, os.getcwd())
    extractor.show()
    
    def close():
        print("Menutup Extractor. Sukses!")
        extractor.close()
        app.quit()
        
    QTimer.singleShot(1500, close)
    app.exec()

if __name__ == "__main__":
    test_launcher_bootstrap()
    test_extractor_bootstrap()
    print("Semua tes bootstrap jendela baru SUKSES!")
