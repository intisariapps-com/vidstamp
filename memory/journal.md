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

## 2026-07-27 - Sesi Perombakan UI/UX, Crash Logger Global, & Perbaikan Aspek Rasio/Video Korup
* **Aktivitas**:
  - Menyalin file workflow `session-start` dan `session-end` secara otomatis dari direktori global ke `.agents/workflows/`.
  - Merancang dan menyelesaikan perombakan UI/UX premium modern menggunakan **CustomTkinter** (termasuk Drag & Drop video, context menu klik kanan, dan tombol Registrasi Default Player) dan mempushnya ke remote branch `main`.
  - Melakukan rollback basis kode lokal ke versi lama (`1d0935e`) sesuai instruksi user, dan membuat branch baru **`main-old-base-fixed`** untuk perbaikan bug versi awal.
  - Memperbaiki kesalahan *segmentation fault* (crash native) saat memuat video Kusonime yang korup dengan mengimplementasikan mekanisme **Deferred Resume Playback (penundaan 350ms)** menggunakan Tkinter `.after()` sebelum memanggil seek.
  - Memperbaiki bug visual aspek rasio video di mana video tetap berukuran kecil dan menempel di kiri atas Canvas saat jendela dimaksimalkan (*maximized*). Solusi: Menggunakan `update_idletasks()`, memperbaiki logika fallback dimensi, dan mengikat (*bind*) event `<Configure>` agar video membesar secara dinamis dan selalu diposisikan tepat di tengah (*centered*).
  - Mengembangkan sistem **Crash Logger Global** di `vidstamp/utils/logger.py` untuk menangkap semua uncaught exception (`sys.excepthook`) dan kesalahan Tkinter callback loop (`report_callback_exception`), lalu mencatatnya secara terstruktur ke berkas lokal **`crash.log`** serta menampilkan messagebox pemberitahuan yang ramah pengguna.
  - Mengunggah seluruh perbaikan di atas ke remote branch baru `main-old-base-fixed` di GitHub.
  - Melakukan kompilasi executable mandiri terbaru menggunakan **PyInstaller** dengan spec `vidstamp.spec` (dengan DLL ffpyplayer/SDL2 dan biner FFmpeg Windows terintegrasi).
  - Membangun berkas installer resmi Windows **`VidStamp_Setup.exe`** (~125MB) menggunakan **Inno Setup** setelah menyesuaikan konfigurasi bahasa (menggunakan bahasa Inggris sebagai default karena tidak adanya paket lokalisasi Indonesia `.isl` pada mesin build lokal).
  - Mengatasi masalah video patah-patah (stuttering) saat dijalankan sebagai EXE dengan: (1) menghapus `update_idletasks()` di loop render `player_view.py` untuk mengeliminasi blocking layout sync, dan (2) mengganti kueri properti sinkron OpenCV `cap.get(cv2.CAP_PROP_POS_FRAMES)` dengan pelacakan indeks frame manual in-memory (`self.cur_idx`) di `player.py`.
  - Merumuskan berkas Product Requirement Document (PRD) di `docs/prd.md` yang memperluas visi, fitur, dan peta jalan pengembangan (seperti rencana integrasi API AniSkip dan modernisasi UI CustomTkinter).
* **Status**: Sukses besar, optimasi performa pemutaran, integrasi format waktu hitung mundur, dan dokumen PRD telah selesai dirancang dan disimpan.
* **Langkah Selanjutnya**: Melakukan pengujian lanjutan pada video-video anime lama dengan konfigurasi skip OP/ED otomatis, serta persiapan migrasi UI CustomTkinter.


