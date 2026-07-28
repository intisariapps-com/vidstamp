# Software Requirements Specification (SRS): Optimasi Performa Video & Jendela Catatan Terpisah

## 1. Latar Belakang & Masalah
* **Masalah Video Patah-patah**: Penggunaan `Qt.SmoothTransformation` untuk menskalakan frame OpenCV beresolusi tinggi pada setiap iterasi timer (15ms) memakan resource CPU yang sangat besar, menyebabkan penurunan framerate (stuttering).
* **Kerapian Layar Video**: Pengguna ingin area menonton video benar-benar bersih dan lapang. Panel adegan tercatat sebaiknya dipisahkan ke jendela dialog mengambang (seperti menu Batch Merger) daripada menempel di sidebar.

## 2. Solusi Desain Baru & Optimasi
### A. Optimasi Rendering Video (Anti-Stuttering)
* Mengganti `Qt.SmoothTransformation` dengan **`Qt.FastTransformation`** di dalam fungsi rendering `_draw_frame_on_canvas`.
* Ini akan memotong beban CPU rendering Qt hingga 80%, mengembalikan kenyamanan pemutaran video secara mulus (smooth playback).

### B. Jendela Catatan Adegan Terpisah (`SceneListDialog`)
* Membuat kelas dialog baru bernama `SceneListDialog` (`QDialog`) yang menampung:
  * List adegan tercatat (`QListWidget`).
  * Tombol aksi ("Lompat", "Hapus", "Export").
  * Preview detail adegan (`QTextEdit`).
* Jendela dialog ini diluncurkan dari menu utama **Peralatan** -> **Daftar Catatan Adegan...** atau dengan pintasan keyboard **`Ctrl+L`**.
* Ketika tombol "Lompat" diklik di dialog, ia akan memicu fungsi `seek_to` pada player utama secara real-time.
* File `player_view.py` akan dibersihkan dari panel adegan bawah/samping, sehingga area player menjadi 100% luas dan fokus menonton.

---

## 3. Rencana Commit
* Berkas spesifikasi ini akan di-add dan di-commit sebelum penulisan kode dimulai.
