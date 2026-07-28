# Spesifikasi Kebutuhan Perangkat Lunak (SRS): Deteksi Bab MKV Otomatis & Fitur Ekspor Video Bersih (Smart Cut & Subtitle Aligner)

Dokumen ini mendokumentasikan spesifikasi kebutuhan untuk integrasi fitur deteksi bab (chapters) MKV otomatis guna menentukan waktu skip OP/ED serta modul ekspor video bersih (tanpa OP/ED) dengan penyelarasan subtitel otomatis dari skrip eksternal `mkv_merger_skip_oped.py`.

---

## 1. Deskripsi Fitur

### A. Deteksi Bab (Chapters) MKV Otomatis
Mengotomatiskan pengisian waktu mulai/selesai Opening (OP) dan Ending (ED) tanpa input manual dari pengguna jika berkas video bertipe MKV memiliki metadata chapter (bab).
* **Mekanisme**:
  * Ketika video dimuat di `load_video`, jika format video mendukung metadata chapter (seperti `.mkv`), jalankan `ffprobe` di latar belakang untuk mengekstrak daftar chapter.
  * Lakukan pencarian nama chapter menggunakan kata kunci pencocokan kata (case-insensitive): `["lagu pembuka", "lagu penutup", "opening", "ending", "op", "ed", "closing", "theme"]`.
  * Jika chapter Opening terdeteksi, isi nilai `op_start` dan `op_end`.
  * Jika chapter Ending terdeteksi, isi nilai `ed_start` dan `ed_end`.
  * Simpan nilai tersebut secara otomatis ke berkas `skip_config.json` lokal sehingga langsung siap digunakan untuk Auto-Skip.

### B. Fitur Ekspor Video & Subtitel Bersih (Smart Cut & Shift)
Mengintegrasikan kapabilitas dari skrip `mkv_merger_skip_oped.py` ke dalam UI VidStamp sehingga pengguna dapat mengekspor video bersih tanpa bagian Opening/Ending dengan subtitel yang terpotong dan tergeser secara presisi.
* **Mekanisme**:
  * Menambahkan tombol **"✂️ Ekspor Video Bersih"** pada dialog "Set Skip OP/ED" atau panel kontrol utama.
  * Ketika tombol diklik, tampilkan dialog konfigurasi ekspor:
    * **Mode Subtitel**:
      1. *Hardsub*: Subtitel digabungkan langsung ke dalam video hasil ekspor menggunakan filter `subtitles` FFmpeg.
      2. *Softsub (Potong Saja)*: Video dipotong bersih tanpa hardsub, dan berkas subtitel `.srt` bersih dengan timestamp tergeser disimpan secara terpisah.
    * **Cakupan Ekspor**:
      1. *Video Aktif Saja*: Hanya memproses video yang sedang dibuka.
      2. *Bulk Folder (Semua Episode)*: Memproses seluruh berkas video dalam folder aktif saat ini secara massal (batch).
  * Jalankan proses rendering FFmpeg di latar belakang (Background Thread) agar aplikasi tidak membeku (*non-blocking*), serta sediakan jendela indikator progres yang informatif (menampilkan bar persentase dan estimasi waktu selesai).

---

## 2. Perubahan Struktur Kode

### A. Modul Utilitas: `vidstamp/utils/path_helper.py`
* Menambahkan fungsi `get_ffprobe_path()` untuk mendeteksi biner `ffprobe` baik di mode pengembangan (dev) maupun rilis PyInstaller (EXE).

### B. Modul Inti: `vidstamp/core/player.py` atau Tambah Modul Baru `vidstamp/core/exporter.py`
* Membuat modul baru atau menambahkan fungsi pembantu untuk:
  * Membaca chapter MKV menggunakan `ffprobe`.
  * Melakukan kalkulasi pemotongan segmen (trimming) video & audio menggunakan FFmpeg filter complex concat.
  * Mengekstrak, memotong, dan menggeser subtitel SRT secara presisi berdasarkan daftar chapter/detik yang di-skip (logika pemotongan SRT dari `mkv_merger_skip_oped.py`).

### C. Modul UI Player View: `vidstamp/ui/player_view.py`
* Menambahkan tombol aksi ekspor video bersih di dalam UI Dialog "Set Skip OP/ED".
* Mendesain jendela dialog kemajuan (Progress Window) dengan progress bar Tkinter (`ttk.Progressbar`) untuk memantau proses render FFmpeg.

### D. Modul UI Window Utama: `vidstamp/ui/main_window.py`
* Memodifikasi event `load_video` agar otomatis memicu fungsi deteksi chapter MKV saat video pertama kali dimuat jika belum ada `skip_config.json` tersimpan.

---

## 3. Rencana Pengujian (Verifikasi)
1. Buka berkas video MKV yang memiliki chapter Opening/Ending (misalnya Sword Art Online BD).
2. Pastikan nilai input di dialog "Set Skip OP/ED" terisi secara otomatis tanpa perlu diketik manual.
3. Klik tombol "Ekspor Video Bersih" dan pilih opsi "Hardsub" untuk "Video Aktif Saja".
4. Verifikasi bahwa proses ekspor berjalan di latar belakang tanpa membuat aplikasi tidak responsif (*Not Responding*).
5. Putar berkas hasil ekspor: pastikan bagian Opening/Ending hilang dan teks subtitel tetap muncul secara sinkron tepat waktu.
