# Software Requirements Specification (SRS): Tata Letak Antarmuka Video & Sidebar Adegan PySide6

## 1. Latar Belakang & Masalah
Pada resolusi layar widescreen, penempatan panel "Adegan Tercatat" di bagian bawah video player memakan ruang vertikal yang sangat besar. Hal ini memaksa area visual video player menyusut secara vertikal, menyisakan area kosong hitam (kotak hitam) yang tidak estetis di sisi kiri dan kanan video demi mempertahankan aspek rasio video (16:9).

## 2. Solusi & Desain Tata Letak Baru
Untuk memaksimalkan tinggi rendering video dan memberikan tampilan professional ala media editor premium (seperti Adobe Premiere / DaVinci Resolve), tata letak dirombak menggunakan pembagian horizontal:

### A. Bagian Kiri (Area Pemutar Video - Lebar Dominan)
* **Video Canvas**: Menempati ruang vertikal maksimal di bagian atas kiri.
* **Seek Bar**: Slider horizontal tepat di bawah video canvas.
* **Control Bar**: Baris tombol navigasi tipis (Play/Pause, speed combo, auto skip, marker) di bawah seek bar.

### B. Bagian Kanan (Sidebar Adegan - Lebar Tetap ~260px)
* **Scene List (`QListWidget`)**: Daftar catatan adegan memanjang vertikal ke bawah.
* **Aksi Adegan**: Tombol-tombol "Lompat", "Hapus", dan "Export" disusun rapi di bawah list.
* **Panel Detail**: Teks preview detail adegan di bagian terbawah sidebar, yang muncul dinamis saat adegan dipilih.

---

## 3. Rencana Commit
* Berkas spesifikasi ini akan di-add dan di-commit sebelum penulisan kode dimulai.
