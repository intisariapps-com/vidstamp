# Jurnal Sesi & Riwayat Aktivitas

Log kronologis aktivitas harian sesi pengembangan.

## 2026-07-26 - Sesi Inisialisasi & Fitur Pintar VidStamp
* **Aktivitas**: 
  - Restrukturisasi total kode dari berkas tunggal menjadi arsitektur modular profesional di bawah paket `vidstamp/` (MVC structure).
  - Penambahan parent-path dinamis di `__main__.py` untuk memperbaiki error `ModuleNotFoundError` PYTHONPATH saat dijalankan dari subdirektori.
  - Peningkatan performa video super mulus (stutter-free) dengan menaikkan toleransi sync audio ke 6 frame dan INTER_NEAREST canvas rendering.
  - Implementasi detektor berkas subtitle `.srt` eksternal otomatis berdasarkan kesamaan nama video di direktori.
  - Pengembangan fitur penandaan dan Auto-Skip Opening/Ending (OP/ED) anime dengan dukungan template folder per season (`season_skip_template.json`).
  - Inisialisasi struktur memori dan dokumen kontrol `Agent.md` proyek via `/init-project`.
  - Penyesuaian `Agent.md` dan `memory/features_roadmap.md` untuk menyertakan visi masa depan: Peningkatan UI/UX (CustomTkinter) serta integrasi compiler biner `.exe` (Windows + Setup Installer) dan `.dmg` (macOS).
  - Penambahan fitur indikator durasi detik berjalan (REC) secara real-time pada video canvas dan status bar ketika pintasan Ctrl+T (perekaman adegan) diaktifkan.
  - Penyiapan arsitektur bundling: membuat `path_helper.py` untuk deteksi `sys._MEIPASS`, memodifikasi `subtitle.py` untuk pemanggilan FFmpeg dinamis, dan menyiapkan file spesifikasi PyInstaller `vidstamp.spec` beserta struktur direktori kontainer `bin/win/` dan `bin/mac/`.
  - Pembaruan berkas `.gitignore` untuk mencegah masuknya berkas kompilasi (`build/`, `dist/`), biner FFmpeg lokal (`bin/`), dan installer setup (`VidStamp_Setup.exe`) ke repositori Git.
  - Implementasi fitur Resume Playback yang secara otomatis mengingat dan memulihkan posisi video terakhir dari file `playback_state.json` (termasuk auto-save berkala tiap 5 detik).
  - Implementasi fitur Sinkronisasi & Auto-Update catatan adegan terstruktur (`scenes.json`) dan format teks (`_catatan_adegan.txt`) secara real-time saat adegan disimpan atau dihapus.
* **Status**: Sukses besar, fitur Resume Playback dan Auto-Update Catatan berjalan stabil serta siap untuk kompilasi rilis berikutnya.
* **Langkah Selanjutnya**: Menunggu penutupan sesi atau pengujian build biner terbaru.

