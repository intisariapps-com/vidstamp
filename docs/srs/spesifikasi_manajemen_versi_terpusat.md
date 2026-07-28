# Spesifikasi Kebutuhan Perangkat Lunak (SRS): Sistem Manajemen Versi Terpusat (Central Versioning)

## 1. Pendahuluan
Saat mengompilasi dan merilis aplikasi desktop seperti **VidStamp**, terdapat kebutuhan untuk memperbarui string versi aplikasi di berbagai tempat (kode sumber, UI launcher, window title, konfigurasi PyInstaller, dan skrip installer Windows Inno Setup). 

Memperbarui string versi secara manual pada banyak berkas rentan terhadap kesalahan manusia (*human error*), seperti inkonsistensi versi antara installer dan aplikasi yang terinstal. Dokumen ini menetapkan spesifikasi sistem otomatisasi pembaruan versi terpusat (*Central Versioning System*).

---

## 2. Mekanisme Arsitektur
Sistem ini menggunakan satu berkas JSON terpusat sebagai *source of truth* untuk informasi versi aplikasi, yang disebarkan ke berkas target menggunakan skrip pembantu Python sebelum proses build dimulai.

```
                  ┌──────────────┐
                  │ version.json │ (Source of Truth)
                  └──────┬───────┘
                         │
                         ▼
               ┌───────────────────┐
               │ update_version.py │ (Skrip Pemroses)
               └─┬───┬───────────┬─┘
                 │   │           │
      ┌──────────┘   │           └──────────┐
      ▼              ▼                      ▼
┌────────────┐ ┌─────────────┐       ┌──────────────┐
│  __init__.py│ │ launcher.py │       │  main_window.py│
└────────────┘ └─────────────┘       └──────────────┘
                     │                      │
                     ▼                      ▼
               ┌─────────────┐       ┌──────────────┐
               │  versi label│       │  window title│
               └─────────────┘       └──────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │   installer_windows.iss   │
       └───────────────────────────┘
```

### 2.1. Berkas Konfigurasi (`version.json`)
Berkas JSON ini terletak di root repositori dan menyimpan informasi:
* `version`: Versi aplikasi standar semantik (contoh: `"1.3.0"`).
* `build_number`: Angka pengenal build.
* `app_name`: Nama aplikasi resmi ("VidStamp").

---

## 3. Spesifikasi Berkas Target yang Disinkronkan
Skrip `update_version.py` bertugas memindai dan memperbarui string versi pada lokasi berikut:

### 3.1. Metadata Paket (`vidstamp/__init__.py`)
Menulis variabel `__version__ = "[VERSION]"` secara otonom sehingga pustaka Python internal dan eksternal dapat melakukan kueri versi secara native.

### 3.2. Jendela Launcher (`vidstamp/ui/launcher.py`)
Mencari teks label versi di bagian bawah jendela launcher (menggunakan pencocokan pola regex `text="v[0-9\.]+"`) dan menggantinya dengan versi terbaru agar pengguna dapat melihat versi build aktif saat boot.

### 3.3. Jendela Utama (`vidstamp/ui/main_window.py`)
Memodifikasi judul jendela utama agar menyertakan versi aktif:
* Format: `VidStamp v[VERSION] - Video Timestamp & Scene Marker`

### 3.4. Skrip Setup Installer (`installer_windows.iss`)
* Memperbarui parameter `AppVersion=[VERSION]`.
* Memperbarui nama berkas biner installer yang dihasilkan agar dinamis:
  `OutputBaseFilename=VidStamp_Setup_v[VERSION]` (Menghasilkan `VidStamp_Setup_v1.3.0.exe`).

---

## 4. Alur Integrasi pada Workflow Kompilasi
Langkah sinkronisasi versi ini diintegrasikan sebagai **langkah paling awal (step 1)** pada alur kerja `/build-app` (dan di masa depan pada GitHub Actions workflow) sebelum unit test dijalankan dan PyInstaller mulai mengemas biner.
 Hal ini memastikan seluruh file biner dan installer yang dibuat selalu sinkron dengan versi target di `version.json`.
