# Spesifikasi Kebutuhan Perangkat Lunak (SRS): Indikator Detik Berjalan Saat Perekaman Adegan (Ctrl+T)

Dokumen ini mendokumentasikan spesifikasi kebutuhan untuk fitur penunjuk durasi detik berjalan secara real-time saat melakukan perekaman/pencatatan adegan.

---

## 1. Latar Belakang & Deskripsi Fitur
Saat pengguna menekan pintasan tombol `Ctrl+T` (atau tombol *[M] Start*), aplikasi memulai pencatatan adegan (menandai waktu mulai). Sebelumnya, pengguna tidak mengetahui berapa detik durasi adegan yang sudah berjalan sebelum mereka menekan `Ctrl+T` kedua kali untuk menyimpan.

Fitur ini bertujuan untuk menampilkan indikator detik berjalan secara real-time sejak tombol perekaman ditekan:
1. **Pada Canvas Video (Overlay)**: Menampilkan teks berformat `REC: X.XXs` berwarna merah kontras di sebelah kiri bawah (di atas label START).
2. **Pada Info Mark Bar (`lbl_mk`)**: Memperbarui label `lbl_mk` di kanan bawah secara dinamis dengan format `S:MM:SS.CC  E:--  (X.XXs)`.

---

## 2. Rincian Perubahan Kode

### Komponen UI: `vidstamp/ui/player_view.py`
1. **Modifikasi Fungsi `_upmk(self, current_sec=None)`**:
   * Menambahkan parameter opsional `current_sec`.
   * Jika `self.mark_start` tidak bernilai `None`, `self.mark_end` bernilai `None`, dan `current_sec` diberikan, hitung selisih durasi `current_sec - self.mark_start` dan tampilkan di label `lbl_mk`.
2. **Modifikasi Fungsi `draw_frame(self, frame)`**:
   * Jika `self.mark_start` aktif (`not None`) dan `self.mark_end` belum aktif (`None`):
     * Hitung durasi berjalan: `running_sec = sec - self.mark_start`.
     * Render teks `REC: {running_sec:.2f}s` berwarna merah (BGR: `(0, 0, 255)`) dengan bayangan hitam di canvas.
     * Panggil `self._upmk(sec)` untuk memperbarui label info bar secara dinamis pada frame yang dirender.

---

## 3. Rencana Pengujian (Verifikasi)
1. **Pengujian Fungsional**:
   * Jalankan program menggunakan `python -m vidstamp`.
   * Buka video apa saja.
   * Tekan `Ctrl+T` pertama kali untuk memulai perekaman.
   * Pastikan indikator overlay merah `REC: X.XXs` muncul dan bertambah nilainya di layar video saat video diputar atau di-seek.
   * Pastikan label status di kanan bawah ikut ter-update.
   * Tekan `Ctrl+T` kedua kali atau `Ctrl+Space` (Batal) untuk memastikan indikator tersebut hilang dengan semestinya.
