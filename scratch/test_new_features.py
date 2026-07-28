"""
scratch/test_new_features.py - Uji Bootstrap Visual Jendela Baru (Launcher & Extractor)
"""
import os
import sys
import tkinter as tk
import pytest

# Tambahkan root proyek ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.mark.skip(reason="Memeriksa GUI di runner non-interaktif")
def test_launcher_bootstrap():
    print("Memulai tes bootstrap LauncherWindow...")
    root = tk.Tk()
    root.withdraw()
    
    from vidstamp.ui.launcher import LauncherWindow
    
    dummy_fn = lambda *args: print("Callback terpicu")
    launcher = LauncherWindow(dummy_fn, dummy_fn, lambda: os.getcwd())
    
    def close():
        print("Menutup Launcher. Sukses!")
        launcher.destroy()
        root.destroy()
        
    launcher.after(1500, close)
    launcher.mainloop()

@pytest.mark.skip(reason="Memeriksa GUI di runner non-interaktif")
def test_extractor_bootstrap():
    print("Memulai tes bootstrap AudioSubExtractorWizard...")
    root = tk.Tk()
    root.withdraw()
    
    from vidstamp.ui.extractor_tool import AudioSubExtractorWizard
    extractor = AudioSubExtractorWizard(root, os.getcwd())
    
    def close():
        print("Menutup Extractor. Sukses!")
        extractor.destroy()
        root.destroy()
        
    extractor.after(1500, close)
    extractor.mainloop()

if __name__ == "__main__":
    test_launcher_bootstrap()
    test_extractor_bootstrap()
    print("Semua tes bootstrap jendela baru SUKSES!")
