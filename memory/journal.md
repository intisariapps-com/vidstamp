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

## 2026-07-28 (Lanjutan) / 2026-07-29 - Sesi Restrukturisasi Tata Letak Bersih & Peningkatan Fitur Batch Merger Paralel
* **Aktivitas**:
  - **Restrukturisasi Tata Letak Bersih**: Menghapus panel penjelajah folder kiri (`LeftBrowserPanel`), mempack panel utama (`RightPlayerPanel`) memenuhi 100% lebar jendela utama, dan menambahkan tombol "📁 Buka Folder" & "📄 Buka Video" di menu bar atas.
  - **Dropdown Episode Dinamis**: Menambahkan dropdown Combobox "🎬 Video:" di menu atas untuk memudahkan penonton berpindah antar video/episode dalam folder aktif.
  - **Tombol Menu Peralatan Kanan Atas**: Menambahkan tombol "🛠️ Peralatan ▾" melayang yang memicu popup menu native Tkinter untuk akses cepat ke Batch Merger, Ekstraktor, dan pembukaan folder catatan adegan di Windows Explorer.
  - **Perbaikan Bug Menu Bar Windows**: Menghapus pewarnaan kustom tidak standar dari `tk.Menu` untuk mengembalikan rendering native Windows, mematikan bug menu "tidak tiba" (tidak merespons/teks tersembunyi).
  - **Kustomisasi Subtitel Hardsub**: Menambahkan dropdown Ukuran Font Hardsub (lewat filter `subtitles` FFmpeg `:force_style='Fontsize=X'`) dan dropdown Batas Panjang Baris (menggunakan fungsi auto-wrap teks seimbang di Python agar teks tidak terpotong di rasio 1:1 Instagram).
  - **Multi-tasking & Paralel Render Tanpa Konflik**: Mengubah dialog wizard merger dan ekstraktor menjadi non-modal, menambahkan tombol "➕ Jendela Baru" untuk menduplikasi jendela merger secara dinamis, dan menambahkan generator kode unik UUID acak untuk penamaan seluruh berkas temporer (`temp_clean_ep...`, `mylist_temp_...`, `temp_extract_...`) agar proses render paralel berjalan aman tanpa tabrakan file.
  - **UX & Manajemen Antrean Merger**: Menghindari penutupan wizard otomatis pasca-sukses dengan me-reset status UI secara langsung. Menambahkan fitur hapus video terpilih dari antrean merger (tombol visual dan tombol keyboard `Delete`), serta menyelaraskan list file sisa ke backend render.
  - **Penyempurnaan Visual & Bug Fix**: Memperbaiki visual bug tata letak tombol hapus dengan memposisikan parent Treeview secara tepat ke `tree_container` di bawah `table_frame`. Memperbaiki `NameError: filedialog is not defined` di `main_window.py`. Mengubah urutan reset status `self.processing` agar berjalan sebelum pemblokiran modal messagebox sukses.
* **Status**: Sukses besar, antarmuka VidStamp jauh lebih bersih dan premium, serta Batch Merger Wizard kini sangat andal untuk rendering paralel banyak folder secara bersamaan.
* **Langkah Selanjutnya**: Evaluasi performa pembakaran subtitle untuk font dan gaya bahasa kustom lainnya.

## 2026-07-28 - Sesi Konfirmasi Jalur Pengembangan Utama (Kembali ke Tkinter Klasik Stabil)
* **Aktivitas**:
  - Melakukan uji coba perombakan arsitektur PySide6 / Companion App MPC-HC pada branch terpisah (`feat-pyside6-gui`).
  - Setelah evaluasi mendalam, diputuskan secara strategis untuk **kembali menggunakan dan melanjutkan pengembangan pada basis kode Tkinter klasik yang stabil** (`main-old-base-fixed`).
  - Memperbarui memori proyek untuk mencatat arah pengembangan masa depan yang berfokus pada Tkinter klasik, optimasi performa pemutar video internal OpenCV, dan perluasan fitur-fitur pintar.
* **Status**: Sukses besar, repositori lokal berada di branch `main-old-base-fixed` yang bersih, stabil, dan siap dikembangkan lebih lanjut.

