# Spesifikasi Kebutuhan Sistem (SRS): Optimasi Performa Pemutaran Video (Anti-Stuttering)

## 1. Pendahuluan
Dokumen ini menjelaskan spesifikasi perbaikan teknis untuk mengatasi video patah-patah (stuttering/lagging) pada aplikasi pemutar media VidStamp, terutama ketika program dikompilasi ke bentuk executable mandiri (`.exe`) di bawah sistem operasi Windows.

## 2. Deskripsi Masalah & Analisis Bottleneck
Setelah dianalisis, performa pemutaran video terhambat oleh dua operasi tersinkronisasi berulang yang memblokir alur eksekusi thread utama pada setiap iterasi loop pemutaran (~33.3ms untuk target 30 FPS):

1. **Geometry Layout Update (`update_idletasks`):**
   * Lokasi: `vidstamp/ui/player_view.py` -> `RightPlayerPanel.draw_frame`
   * Masalah: Memaksa pembaruan tata letak widget Tkinter secara sinkron setiap kali frame baru digambar. Operasi ini lambat karena melibatkan kalkulasi layout sistem operasi.
   * Dampak: Menghabiskan waktu CPU thread GUI utama, menyebabkan frame rate rendering aktual turun drastis di bawah FPS video asli.

2. **OpenCV Frame Index Query (`cv2.VideoCapture.get`):**
   * Lokasi: `vidstamp/core/player.py` -> `VideoPlayerEngine.get_next_frame` & `read_single_frame`
   * Masalah: Memanggil `self.cap.get(cv2.CAP_PROP_POS_FRAMES)` untuk memeriksa stempel indeks frame saat ini. Operasi ini menanyakan status langsung ke graph Media Foundation Windows secara sinkron.
   * Dampak: Menambahkan latensi 5-15ms pada setiap frame, yang mengakibatkan frame-delay melampaui batas toleransi sinkronisasi audio-video.

## 3. Spesifikasi Perubahan Logika & Perbaikan

### 3.1. Penghapusan Sinkronisasi Layout di Loop Render (UI)
* **Kebutuhan**: Mengurangi beban thread GUI utama.
* **Solusi**: 
  * Menghapus baris `self.canvas.update_idletasks()` di dalam fungsi `draw_frame`.
  * Membaca dimensi Canvas secara langsung menggunakan `winfo_width()` dan `winfo_height()`. Jika widget belum sepenuhnya diinisialisasi (misal, mengembalikan nilai `<= 1`), gunakan resolusi fallback default (760x428) yang telah disediakan.

### 3.2. Pelacakan Indeks Frame In-Memory Secara Manual (Engine)
* **Kebutuhan**: Menghilangkan pemanggilan I/O sinkron ke properti video decoder.
* **Solusi**:
  * Menggunakan variabel instansi `self.cur_idx` di `VideoPlayerEngine` sebagai satu-satunya *source of truth* untuk stempel indeks frame yang sedang diputar.
  * Logika pemutaran:
    * Pada inisialisasi awal (`load`): `self.cur_idx = 0`.
    * Sebelum memanggil `self.cap.read()`, hitung indeks frame yang ditargetkan (`target_idx`).
    * Jika ada antrean `self._seek_target`, gunakan nilai tersebut dan setel posisi OpenCV cap.
    * Jika sedang memutar dengan audio sinkron, bandingkan `self.cur_idx` dengan frame audio target (berdasarkan PTS audio). Jika deselisih `>= 6` frame, lakukan seek ke frame target pada cap dan perbarui `target_idx` ke frame audio target tersebut.
    * Jika pemutaran normal berurutan (tanpa desync/seek), `target_idx = self.cur_idx + 1`.
    * Setelah `self.cap.read()` berhasil mengembalikan frame, perbarui `self.cur_idx = target_idx`.
  * Logika pembacaan frame tunggal (`read_single_frame`):
    * Alih-alih memanggil `cap.get(cv2.CAP_PROP_POS_FRAMES)` untuk menyimpan posisi lama, setel langsung posisi OpenCV ke `frame_idx`.
    * Lakukan pembacaan frame (`cap.read()`).
    * Kembalikan posisi cap secara instan ke indeks frame berikutnya yang akan diputar yaitu `max(0, self.cur_idx + 1)`.

## 4. Kriteria Keberhasilan & Pengujian
* **Kriteria Keberhasilan**: Video diputar dengan mulus tanpa adanya visual putus-putus pada berkas executable `.exe` maupun saat dijalankan dari source code. Indikator waktu detik berjalan (REC) tetap sinkron dan tidak mengalami loncatan yang tidak wajar.
* **Pengujian Manual**:
  * Navigasi ke video berdurasi >10 menit.
  * Putar video, ubah kecepatan (speed combo), lompat ke detik acak.
  * Buat penandaan awal/akhir adegan dan verifikasi file teks catatan yang diekspor.
