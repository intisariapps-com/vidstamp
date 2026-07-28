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
  - Mengintegrasikan path absolut video (`Video Abs Path`) dan path folder catatan (`Note Folder Path`) secara detail pada berkas ekspor `_catatan_adegan.txt` agar tersinkronisasi otomatis dengan Gemini Custom (Intisari Viral Lens) dan Ekstensi Chrome (Intisari Extractor).
* **Status**: Sukses besar, optimasi performa pemutaran, integrasi format waktu hitung mundur, dokumen PRD, dan sinkronisasi path absolut catatan adegan telah selesai dirancang dan disimpan.
* **Langkah Selanjutnya**: Pengujian integrasi pemotongan video end-to-end menggunakan berkas ekspor teks, serta persiapan migrasi UI CustomTkinter.

## 2026-07-28 - Sesi Integrasi Deteksi Bab MKV Otomatis & Fitur Ekspor Video Bersih
* **Aktivitas**:
  - Menganalisis skrip `mkv_merger_skip_oped.py` yang berada di drive `E:\` untuk mengonseptualisasikan fitur baru.
  - Membuat berkas Spesifikasi Kebutuhan Perangkat Lunak (SRS) di `docs/srs/integrasi_mkv_chapters_dan_export_clean.md` dan melakukan commit awal ke repositori.
  - Memodifikasi `vidstamp/utils/path_helper.py` untuk mengintegrasikan deteksi biner `ffprobe` yang kompatibel dengan PyInstaller.
  - Membangun modul inti baru `vidstamp/core/exporter.py` yang menangani pembacaan bab MKV (chapters), kalkulasi segmen simpan/skip, pembacaan, pergeseran, dan penyelarasan subtitel (.srt) secara presisi, serta pemicu render FFmpeg.
  - Mengintegrasikan fungsi deteksi bab MKV otomatis pada `load_video()` di `vidstamp/ui/main_window.py`. Jika video berekstensi `.mkv` tidak memiliki skip config, program akan memindai chapter metadata di latar belakang dan mengisi waktu skip secara otonom.
  - Mendesain dialog opsi ekspor baru (`setup_export_clean_dialog`) di `vidstamp/ui/player_view.py` untuk memilih mode subtitel (Hardsub vs Softsub) dan cakupan pemrosesan (Satu file vs Bulk folder).
  - Mengembangkan visualisasi progress bar (`show_export_progress_window`) berbasis Threading non-blocking di Tkinter yang melacak kemajuan render FFmpeg per detik secara real-time dan mendukung pembatalan (Cancel).
  - Memperbarui dokumentasi memori proyek (`memory/features_existing.md`) dengan fitur-fitur baru yang telah stabil ini.
* **Status**: Sukses besar, fitur deteksi bab otomatis dan ekspor video bersih berjalan sangat lancar dan responsif tanpa memblokir antarmuka utama (UI).
* **Langkah Selanjutnya**: Evaluasi kinerja ekspor massal untuk folder berskala besar.

## 2026-07-28 - Sesi Konfirmasi Jalur Pengembangan Utama (Kembali ke Tkinter Klasik Stabil)
* **Aktivitas**:
  - Melakukan uji coba perombakan arsitektur PySide6 / Companion App MPC-HC pada branch terpisah (`feat-pyside6-gui`).
  - Setelah evaluasi mendalam, diputuskan secara strategis untuk **kembali menggunakan dan melanjutkan pengembangan pada basis kode Tkinter klasik yang stabil** (`main-old-base-fixed`).
  - Memperbarui memori proyek untuk mencatat arah pengembangan masa depan yang berfokus pada Tkinter klasik, optimasi performa pemutar video internal OpenCV, dan perluasan fitur-fitur pintar.
* **Status**: Sukses besar, repositori lokal berada di branch `main-old-base-fixed` yang bersih, stabil, dan siap dikembangkan lebih lanjut.
* **Langkah Selanjutnya**: Melanjutkan backlog fitur (Whisper API / database AniSkip) langsung di atas basis Tkinter klasik stabil.




