# Fitur Terimplementasi (Existing)

Berikut adalah daftar fitur yang sudah selesai dibangun dan berstatus stabil di proyek VidStamp.

## 1. Fondasi Proyek
* **Deskripsi**: Struktur direktori dasar, konfigurasi Git, manajemen sesi modular, dan runner runner minimalis.
* **Status**: Selesai

## 2. Mesin Pemutus Video Companion App MPC-HC (REST HTTP API)
* **Deskripsi**: Mengendalikan media player eksternal MPC-HC secara asinkron menggunakan klien HTTP bawaan Python (`mpc_client.py`) yang ringan. Status pemutaran, timeline detik aktif, dan durasi disinkronkan secara real-time melalui polling QTimer (200ms) di tingkat window utama.
* **Status**: Selesai

## 3. Rendering Mulus 100% Bebas CPU Overhead
* **Deskripsi**: Seluruh pemrosesan decoding pixel video OpenCV dan audio track engine ffpyplayer internal Python dihilangkan secara total. Proses rendering sepenuhnya dialihkan ke MPC-HC eksternal dengan akselerasi GPU bawaan, menjamin tontonan berjalan mulus tanpa lag.
* **Status**: Selesai

## 4. Deteksi Subtitle Eksternal (.srt) Otomatis
* **Deskripsi**: Mendeteksi file subtitle `.srt` dengan nama yang cocok di direktori video sebelum memicu fallback ekstraksi subtitle internal dari video `.mkv` menggunakan FFmpeg.
* **Status**: Selesai

## 5. Perekam Catatan Adegan & Shortcuts
* **Deskripsi**: Fitur mencatat adegan menggunakan `Ctrl+T` (recorder style) dan mengekspor adegan ber-subtitle ke dalam folder khusus video dengan nama default pintar.
* **Status**: Selesai

## 6. Auto-Skip Opening & Ending (OP/ED)
* **Deskripsi**: Skip otomatis jika waktu pemutaran video menyentuh batas awal lagu OP/ED. Mendukung template season `season_skip_template.json` sehingga set sekali berlaku untuk semua episode.
* **Status**: Selesai

## 7. Indikator Detik Berjalan (Record Duration)
* **Deskripsi**: Menampilkan indikator durasi berjalan (REC) secara real-time pada video canvas overlay dan status bar saat perekaman adegan (Ctrl+T) aktif.
* **Status**: Selesai

## 8. Resume Playback (Lanjutkan Pemutaran)
* **Deskripsi**: Menyimpan posisi detik terakhir pemutaran video aktif ke playback_state.json dan memulihkannya secara otomatis saat video dibuka kembali (termasuk auto-save berkala tiap 5 detik).
* **Status**: Selesai

## 9. Sinkronisasi & Auto-Update Catatan Adegan
* **Deskripsi**: Menyimpan daftar adegan terstruktur ke database scenes.json dan menulis ulang file teks catatan adegan (.txt) secara otomatis setiap kali ada catatan baru yang disimpan atau dihapus.
* **Status**: Selesai

## 10. Setup Bundling Desktop & Installer (Windows)
* **Deskripsi**: Menyediakan file konfigurasi PyInstaller (vidstamp.spec), folder penampung biner FFmpeg portable (bin/), aset ikon visual kustom (.ico/.bmp), dan skrip Inno Setup Compiler (installer_windows.iss) untuk kompilasi executable mandiri yang premium.
* **Status**: Selesai

## 11. Format Waktu HH:MM:SS & Hitung Mundur (Countdown)
* **Deskripsi**: Mengubah format penanda waktu dari MM:SS menjadi HH:MM:SS. Label sebelah kiri menampilkan waktu berjalan (elapsed time, hitung maju) dan label sebelah kanan menampilkan waktu tersisa (remaining time, hitung mundur). Format ini juga diterapkan pada overlay pojok kanan atas canvas.
* **Status**: Selesai

## 12. Deteksi Bab MKV Otomatis (Auto-Detect MKV Chapters)
* **Deskripsi**: Menjalankan analisis `ffprobe` otomatis saat memuat berkas video MKV yang belum memiliki konfigurasi skip. Jika ditemukan nama chapter yang cocok dengan kata kunci Opening atau Ending, nilai waktu skip langsung diisi dan disimpan secara otomatis.
* **Status**: Selesai

## 13. Fitur Ekspor Video & Subtitel Bersih (Smart Cut & Subtitle Aligner)
* **Deskripsi**: Menyediakan dialog ekspor untuk memotong video bersih tanpa Opening/Ending (dengan opsi Softsub atau Hardsub) baik untuk video aktif saat ini maupun pemrosesan massal (Bulk Folder Batch) menggunakan latar belakang proses threading non-blocking dan visual progress bar. Subtitle diselaraskan dan digeser waktunya secara otomatis secara presisi.
* **Status**: Selesai
