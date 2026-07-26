"""
vidstamp/__main__.py - Entry point utama aplikasi VidStamp
"""
import os
import sys

# Deteksi direktori induk dari folder 'vidstamp' secara dinamis
# dan tambahkan ke sys.path agar impor absolut 'from vidstamp...' selalu berhasil
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from vidstamp.ui.main_window import start_gui

if __name__ == "__main__":
    # Mendukung input argumen path video / folder dari command line
    start_arg = sys.argv[1] if len(sys.argv) > 1 else None
    start_gui(start_arg)
