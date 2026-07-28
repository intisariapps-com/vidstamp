"""
scratch/test_batch_merger_ui.py - Uji Bootstrap GUI Batch Merger Wizard secara Terisolasi
"""
import os
import sys
import tkinter as tk

# Tambahkan root proyek ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_wizard_bootstrap():
    print("Memulai tes bootstrap GUI BatchMergerWizard...")
    
    root = tk.Tk()
    root.withdraw() # Sembunyikan window root
    
    # Gunakan directory CWD sebagai target directory pengujian folder video
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"Menggunakan test directory: {test_dir}")
    
    from vidstamp.ui.batch_merger import BatchMergerWizard
    
    # Inisialisasi Wizard
    wizard = BatchMergerWizard(root, test_dir)
    
    # Timer untuk menutup otomatis setelah 2.5 detik
    def close_test():
        print("Menutup Wizard secara otomatis. Tes bootstrap sukses!")
        wizard.destroy()
        root.destroy()
        
    root.after(2500, close_test)
    root.mainloop()

if __name__ == "__main__":
    test_wizard_bootstrap()
