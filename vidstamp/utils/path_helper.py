"""
vidstamp/utils/path_helper.py - Helper pendeteksi environment PyInstaller dan biner eksternal
"""
import sys
import os
import shutil

def get_resource_path(relative_path):
    """Mendapatkan absolute path ke resource, bekerja untuk dev dan PyInstaller runtime."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_ffmpeg_path():
    """
    Mendeteksi dan mengembalikan path biner FFmpeg yang valid.
    Urutan deteksi:
    1. Runtime extraction path PyInstaller (sys._MEIPASS/bin)
    2. Folder bin lokal (./bin/win/ffmpeg.exe atau ./bin/mac/ffmpeg)
    3. Fallback pencarian biner di PATH sistem.
    """
    # 1. Cek di lingkungan PyInstaller
    try:
        base_path = sys._MEIPASS
        ext = ".exe" if os.name == "nt" else ""
        pyinstaller_ffmpeg = os.path.join(base_path, "bin", f"ffmpeg{ext}")
        if os.path.exists(pyinstaller_ffmpeg):
            return pyinstaller_ffmpeg
    except AttributeError:
        pass

    # 2. Cek di folder bin proyek lokal
    subfolder = "win" if os.name == "nt" else "mac"
    ext = ".exe" if os.name == "nt" else ""
    local_path = os.path.join(os.path.abspath("."), "bin", subfolder, f"ffmpeg{ext}")
    if os.path.exists(local_path):
        return local_path

    # 3. Fallback ke PATH global sistem
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # Jika semua gagal, kembalikan 'ffmpeg' mentah dengan harapan ada di PATH
    return "ffmpeg"
