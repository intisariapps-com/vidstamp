# Spesifikasi Kebutuhan Perangkat Lunak (SRS): Bundling & Kompilasi Desktop (Windows & macOS)

Dokumen ini mendokumentasikan spesifikasi konfigurasi kompilasi dan bundling program **VidStamp** agar dapat dikonversi menjadi biner desktop portable mandiri (`.exe` Windows dan `.app`/`.dmg` macOS).

---

## 1. Latar Belakang & Kebutuhan
Program VidStamp memerlukan parser OpenCV, audio engine `ffpyplayer` (yang membungkus SDL2/FFmpeg DLLs), dan subprocess FFmpeg untuk pembacaan subtitle internal berkas `.mkv`. Untuk menyalurkannya ke pengguna akhir secara portable:
* Semua pustaka Python (termasuk modul biner compiled C++ dari OpenCV, Pillow, dan ffpyplayer) harus dibundel.
* File biner `ffmpeg` eksternal harus diletakkan dalam folder aplikasi sehingga program tidak bergantung pada instalasi FFmpeg global di komputer pengguna.
* Program harus mendeteksi secara dinamis apakah ia sedang berjalan di dalam penampung ekstraksi sementara PyInstaller (`sys._MEIPASS`) atau mode interpreter biasa.

---

## 2. Struktur Modul & Konfigurasi Baru

### A. Modul Path Helper
* **File**: `vidstamp/utils/path_helper.py`
* **Fungsi**:
  * `get_resource_path(relative_path)`: Mengembalikan path absolut resource dengan mendeteksi atribut `sys._MEIPASS`.
  * `get_ffmpeg_path()`: Mencari biner `ffmpeg` secara berurutan di folder ekstraksi temp PyInstaller (`_MEIPASS/bin`), folder bin lokal proyek (`./bin/win` atau `./bin/mac`), atau fallback ke PATH global sistem.

### B. Pemanggilan FFmpeg Subprocess
* **File**: `vidstamp/core/subtitle.py`
* **Perubahan**: Mengubah variabel pemanggilan cmd pertama dari `'ffmpeg'` menjadi path absolut dinamis hasil fungsi `get_ffmpeg_path()`.

### C. File Spesifikasi PyInstaller (Spec File)
* **File**: `vidstamp.spec`
* **Konfigurasi Utama**:
  * Menyalin biner `ffmpeg.exe` (Windows) atau `ffmpeg` (macOS) ke dalam folder target `bin`.
  * Menyalin direktori modul `ffpyplayer` secara utuh ke runtime folder untuk memastikan semua DLL biner dependensinya (seperti SDL2) terangkut dengan baik dan tidak menimbulkan crash `ImportError`.
  * Menonaktifkan konsol debug (`console=False`) agar interface berjalan bersih di window mandiri.

### D. Struktur Folder Biner Eksternal
* **Windows**: `bin/win/ffmpeg.exe`
* **macOS**: `bin/mac/ffmpeg`

### E. Aset Visual & Media Installer
Untuk memberikan tampilan installer yang premium dan profesional, aset visual berikut telah disiapkan di folder `vidstamp/ui/assets/`:
* `icon.png`: Ikon utama aplikasi dengan format gambar PNG resolusi tinggi.
* `icon.ico`: Ikon aplikasi Windows (multi-resolusi: 16px hingga 256px) untuk disematkan pada executable VidStamp dan installer.
* `installer_banner.bmp`: Banner samping berdimensi 164x314 piksel dengan latar gelap elegan untuk Wizard layar sambutan Inno Setup.
* `installer_small.bmp`: Logo pojok kanan atas berdimensi 55x58 piksel untuk halaman dalam Wizard Inno Setup.
* `installer_windows.iss` (berada di root): File konfigurasi Inno Setup Compiler untuk Windows desktop installer.

## 3. Alur Kompilasi & Build (Bagi Pengembang)

### Langkah Kompilasi Windows (.exe):
1. Unduh biner FFmpeg Windows dari situs resmi (static build).
2. Salin berkas `ffmpeg.exe` ke direktori `bin/win/` proyek.
3. Jalankan perintah kompilasi:
   ```powershell
   pyinstaller vidstamp.spec
   ```
4. Folder executable hasil bundling akan tersedia di direktori `dist/VidStamp/`. Jalankan `VidStamp.exe` di dalamnya untuk menguji.
5. Jalankan installer compiler **Inno Setup** menggunakan skrip konfigurasi installer untuk menghasilkan file installer `.exe` Setup tunggal.

### Langkah Kompilasi macOS (.app & .dmg):
1. Unduh biner FFmpeg macOS static build.
2. Salin berkas `ffmpeg` ke direktori `bin/mac/` proyek dan pastikan executable permission diatur (`chmod +x bin/mac/ffmpeg`).
3. Jalankan perintah kompilasi:
   ```bash
   pyinstaller vidstamp.spec
   ```
4. Hasil kompilasi berupa `VidStamp.app` akan ada di folder `dist/`.
5. Gunakan utility `create-dmg` untuk membungkus `VidStamp.app` menjadi file `.dmg` installer portable.
