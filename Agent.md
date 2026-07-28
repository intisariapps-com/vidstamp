# Panduan Proyek: VidStamp

Dokumen ini berfungsi sebagai panduan utama persona, arsitektur, dan aturan pengembangan untuk AI dan pengembang di proyek ini.

> **🗺️ PROTOKOL WAJIB AI**: Sebelum membuat atau mengubah kode apapun, baca terlebih dahulu file **`.agents/CODEBASE.md`**. File tersebut berisi peta lengkap seluruh modul, fungsi, state variable, dan dependency antar file — sehingga AI tidak perlu membuka file sumber satu per satu untuk memahami arsitektur. Hemat token, kerja efisien.

---

## 1. Panduan Persona AI
* **Bahasa**: Selalu gunakan Bahasa Indonesia yang profesional, santun, dan formal.
* **Keamanan Kredensial Desktop (Wajib)**:
  * **Tahap Pengembangan**: File `.env` hanya digunakan untuk pengembangan lokal.
  * **Tahap Produksi (Build .exe/.app)**: JANGAN PERNAH membundel berkas `.env` ke dalam executable. Gunakan metode **Remote Config Fetching (In-Memory)** menggunakan Cloudflare R2 (`https://data.intisariapps.com/v1/env`) untuk memuat kredensial/API Key langsung ke RAM saat boot-up tanpa menulis ke disk.
* **Kualitas Desain (Rich Aesthetics - Standar MPC-HC)**:
  * **Framework UI**: Wajib bermigrasi dari Tkinter standar ke **CustomTkinter** untuk menghapus tampilan visual kaku dengan sudut melengkung (*rounded corners*), warna gelap terpadu, dan transisi halus.
  * **Tata Letak Ala MPC-HC**: Mengadopsi tata letak pemutar media profesional:
    * **Compact Control Bar**: Menggabungkan seek bar, volume, penanda waktu, dan tombol kontrol navigasi (menggunakan simbol unicode minimalis) dalam satu baris tipis di bawah video.
    * **Drag & Drop**: Mendukung drag-and-drop file video dari Windows Explorer langsung ke canvas pemutar.
    * **Context Menu**: Klik kanan pada layar video memunculkan pop-up menu pintasan cepat.

* **Pemeliharaan Komentar**: Jangan menghapus komentar asli, docstring, atau kode lama tanpa persetujuan eksplisit.

---

## 2. Arsitektur Proyek
Aplikasi ini bernama **VidStamp** (Video Timestamp & Marker) yang dikembangkan dengan arsitektur modular proper berbasis Python:

* **Entry Point**: `python -m vidstamp` (mengeksekusi `vidstamp/__main__.py`).
* **vidstamp/core/**: Logika inti non-GUI.
  * `player.py`: Integrasi sinkron OpenCV dan `ffpyplayer` audio engine.
  * `subtitle.py`: Ekstraksi subtitle mkv via FFmpeg subprocess dan parser srt eksternal.
* **vidstamp/ui/**: Antarmuka Tkinter.
  * `main_window.py`: Controller/koordinator window utama dan loop pemutaran.
  * `browser.py`: Panel kiri navigasi folder & pencarian berkas video.
  * `player_view.py`: Panel kanan canvas rendering, controls, dialog, dan catatan adegan.
* **vidstamp/utils/**: Helper pembantu.
  * `time_formatter.py`: Formatting detik float.
  * `text_cleaner.py`: Pengolah teks (4 kata judul).
  * `file_manager.py`: Manajemen direktori ekspor catatan dan konfigurasi auto-skip OP/ED.

---

## 3. Sistem Operasi & Lingkungan & Cabang Git (Git Branching)
* **Sistem Operasi**: Windows (PowerShell) & macOS (untuk target build `.dmg`)
* **Direktori Workspace**: `e:\ANIME\`
* **Aturan Cabang Git (MANDATORI)**:
  * **Cabang Pengembangan Aktif (`dev`)**: Segala bentuk modifikasi kode, eksperimen, penulisan fitur, dan perbaikan bug WAJIB dilakukan di branch `dev`.
  * **Cabang Produksi/Stabil (`main`)**: Branch `main` dilindungi secara ketat dan hanya berisi versi rilis yang sudah stabil dan lolos uji (production-ready). JANGAN PERNAH mengubah file kode, melakukan pengujian langsung, atau commit di branch `main`.
  * **Proteksi AI**: Jika AI mendeteksi sedang berada di branch `main`, AI wajib memperingatkan pengguna dan secara otonom beralih ke branch `dev` (`git checkout dev`) sebelum melanjutkan pekerjaan.
* **Manajemen Sesi**:
  * **Mulai Sesi (`/session-start`)**: AI memverifikasi status Git secara proaktif (memastikan berada di branch `dev` yang sinkron dengan remote), membaca `memory/README.md` dan file memori pendukung untuk memulihkan konteks kerja.
  * **Tutup Sesi (`/session-end`)**: AI memperbarui `memory/journal.md`, `memory/features_existing.md`, dan `memory/features_roadmap.md`, lalu melakukan commit & push ke branch `dev`.

---

## 4. Protokol Pengembangan & Dokumentasi
1. **Auto-SRS & Auto-Commit**:
   * Setiap kali ada kesepakatan perubahan arsitektur atau fitur baru, AI wajib membuat/memperbarui file spesifikasi di folder `docs/srs/` secara otomatis.
   * Lakukan commit git awal untuk file SRS tersebut sebelum mulai menulis kode implementasi:
     ```bash
     git add docs/srs/
     git commit -m "docs(srs): perbarui spesifikasi [nama fitur]"
     ```
2. **Mentalitas TDD (Test-First)**:
   * Buat *test suite* atau skenario uji terlebih dahulu sebelum membangun integrasi API yang kompleks.
   * Lakukan *mocking* untuk semua operasi eksternal agar aman.

---

## 5. Protokol Build & Distribusi Aplikasi Desktop
Untuk merilis aplikasi ini sebagai executable mandiri yang dapat digunakan oleh pengguna awam:
* **Target Windows (`.exe` & Installer)**:
  * Gunakan **PyInstaller** untuk mengompilasi kode program menjadi berkas biner mandiri.
  * Sertakan aset non-Python (seperti ikon `.ico` dan dependensi biner FFmpeg) menggunakan opsi `--add-data`.
  * Bungkus hasil dist PyInstaller ke dalam file Setup/Installer yang profesional menggunakan **Inno Setup** atau **NSIS**.
* **Target macOS (`.app` & `.dmg`)**:
  * Gunakan **py2app** atau PyInstaller di lingkungan macOS asli untuk mengompilasi bundel `.app`.
  * Gunakan tool **create-dmg** untuk mengemas bundel `.app` ke dalam bentuk biner `.dmg` installer dengan latar belakang instruksi drag-and-drop khas macOS.
  * Semua rahasia/token wajib dilindungi menggunakan arsitektur *Remote Config Fetching* di memori RAM.

