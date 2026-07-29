# Spesifikasi Kebutuhan Perangkat Lunak (SRS): Migrasi VidStamp ke Flutter Desktop & Engine media-kit

Dokumen ini mendokumentasikan rencana dan spesifikasi teknis untuk migrasi basis kode VidStamp dari Python (Tkinter + OpenCV) ke Flutter Desktop (Dart) menggunakan engine pemutar video bertenaga akselerasi perangkat keras GPU, yaitu **`media-kit`** (berbasis `libmpv`).

---

## 1. Latar Belakang & Tujuan
Aplikasi VidStamp berbasis Python saat ini menggunakan OpenCV untuk pemutaran video, yang menyebabkan desinkronisasi audio-video, lag parah pada resolusi 1080p+, dan rendering subtitel internal MKV (gaya ASS) yang pecah. 

**Tujuan Migrasi:**
1. **Performa Sempurna**: Memanfaatkan akselerasi hardware GPU lewat `libmpv` untuk pemutaran video 1080p/4K yang mulus dan pencarian waktu (*seeking*) instan.
2. **Retensi Estetika Subtitel**: Merender subtitel internal ASS bawaan MKV dengan font, gaya, warna, dan posisi asli secara native.
3. **UI Modern & Premium**: Menggunakan Flutter Desktop untuk antarmuka yang modern, responsif, memiliki animasi mikro, serta sistem pintasan keyboard (*shortcuts*) yang kokoh.

---

## 2. Arsitektur Teknologi & Dependensi
* **Bahasa & Framework**: Dart 3.x & Flutter SDK 3.x (Target: Windows & macOS)
* **Video Engine**: 
  * `media-kit` (Pustaka inti kontrol pemutar)
  * `media-kit_video` (Widget render video permukaan GPU)
* **Mesin Native**: `libmpv` (melalui dynamic link library `mpv-2.dll` di Windows)
* **Manipulasi Video & Ekspor**:
  * Panggilan sub-proses biner `ffmpeg` dan `ffprobe` secara asinkron dari Flutter.
* **Subtitle Processing**:
  * Modul parser dan pergeseran timestamp teks `.srt` dan `.ass` ditulis ulang langsung di Dart.

---

## 3. Rencana Struktur Folder Proyek Baru
```
vidstamp_flutter/
├── pubspec.yaml             # Dependensi Flutter (media-kit, path, dll)
├── lib/
│   ├── main.dart            # Titik masuk aplikasi
│   ├── models/
│   │   ├── scene_record.dart  # Model data rekaman adegan
│   │   └── skip_config.dart   # Model data skip Opening/Ending
│   ├── player/
│   │   ├── video_player.dart  # Widget pemutar video media-kit
│   │   └── player_controller.dart # Pengendali playback, volume, subtitle
│   ├── shortcuts/
│   │   └── keyboard_shortcuts.dart # Konfigurasi shortcut global
│   ├── exporter/
│   │   ├── ffmpeg_runner.dart # Eksekutor proses FFmpeg untuk pemotongan
│   │   └── subtitle_aligner.dart # Logika pergeseran teks SRT & ASS
│   └── ui/
│       ├── main_screen.dart   # Tata letak layar utama (Split Panel)
│       ├── control_bar.dart   # Tombol play, seek, volume, peralatan
│       └── scene_list.dart    # Daftar catatan adegan di panel kanan
```

---

## 4. Alur Kerja & Checklist TODO Migrasi

### Fase 1: Inisialisasi & Integrasi Engine Video (Mulai)
* [ ] Inisialisasi proyek Flutter Desktop baru (`flutter create --platforms=windows,macos vidstamp_flutter`).
* [ ] Konfigurasi file `pubspec.yaml` dengan dependensi `media-kit`, `media-kit_video`, dan `path_provider`.
* [ ] Setup dan uji pemutar video `media-kit` sederhana di Windows untuk memastikan file DLL `mpv-2.dll` termuat secara otomatis dan video berjalan mulus di GPU.

### Fase 2: Pembangunan Antarmuka UI Premium (Layout)
* [ ] Desain tata letak utama: Panel pemutar di bagian kiri dan Panel catatan/transkrip di bagian kanan.
* [ ] Buat bar kontrol pemutar (Play/Pause, Mute, Volume, Durasi waktu, Toggle Fullscreen).
* [ ] Buat menu dropdown "Peralatan" untuk kontrol overlay (Tampilkan Timestamp, Milidetik, Tampilkan Subtitel, Skip OP/ED).

### Fase 3: Integrasi Sistem Keyboard Shortcuts & Scene Recorder
* [ ] Terapkan pintasan keyboard global menggunakan widget `Shortcuts` dan `Actions` Flutter:
  * `Ctrl + R` -> Toggle perekaman adegan (Scene)
  * `Ctrl + O` -> Toggle pembatas Opening (OP)
  * `Ctrl + C` -> Toggle pembatas Closing (ED)
* [ ] Implementasikan proteksi fokus input teks: pintasan keyboard tidak akan berjalan secara tidak sengaja ketika kursor aktif mengetik catatan adegan di kolom input.
* [ ] Tampilkan hasil rekaman adegan secara real-time pada panel listbox kanan dengan tombol aksi hapus dan ekspor berkas `.txt` / `.srt`.

### Fase 4: Auto-Skip & Bab (Chapters) MKV
* [ ] Buat fungsi pembaca metadata chapter video MKV secara asinkron menggunakan sub-proses `ffprobe`.
* [ ] Terapkan pencarian kata kunci chapter untuk mendeteksi Opening & Ending otomatis dan menyimpannya ke konfigurasi JSON lokal.
* [ ] Buat fitur Auto-Skip yang mendengarkan perubahan waktu pemutaran `media-kit` secara real-time dan melompati waktu OP/ED secara instan tanpa lag.

### Fase 5: Modul Ekspor Video Bersih & Pergeseran Subtitle
* [ ] Porting fungsi pemotong subtitle `cut_and_shift_srt` dan `cut_and_shift_ass` ke bahasa Dart.
* [ ] Terapkan pembersih teks OCR subtitle duplikat (deduplikasi OCR).
* [ ] Susun perintah filter complex FFmpeg di Dart untuk memotong video bersih (tanpa OP/ED) dan membakar hardsub (baik SRT biasa maupun ASS bergaya penuh).
* [ ] Tampilkan dialog progres kemajuan pemotongan video (dengan persentase % dan opsi pembatalan proses render).

### Fase 6: Penggabungan Massal & Concat Lossless (Bulk)
* [ ] Terapkan pengekspor massal untuk memotong semua file video dalam folder kerja sekaligus.
* [ ] Buat file gabungan MP4 akhir menggunakan concat lossless FFmpeg (path relatif untuk keamanan Windows).
* [ ] Susun file subtitle `.srt` global akhir yang selaras dengan gabungan video episode.
