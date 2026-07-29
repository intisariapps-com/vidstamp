# Spesifikasi Kebutuhan Perangkat Lunak (SRS): Sistem Pintasan Keyboard (Keyboard Shortcuts) Terpusat

Dokumen ini mendokumentasikan spesifikasi teknis untuk implementasi pintasan keyboard (keyboard shortcuts) baru pada aplikasi VidStamp, termasuk migrasi pintasan perekaman adegan dan penambahan pintasan perekaman Opening/Closing anime menggunakan skema toggle 1-tombol.

---

## 1. Deskripsi Fungsionalitas & Desain Pintasan

Untuk mempercepat alur kerja penandaan video anime dan adegan penting secara instan tanpa menyentuh mouse, aplikasi mendukung tombol pintas global.

### A. Migrasi Perekaman Adegan (Scene Recorder)
* **Pintasan Lama**: `Ctrl + T`
* **Pintasan Baru**: `Ctrl + R` (Case-insensitive: `Ctrl + r` dan `Ctrl + R`)
* **Mekanisme**:
  * **Tekan Pertama**: Menandai detik awal adegan (`mark_start`).
  * **Tekan Kedua**: Menandai detik akhir adegan (`mark_end`) dan langsung memicu penyimpanan catatan adegan (Scene) ke subfolder catatan.

### B. Perekaman Opening Anime (Opening Recorder)
* **Pintasan**: `Ctrl + O` (Case-insensitive: `Ctrl + o` dan `Ctrl + O`)
* **Mekanisme**:
  * **Tekan Pertama**: Menandai detik mulai Opening (`op_start`). Status visual diperbarui pada label bawah player.
  * **Tekan Kedua**: Menandai detik selesai Opening (`op_end`). Sistem secara otomatis melakukan kalkulasi, menyimpan konfigurasi skip ke file `skip_config.json` lokal (berlaku untuk folder aktif/season), dan menampilkan notifikasi sukses.
  * Jika keduanya sudah diisi sebelumnya, penekanan tombol `Ctrl + O` baru akan menghapus konfigurasi Opening lama dan memulai perekaman baru (menyetel ulang `op_start` ke detik aktif dan `op_end` ke `None`).
  * Jika pengguna melakukan *seek* mundur secara tidak sengaja sehingga detik selesai lebih kecil dari detik mulai, sistem akan menukar (*swap*) kedua nilai secara otonom sebelum menyimpan agar rentang waktu tetap valid.

### C. Perekaman Closing/Ending Anime (Closing Recorder)
* **Pintasan**: `Ctrl + C` (Case-insensitive: `Ctrl + c` dan `Ctrl + C`)
* **Mekanisme**:
  * **Tekan Pertama**: Menandai detik mulai Ending/Closing (`ed_start`).
  * **Tekan Kedua**: Menandai detik selesai Ending/Closing (`ed_end`). Sistem secara otomatis menyimpan konfigurasi skip ke berkas `skip_config.json` lokal, dan memberikan umpan balik visual sukses.
  * Memiliki logika reset rekam baru jika ditekan kembali, serta penukaran otomatis (*auto-swap*) jika detik selesai lebih kecil dari detik mulai.

---

## 2. Tabel Lengkap Pintasan Keyboard (Pusat Referensi Pengguna)

Seluruh daftar pintasan keyboard yang didukung oleh VidStamp terdokumentasi dalam tabel berikut:

| Tombol Pintas | Aksi / Fungsi | Target Panel |
|---|---|---|
| `Space` / `Klik Layar` | Play / Pause Pemutaran | Panel Utama |
| `←` / `→` | Mundur / Maju 1 Detik | Panel Utama |
| `Shift` + `←` / `→` | Mundur / Maju 10 Detik | Panel Utama |
| `F11` / `Double Click` | Masuk / Keluar Mode Layar Penuh (Fullscreen) | Jendela Utama |
| `Escape` | Keluar dari Mode Layar Penuh | Jendela Utama |
| `Ctrl` + `R` | **Perekam Adegan** (Tekan ke-1: Set Awal, Tekan ke-2: Set Akhir & Simpan) | Global |
| `Ctrl` + `O` | **Perekam Opening** (Tekan ke-1: Set Mulai OP, Tekan ke-2: Set Selesai OP & Simpan) | Global |
| `Ctrl` + `C` | **Perekam Closing/ED** (Tekan ke-1: Set Mulai ED, Tekan ke-2: Set Selesai ED & Simpan) | Global |
| `Ctrl` + `Space` | Membatalkan Perekaman Adegan yang Sedang Berjalan | Global |
| `Ctrl` + `M` | Membuka Jendela Wizard Batch Merger (Penyatuan Massal) | Global |
| `Q` | Keluar dari Aplikasi secara Bersih | Global |

---

## 3. Rencana Pengujian (Verifikasi)

1. Putar video lokal berdurasi panjang.
2. Tekan `Ctrl + R` saat adegan penting dimulai, biarkan berjalan beberapa detik, lalu tekan `Ctrl + R` lagi. Pastikan dialog simpan adegan muncul dan `Ctrl + T` lama sudah tidak aktif.
3. Tekan `Ctrl + O` pada menit awal lagu Opening. Pastikan muncul status `OP Mulai` di status bar. Tekan `Ctrl + O` lagi di akhir lagu Opening. Verifikasi bahwa file `skip_config.json` terbuat dan status bar menunjukkan `OP Tersimpan`.
4. Tekan `Ctrl + C` pada menit awal lagu Ending. Pastikan muncul status `ED Mulai`. Tekan `Ctrl + C` lagi di akhir lagu Ending. Verifikasi bahwa file konfigurasi terupdate.
5. Uji tombol pembatalan (`Ctrl + Space`) ketika proses perekaman sedang berlangsung.
