"""
vidstamp/config.py - Konfigurasi global untuk aplikasi VidStamp
"""
import os

from vidstamp.utils.file_manager import load_global_config

# Muat data konfigurasi global secara dinamis
_g_config = load_global_config()

VIDEO_EXTS = set(_g_config.get("video_exts", [
    ".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".m4v", ".webm", ".ts", ".rmvb"
]))

# Warna OpenCV (BGR format)
COLOR_TS   = (0, 255, 200)    # Cyan-hijau
COLOR_MARK = (80, 140, 255)   # Oranye/biru muda
COLOR_END  = (80, 255, 140)   # Hijau
COLOR_BG   = (0, 0, 0)        # Bayangan teks (Hitam)

FONT = 2 # cv2.FONT_HERSHEY_DUPLEX (Nilai integernya adalah 2)

# Direktori pencarian awal default
ROOT_DIRS = _g_config.get("root_dirs", [
    r"e:\ANIME",
    os.path.expanduser("~\\Videos")
])

