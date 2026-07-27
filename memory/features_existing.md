# Fitur Terimplementasi (Existing)

Berikut adalah daftar fitur yang sudah selesai dibangun dan berstatus stabil di proyek VidStamp.

## 1. Fondasi Proyek
* **Deskripsi**: Struktur direktori dasar, konfigurasi Git, manajemen sesi modular, dan runner runner minimalis.
* **Status**: Selesai

## 2. Playback Engine Terintegrasi Audio (ffpyplayer + OpenCV)
* **Deskripsi**: Menangani pemutaran frame video OpenCV sinkron dengan audio track menggunakan ffpyplayer secara real-time.
* **Status**: Selesai

## 3. Optimasi Video Super Mulus (Anti Patah-patah)
* **Deskripsi**: Toleransi desync audio-video diperbesar ke 6 frame untuk menghindari pemanggilan set-frame OpenCV yang berat. Resize canvas menggunakan interpolasi `cv2.INTER_NEAREST` untuk performa CPU ringan. Selain itu, pemanggilan pemblokiran layout `self.canvas.update_idletasks()` di loop render dan kueri sinkron OpenCV `cap.get(cv2.CAP_PROP_POS_FRAMES)` dieliminasi serta digantikan dengan pelacakan frame index in-memory (`self.cur_idx`).
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
