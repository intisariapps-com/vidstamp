---
name: pyinstaller-desktop-bundling
description: Panduan bundling executable desktop portabel untuk Windows (PyInstaller + Inno Setup) dan macOS (.app/.dmg).
---

# Panduan Bundling Desktop (VidStamp)

Dokumen ini menjelaskan alur kerja bundling biner mandiri (.exe untuk Windows, .dmg untuk macOS) agar aplikasi dapat didistribusikan kepada pengguna akhir secara mudah dan mandiri.

## 1. Resolusi Path Sumber Daya Dinamis (PyInstaller sys._MEIPASS)
Saat aplikasi dikompilasi ke mode satu file (`--onefile`), PyInstaller mengekstrak seluruh pustaka dan aset non-Python ke dalam folder temporer di disk yang jalurnya disimpan dalam `sys._MEIPASS`.

Gunakan fungsi pembantu `resource_path` di seluruh modul UI dan utilitas untuk merujuk file aset (gambar ikon, template, biner portabel FFmpeg):

```python
import os
import sys

def resource_path(relative_path):
    """ Dapatkan path absolut untuk aset, berfungsi baik saat pengembangan maupun setelah dibundel """
    try:
        # PyInstaller membuat folder sementara dan menyimpan path di _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
```

## 2. Struktur File vidstamp.spec
Berkas spesifikasi (`.spec`) mengonfigurasi bagaimana PyInstaller mengemas modul. 

### Elemen Penting:
* **`datas`**: Daftar aset non-Python (seperti ikon, template config).
* **`binaries`**: Biner portabel pihak ketiga (seperti `ffmpeg.exe` dan `ffprobe.exe`).
* **`hiddenimports`**: Pustaka yang diimpor secara dinamis (seperti `ffpyplayer` compiler-dependent, atau SDL2 library).

```python
# Contoh konfigurasi parsial vidstamp.spec
a = Analysis(
    ['vidstamp\\__main__.py'],
    pathex=[],
    binaries=[
        ('bin/win/ffmpeg.exe', 'bin/win'),
        ('bin/win/ffprobe.exe', 'bin/win')
    ],
    datas=[
        ('vidstamp/ui/assets/*.ico', 'vidstamp/ui/assets'),
        ('season_skip_template.json', '.')
    ],
    hiddenimports=['ffpyplayer', 'ffpyplayer.player', 'customtkinter'],
    ...
)
```

## 3. Kompilasi Installer Windows (Inno Setup)
Setelah direktori hasil kompilasi PyInstaller (`dist/vidstamp/`) selesai diuji secara visual:
1. Pastikan program berjalan lancar tanpa ada DLL yang hilang (terutama SDL2 milik `ffpyplayer`).
2. Gunakan berkas spesifikasi `installer_windows.iss` untuk membungkus direktori `dist/vidstamp/` ke berkas Setup tunggal (`VidStamp_Setup.exe`).
3. Selalu sertakan runtime C++ redistributable jika program crash saat boot di Windows yang belum ter-update.

## 4. Bundling macOS (.dmg)
Untuk macOS:
1. Gunakan PyInstaller di lingkungan macOS asli untuk menghasilkan folder aplikasi `VidStamp.app`.
2. Gunakan pustaka open-source `create-dmg` via bash command untuk membungkus aplikasi ke dalam volume `.dmg`:
   ```bash
   create-dmg \
     --volname "VidStamp Installer" \
     --volicon "assets/icon.icns" \
     --window-pos 200 120 \
     --window-size 800 400 \
     --icon-size 100 \
     --icon "VidStamp.app" 200 190 \
     --hide-extension "VidStamp.app" \
     --app-drop-link 600 190 \
     "dist/VidStamp_Setup.dmg" \
     "dist/VidStamp.app"
   ```
3. Pastikan tidak ada berkas `.env` atau kunci API yang tertulis ke dalam isi `.app` bundle.
