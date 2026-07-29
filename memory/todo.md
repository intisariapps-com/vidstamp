# TODO List - Migrasi VidStamp ke Flutter Desktop & Engine media-kit

Dokumen ini adalah daftar tugas aktif (TODO) untuk proyek migrasi VidStamp ke basis kode Flutter Desktop dengan engine pemutar video `media-kit` (`libmpv`).

---

## 📌 Status Cabang Git (Git Branch)
Seluruh pengerjaan dilakukan pada cabang terpisah:
- **Cabang Target**: `feature/flutter-media-kit`
- **Tujuan**: Mengamankan versi Python asli agar tetap stabil dan bisa digunakan sewaktu-waktu.

---

## 📋 Checklist Tugas Migrasi

### 🚀 Fase 1: Inisialisasi Proyek & Setup Player
- [x] Buat cabang git baru: `git checkout -b feature/flutter-media-kit`.
- [x] Jalankan perintah inisialisasi proyek Flutter Desktop: `flutter create --platforms=windows,macos vidstamp_flutter`.
- [x] Tambahkan package pemutar video ke `pubspec.yaml` (media_kit, media_kit_video, media_kit_libs_video).
- [x] Buat antarmuka pemutar video minimalis di Flutter untuk menguji kelancaran akselerasi hardware GPU.


### 🎨 Fase 2: Pembangunan Antarmuka UI (Split Panel Layout)
- [ ] Desain panel pemutar video di kiri dan panel catatan/transkrip di kanan.
- [ ] Buat tombol kontrol video custom (Play/Pause, Mute, Volume, Durasi waktu, Toggle Fullscreen).
- [ ] Pindahkan pengaturan checkbox visual ke dropdown menu kustom "Peralatan" di kanan atas (Tampilkan Timestamp, Milidetik, Subtitel, Skip OP/ED).

### ⌨️ Fase 3: Integrasi Sistem Shortcuts & Scene Recorder
- [ ] Terapkan widget `Shortcuts` dan `Actions` di Flutter untuk mendeteksi:
  * `Ctrl+R` -> Toggle Scene Record
  * `Ctrl+O` -> Toggle Opening Record
  * `Ctrl+C` -> Toggle Closing Record
- [ ] Buat pengaman fokus pengetikan notes: shortcut global otomatis dinonaktifkan jika kursor aktif di input teks.
- [ ] Buat list view catatan adegan di panel kanan dengan detail timestamp mulai/selesai serta tombol hapus.
- [ ] Terapkan ekspor berkas catatan adegan ke format berkas `.txt` dan `.srt`.

### ⏱️ Fase 4: Deteksi Bab (Chapters) MKV & Auto-Skip
- [ ] Panggil sub-proses CLI `ffprobe` secara asinkron untuk mendeteksi metadata chapter video MKV.
- [ ] Implementasikan parser kata kunci untuk mendeteksi Opening & Ending otomatis.
- [ ] Buat scheduler pemantau durasi pemutaran video `media-kit` untuk melompati waktu Opening/Ending secara otomatis (Auto-Skip).

### ✂️ Fase 5: Ekspor Video Bersih & Pergeseran Subtitle
- [ ] Porting fungsi pergeseran teks `cut_and_shift_srt` dan `cut_and_shift_ass` ke bahasa Dart.
- [ ] Terapkan filter pembersihan OCR subtitle duplikat.
- [ ] Susun instruksi command complex FFmpeg untuk memotong video bersih dan membakar subtitel ASS/SRT (hardsub).
- [ ] Tampilkan dialog progres render ekspor asinkron dengan progress bar persentase %.

### 📦 Fase 6: Penggabungan Massal & Concat Lossless
- [ ] Implementasikan batch exporter untuk memproses seluruh file video dalam folder.
- [ ] Gabungkan video secara lossless menggunakan filter concat (menggunakan path relatif agar aman di OS Windows).
- [ ] Rakit satu file subtitle global `.srt` hasil merger episode secara terintegrasi.
