# Spesifikasi Kebutuhan Perangkat Lunak (SRS): Fitur Resume Playback & Sinkronisasi Otomatis Catatan Adegan

Dokumen ini mendokumentasikan spesifikasi kebutuhan untuk fitur kelanjutan pemutaran (Resume Playback) dan sinkronisasi otomatis catatan adegan tanpa perlu ekspor manual.

---

## 1. Deskripsi Fitur

### A. Fitur Resume Playback
Meningkatkan kenyamanan pengguna dengan mengingat detik terakhir video saat diputar. Ketika pengguna membuka kembali video yang sama, player akan langsung melompat ke detik terakhir tersebut.
* **Mekanisme**:
  * Status disimpan ke file `playback_state.json` di folder khusus catatan video (`[Nama Video]_Catatan/`).
  * Posisi disimpan otomatis setiap 5 detik (periodik) saat video diputar, saat berganti video, atau saat aplikasi ditutup (`quit_app`).
  * Posisi dipulihkan saat video berhasil dimuat di `load_video`.

### B. Fitur Sinkronisasi & Auto-Update Catatan Adegan
Menghilangkan kebutuhan untuk menekan tombol "Export" secara manual.
* **Mekanisme**:
  * Daftar adegan disimpan secara terstruktur ke database `scenes.json` di folder catatan video.
  * Setiap ada adegan baru yang disimpan atau dihapus di GUI, program akan memperbarui database JSON dan menulis ulang file catatan teks format `.txt` (`[Nama Video]_catatan_adegan.txt`) secara otomatis.
  * Ketika video dibuka kembali, database `scenes.json` dibaca secara otomatis untuk memulihkan daftar adegan lama ke dalam GUI listbox, sehingga catatan lama tidak akan tertimpa atau hilang.

---

## 2. Perubahan Struktur Kode

### A. Modul Utilitas: `vidstamp/utils/file_manager.py`
Menambahkan helper read/write:
* `load_playback_state(video_path)` & `save_playback_state(video_path, current_sec)`
* `load_scenes_data(video_path)` & `save_scenes_data(video_path, scenes_list)`

### B. Modul UI Player View: `vidstamp/ui/player_view.py`
* Modifikasi `save_scene_action` dan `_del_sc` agar menyimpan data JSON dan mengekspor teks otomatis.
* Menambahkan metode `_auto_export_scenes()` untuk menulis file teks `.txt` secara otonom.
* Menambahkan metode `load_saved_scenes()` untuk memuat database JSON lama ke GUI listbox.

### C. Modul UI Window Utama: `vidstamp/ui/main_window.py`
* Modifikasi `load_video` untuk menyimpan posisi video lama dan memulihkan posisi video baru serta adegannya.
* Modifikasi `quit_app` untuk menyimpan posisi detik terakhir sebelum keluar.
* Menambahkan event loop `_start_auto_save_loop` untuk menyimpan posisi video secara periodik tiap 5 detik.

---

## 3. Rencana Pengujian (Verifikasi)
1. Buka video adegan. Putar sampai detik tertentu (misal detik ke-20). Tutup aplikasi.
2. Cek apakah folder `_Catatan` berisi file `playback_state.json`.
3. Buka kembali aplikasi dan video tersebut. Pastikan player langsung seek ke detik ke-20.
4. Buat catatan adegan baru. Pastikan file teks `.txt` langsung dibuat dan di-update di folder catatan secara real-time.
