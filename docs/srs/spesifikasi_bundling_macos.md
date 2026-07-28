# Spesifikasi Kebutuhan Perangkat Lunak (SRS): Bundling macOS (.dmg) & Kompilasi .app

## 1. Pendahuluan
Dokumen ini menetapkan spesifikasi teknis dan alur otomatisasi untuk mengemas aplikasi **VidStamp** menjadi berkas biner mandiri macOS (`.app`) dan mendistribusikannya melalui volume installer disk image (`.dmg`).

Hal ini penting untuk memberikan kenyamanan instalasi bergaya macOS native kepada pengguna akhir, sekaligus memastikan seluruh aset (seperti ikon, setelan bawaan) dan dependensi biner pihak ketiga (`ffmpeg` dan `ffprobe` macOS) dikemas dengan aman di dalam bundel aplikasi.

---

## 2. Struktur Bundel Aplikasi macOS (`.app`)
PyInstaller di lingkungan macOS akan menghasilkan folder bundel terstruktur dengan ekstensi `.app`. Struktur bundel ini mengikuti standar macOS App Bundle:

```
VidStamp.app/
└── Contents/
    ├── Info.plist              # Metadata aplikasi (bundle ID, tipe file yang didukung)
    ├── MacOS/
    │   ├── VidStamp            # Biner executable utama
    │   └── bin/
    │       ├── ffmpeg          # Biner statis FFmpeg macOS
    │       └── ffprobe         # Biner statis FFprobe macOS
    └── Resources/
        ├── icon.icns           # Sumber daya ikon aplikasi (macOS format)
        └── ...                 # Sumber daya in-memory tambahan
```

### 2.1. Penyesuaian `vidstamp.spec` untuk macOS
Berkas spesifikasi PyInstaller `vidstamp.spec` harus diperbarui agar:
1. Menyertakan biner `ffmpeg` dan `ffprobe` yang sesuai untuk arsitektur target macOS (diletakkan di `bin/mac/`).
2. Menghasilkan objek `BUNDLE` di akhir proses pengemasan `COLLECT`.
3. Mengasosiasikan tipe file video populer agar dapat dibuka langsung oleh VidStamp di macOS via `Info.plist` (melalui opsi `info_plist` pada generator `BUNDLE`).

---

## 3. Otomatisasi Pembuatan Installer Disk Image (`.dmg`)
Untuk memudahkan proses distribusi, berkas `.app` akan dibungkus menjadi berkas `.dmg` satu-file yang ramah pengguna. 

### 3.1. Spesifikasi Visual Installer .dmg
Volume `.dmg` yang dihasilkan wajib menyajikan antarmuka grafis yang memandu pengguna untuk menyeret ikon **VidStamp.app** ke dalam pintasan folder **/Applications** (standard drag-and-drop installer).
Hal ini dicapai dengan menggunakan perkakas command-line open-source **`create-dmg`**.

### 3.2. Parameter Perintah `create-dmg`
Berikut adalah parameter yang akan digunakan:
* `--volname`: "VidStamp Installer"
* `--volicon`: Menyertakan ikon `.icns` untuk volume disk image itu sendiri.
* `--window-size 800 400`: Ukuran jendela installer yang proporsional.
* `--icon-size 100`: Ukuran ikon aplikasi dan pintasan folder agar mudah dilihat.
* `--icon "VidStamp.app" 200 190`: Koordinat posisi ikon aplikasi di sebelah kiri.
* `--app-drop-link 600 190`: Koordinat posisi pintasan folder `/Applications` di sebelah kanan.
* Output file: `dist/VidStamp_Setup.dmg`

---

## 4. Alur Kerja Otomatisasi CI/CD (GitHub Actions)
Mengingat keterbatasan pengembangan di mesin lokal Windows, build macOS wajib diotomatisasi melalui **GitHub Actions**.

### 4.1. Spesifikasi Runner
* **OS**: `macos-latest` (disediakan oleh GitHub runner, mendukung Xcode tools dan macOS native build).

### 4.2. Tahapan Build Workflow
1. **Checkout Code**: Melakukan kloning repositori.
2. **Setup Python**: Mengonfigurasi lingkungan Python 3.10 ke atas.
3. **Instalasi Dependensi**: Menginstal modul Python dari `requirements.txt` ditambah `pyinstaller`.
4. **Instalasi Biner FFmpeg/FFprobe macOS**:
   Mengunduh biner FFmpeg & FFprobe statis versi macOS dekompresi dari penyedia tepercaya (seperti `ffbinaries` API) dan menempatkannya ke dalam folder `bin/mac/` sebelum PyInstaller dijalankan.
5. **Kompilasi PyInstaller**: Mengeksekusi `pyinstaller --clean -y vidstamp.spec`.
6. **Pembuatan berkas `.dmg`**:
   - Menginstal `create-dmg` via Homebrew (`brew install create-dmg`).
   - Mengeksekusi pembuatan berkas `.dmg` dari bundel `.app` yang terletak di folder `dist/`.
7. **Unggah Aset Artifact/Release**: Menyimpan berkas `.dmg` yang berhasil dikompilasi sebagai GitHub artifact atau melampirkannya langsung ke rilis GitHub baru jika dipicu oleh tag versi.

---

## 5. Pengujian & Kepatuhan Keamanan
1. **Verifikasi Sintaks**: Memastikan penambahan modul `BUNDLE` di `vidstamp.spec` tidak menyebabkan regresi sintaks saat dikompilasi di Windows.
2. **Keamanan Kredensial**: Memastikan berkas konfigurasi lokal sensitif (seperti `.env`) dikecualikan sepenuhnya dari pengemasan di macOS App Bundle. Pengambilan kredensial dilakukan secara aman di memori RAM melalui Cloudflare R2 API.
