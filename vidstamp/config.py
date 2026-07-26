"""
vidstamp/config.py - Konfigurasi global untuk aplikasi VidStamp
"""
import os

VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".m4v", ".webm", ".ts", ".rmvb"}

# Warna OpenCV (BGR format)
COLOR_TS   = (0, 255, 200)    # Cyan-hijau
COLOR_MARK = (80, 140, 255)   # Oranye/biru muda
COLOR_END  = (80, 255, 140)   # Hijau
COLOR_BG   = (0, 0, 0)        # Bayangan teks (Hitam)

FONT = 2 # cv2.FONT_HERSHEY_DUPLEX (Nilai integernya adalah 2)

# Direktori pencarian awal default
ROOT_DIRS = [
    r"e:\ANIME",
    os.path.expanduser("~\\Videos")
]