## 2026-07-29 - Sesi Bundling macOS, Workspace Workflows & Sistem Manajemen Versi Terpusat
* **Aktivitas**:
  - **Spesifikasi Bundling macOS**: Merancang dan menulis dokumen spesifikasi teknis SRS di [spesifikasi_bundling_macos.md](file:///d:/VIDSTAMPS-APPS/docs/srs/spesifikasi_bundling_macos.md) beserta rencana implementasinya.
  - **Otomatisasi Build macOS**:
    - Memodifikasi berkas [vidstamp.spec](file:///d:/VIDSTAMPS-APPS/vidstamp.spec) untuk menyertakan `ffprobe` (Windows & macOS) dan menambahkan konfigurasi `BUNDLE` macOS kondisional.
    - Membuat skrip build portabel [build_macos.sh](file:///d:/VIDSTAMPS-APPS/bin/build_macos.sh) yang secara dinamis mengunduh FFmpeg/FFprobe macOS, merender ikon `.icns` dari PNG via `sips`/`iconutil`, dan membungkus `.app` menjadi `.dmg` installer dengan `create-dmg`.
    - Membuat berkas konfigurasi GitHub Actions [build-macos.yml](file:///d:/VIDSTAMPS-APPS/.github/workflows/build-macos.yml) untuk build cloud otonom di runner `macos-latest`.
  - **Workspace Workflows Baru**: Membuat 3 berkas alur kerja (slash command) kustom di `.agents/workflows/`: [run-test.md](file:///d:/VIDSTAMPS-APPS/.agents/workflows/run-test.md), [build-app.md](file:///d:/VIDSTAMPS-APPS/.agents/workflows/build-app.md), dan [sync-docs.md](file:///d:/VIDSTAMPS-APPS/.agents/workflows/sync-docs.md).
  - **Sistem Manajemen Versi Terpusat (Central Versioning)**:
    - Membuat berkas [version.json](file:///d:/VIDSTAMPS-APPS/version.json) di root sebagai *source of truth* versi aplikasi.
    - Membuat berkas utilitas [update_version.py](file:///d:/VIDSTAMPS-APPS/update_version.py) untuk menyinkronkan versi central ke metadata paket, label versi launcher, window title player, dan nama setup installer.
    - Mengintegrasikan skrip pembaruan versi ini ke langkah awal workflow `/build-app`.
    - Mendokumentasikan spesifikasi arsitekturnya di [spesifikasi_manajemen_versi_terpusat.md](file:///d:/VIDSTAMPS-APPS/docs/srs/spesifikasi_manajemen_versi_terpusat.md).
  - **Verifikasi & Eksekusi Kompilasi**:
    - Menjalankan pengujian unit pytest lokal pra-build (6 passed, 2 skipped).
    - Menjalankan `/build-app` yang memicu pembaruan versi, kompilasi PyInstaller, dan build Inno Setup secara otonom menghasilkan installer Windows `VidStamp_Setup_v1.3.0.exe` (~146MB) dengan sukses di root.
* **Status**: Sukses besar, sistem manajemen versi terpusat, pengemasan macOS, dan otomatisasi installer Windows/macOS telah diselesaikan dan berjalan dengan stabil.
* **Langkah Selanjutnya**: Melakukan push commit ke GitHub remote untuk memicu pengujian build macOS di Actions secara cloud.

## 2026-07-29 - Sesi Perbaikan Bug Merger, Sistem Pintasan Baru, & Optimasi Fullscreen
* **Aktivitas**:
  - **Perbaikan Concat Merger**: Memperbaiki error `4294967268` / `-28` (`ENOSPC` - Penyimpanan penuh / batas FAT32) dengan memigrasi daftar file concat (`mylist_temp_*.txt`) menggunakan relative path alih-alih path absolut, yang sekaligus mencegah kegagalan FFmpeg akibat spasi/unicode pada folder kerja induk. Menambahkan penangkapan stderr dan notifikasi informatif jika terjadi disk full.
  - **Otomatisasi Build Windows (`build.py`)**: Membuat skrip pembangun lokal `build.py` untuk mengotomatiskan jalannya `update_version.py`, `pytest`, `pyinstaller`, dan `ISCC.exe` sekali jalan.
  - **Sistem Pintasan Keyboard Terpusat**:
    - Memigrasi tombol perekam adegan dari `Ctrl+T` ke `Ctrl+R`.
    - Menambahkan pintasan perekam Opening (`Ctrl+O`) dan Closing (`Ctrl+C`) dengan mekanisme toggle 1-tombol (tekan 1 set start, tekan 2 set end & simpan).
    - Menerapkan proteksi fokus ketik (`_is_typing_focus()`) agar shortcuts ini tidak mengganggu copy/paste (`Ctrl+C`) atau ketikan normal saat kursor berada di input field (Entry/Text).
  - **Penyatuan Pengaturan ke Menu Peralatan (Decluttering)**: Memindahkan seluruh checkbox kontrol visual (`Tampilkan Timestamp`, `Milidetik`, `Subtitel Overlay`, `Auto-Skip OP/ED`) dan tombol `Set Skip OP/ED` dari `top_bar` ke dalam menu dropdown `Peralatan`. Membuat `top_bar` menjadi sangat minimalis dan bersih.
  - **Tampilan Kontrol Fullscreen yang Interaktif**: Menambahkan fitur toggle panel kontrol (`top_bar`, `seek_frame`, `ctrl_panel`, `inf_bar`) di mode fullscreen dengan menekan tombol **`Tab`** atau melakukan **Klik Kiri (Left Click)** pada video canvas. Play/pause di mode fullscreen dialihkan sepenuhnya ke tombol **`Space`** untuk menghindari konflik.
  - **Retensi Gaya Subtitel ASS Asli Bawaan MKV**: Memperbaiki sistem ekspor hardsub lama yang merusak styling subtitel dengan mereduksi format ke plain SRT. Sistem baru secara otonom mengekstrak format `.ass` asli, menyelaraskan waktu Dialogue tanpa menyentuh styles header/tags, dan menggunakannya untuk proses pembakaran FFmpeg. Hal ini memastikan seluruh tipe font, warna, ukuran, dan posisi typesetting anime bawaan MKV dipertahankan secara sempurna di hasil ekspor tanpa mempengaruhi kebersihan berkas catatan adegan/rekaman `.srt` yang tetap polos.
* **Status**: Sukses besar, seluruh unit test lulus (6 passed, 2 skipped), dan aplikasi berjalan secara optimal dengan performa mulus dan retensi visual yang menawan.


