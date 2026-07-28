# Peta Jalan Fitur & Backlog

Daftar fitur, peningkatan, atau perbaikan yang akan dikerjakan ke depannya pada proyek VidStamp.

## 🎨 Peningkatan Tampilan (UI/UX Modern)
* [ ] **Modernisasi Widget (CustomTkinter)**: Migrasi dari Tkinter klasik bawaan ke library CustomTkinter untuk menghasilkan desain antarmuka gelap (Dark Mode) modern, bersudut tumpul (rounded corners), slider yang halus, dan kontras warna premium secara default.
* [ ] **Mikro-Animasi Hover**: Menambahkan animasi hover interaktif pada tombol pemutar, slider, dan item list adegan.

## 📦 Kompilasi & Distribusi Desktop (.exe / .dmg)
* [x] **Bundling Windows (`.exe`)**:
  * [x] Menyiapkan file konfigurasi PyInstaller `.spec`.
  * [x] Menguji bundel *one-folder* (`COLLECT`) dengan penyertaan aset biner FFmpeg.
  * [x] Membuat skrip installer instan (Setup) menggunakan Inno Setup (`installer_windows.iss`).
* [x] **Bundling macOS (`.dmg`)**:
  * [x] Mengompilasi aplikasi ke bundel `.app` di lingkungan macOS.
  * [x] Mengemas bundel `.app` menjadi berkas installer `.dmg` dengan latar belakang grafis pemandu drag-and-drop.

## 🎯 Prioritas Utama (Backlog Fitur)
* [ ] **Integrasi API Groq Whisper**: Transkripsi audio hasil ekstrak (`.mp3`/`.wav`) ke format subtitle `.srt` otomatis yang sinkron dengan video secara pintar.
* [ ] Integrasi database anime online (API AniSkip) untuk auto-fetch durasi OP/ED anime populer secara langsung tanpa setting manual.
* [ ] Ekstraksi trek subtitle lebih dari satu (multilingual subtitle track selection).
* [ ] Fitur preview thumbnail di seek bar saat pointer hover di atasnya.

