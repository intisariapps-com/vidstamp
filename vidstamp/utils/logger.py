"""
vidstamp/utils/logger.py - Sistem Logger Global dan Penanganan Kesalahan Fatal (Crash Logger)
"""
import sys
import os
import traceback
import logging
from tkinter import messagebox

# Berkas log ditempatkan di root folder kerja aplikasi saat ini
LOG_FILE = os.path.join(os.getcwd(), "crash.log")

def init_logger():
    """Menginisialisasi pencatatan error global ke berkas crash.log"""
    # Bersihkan file handler lama jika ada
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.ERROR,
        format="=== CRASH LOG [%(asctime)s] ===\n%(message)s\n" + "="*50 + "\n",
        encoding="utf-8"
    )

    def global_excepthook(exctype, value, tb):
        err_msg = "".join(traceback.format_exception(exctype, value, tb))
        
        # Tulis ke berkas log
        logging.error(f"Uncaught Exception:\n{err_msg}")
        
        # Cetak ke stderr bawaan konsol
        sys.__excepthook__(exctype, value, tb)
        
        # Tampilkan pemberitahuan dialog
        show_crash_dialog(err_msg)

    sys.excepthook = global_excepthook

def show_crash_dialog(error_detail):
    """Menampilkan kotak dialog visual pemberitahuan error"""
    msg = (
        "Aplikasi mengalami kesalahan fatal yang tidak terduga.\n\n"
        f"Detail kesalahan telah dicatat di berkas:\n{LOG_FILE}\n\n"
        "Silakan laporkan masalah ini kepada pengembang."
    )
    try:
        messagebox.showerror("Kesalahan Fatal VidStamp", msg)
    except Exception:
        pass

def register_tkinter_exception_handler(root):
    """Menghubungkan event loop Tkinter callback exception ke logger"""
    def tkinter_excepthook(exctype, value, tb):
        err_msg = "".join(traceback.format_exception(exctype, value, tb))
        logging.error(f"Tkinter Callback Exception:\n{err_msg}")
        show_crash_dialog(err_msg)
        
    root.report_callback_exception = tkinter_excepthook
