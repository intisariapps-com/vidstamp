# Dokumen Persyaratan Produk (PRD): VidStamp

| Detail Dokumen | Deskripsi |
|---|---|
| **Nama Produk** | VidStamp (Video Timestamp & Smart Anime Player) |
| **Kategori** | Aplikasi Desktop Pemutar Media (Windows & macOS) |
| **Status** | Aktif / Pengembangan |
| **Pembuat** | AI & Developer pair-programming |
| **Terakhir Diperbarui** | 2026-07-27 |

---

## 1. Ringkasan Eksekutif & Tujuan Utama
**VidStamp** adalah aplikasi pemutar video desktop yang dirancang khusus untuk para penggemar anime (dan penonton maraton serial video) agar dapat menikmati tontonan secara maksimal tanpa interupsi manual. 

Tujuan utama dari aplikasi ini adalah memberikan pengalaman menonton yang **mulus (seamless)** dengan melompati bagian pembuka (Opening/OP) dan penutup (Ending/ED) secara otomatis, serta menyediakan alat pencatatan adegan (scene marker) yang pintar dan terintegrasi dengan teks subtitle untuk kebutuhan pembuatan klip, kutipan, maupun pengarsipan.

---

## 2. Latar Belakang & Masalah
Menonton anime, terutama seri lama atau serial panjang, sering kali menghadapi beberapa gangguan berulang:
1. **Skipping Manual yang Mengganggu**: Setiap episode anime umumnya memiliki Opening (OP) berdurasi ~90 detik pada menit awal dan Ending (ED) berdurasi ~90 detik di menit akhir. Melakukan skip manual di setiap episode sangat mengganggu kenyamanan menonton saat maraton (*binge-watching*).
2. **Pencarian & Penandaan Adegan Favorit yang Sulit**: Pengguna sering kesulitan mencatat stempel waktu (*timestamp*) adegan favorit, kutipan dialog penting, atau momen ikonik secara akurat untuk kebutuhan dokumentasi atau pembuatan konten media sosial.
3. **Kehilangan Posisi Menonton**: Pemutar video konvensional sering kali tidak mengingat dengan akurat posisi terakhir diputar saat beralih antar file, atau tidak mengotomatisasi penyimpanan log catatan di tingkat folder file itu sendiri.

---

## 3. Profil Pengguna Target (User Persona)
* **Anime Marathoners (Binge-Watchers)**: Menonton puluhan episode dalam satu sesi. Sangat menghargai otomatisasi skip agar transisi antar episode terasa seperti satu film panjang yang utuh.
* **Content Creators / Video Editors**: Membutuhkan penandaan stempel waktu adegan yang presisi beserta teks dialognya (subtitle) untuk memudahkan proses pembuatan klip/cut.
* **Kolektor & Pengarsip Media**: Mengoleksi anime lokal dalam format resolusi tinggi (`.mkv`) di harddisk lokal dan ingin memiliki file catatan terstruktur (.txt dan .json) berdampingan dengan berkas video.

---

## 4. Fitur Utama & Kebutuhan Fungsional (Saat Ini)

### F.01: Smart Auto-Skip OP/ED
* **Deskripsi**: Sistem mendeteksi stempel waktu awal-akhir Opening dan Ending, lalu melompati bagian tersebut secara instan tanpa jeda visual.
* **Template Season**: Konfigurasi waktu skip dapat disimpan sebagai `season_skip_template.json` di folder induk video. Sekali dikonfigurasi pada satu episode, otomatis berlaku pada seluruh episode anime dalam folder yang sama (karena pola waktu lagu OP/ED anime per musim biasanya selalu sama).

### F.02: Audio-Video Sync Engine (Anti-Stuttering)
* **Deskripsi**: Pemutaran video berbasis OpenCV disinkronkan secara real-time ke Presentation Timestamp (PTS) audio dari library `ffpyplayer`.
* **Optimasi Performa**: Menggunakan rendering dengan interpolasi `cv2.INTER_NEAREST` dan pelacakan indeks frame manual di memori RAM (tanpa interupsi query driver OS) untuk memastikan pemutaran sangat mulus tanpa patah-patah, bahkan pada berkas executable `.exe` portabel.

### F.03: Perekam Catatan Adegan Pintar & Shortcut Ctrl+T
* **Deskripsi**: Pengguna dapat menandai awal adegan dengan pintasan `Ctrl+T`, memutar video hingga akhir adegan, dan menekan `Ctrl+T` kembali untuk menyimpan adegan tersebut.
* **Integrasi Subtitle Otomatis**: Aplikasi membaca file subtitle `.srt` eksternal atau mengekstrak trek subtitle internal pertama dari file `.mkv` menggunakan FFmpeg. Semua teks subtitle yang beririsan dalam rentang adegan yang ditandai akan disalin secara otomatis ke dalam catatan.

### F.04: Sinkronisasi Status Pemutaran & Auto-Export
* **Deskripsi**: 
  * Setiap video yang diputar memiliki subfolder catatan khusus `[NamaVideo]_Catatan/`.
  * **Resume Playback**: Posisi detik terakhir disimpan otomatis setiap 5 detik ke file `playback_state.json` dan dipulihkan saat video dibuka kembali.
  * **Scenes DB & TXT Export**: Setiap penambahan/penghapusan catatan adegan langsung disimpan ke `scenes.json` dan diekspor ke file teks ramah pengguna `[NamaVideo]_catatan_adegan.txt` secara real-time.

### F.05: Antarmuka Kontrol & Format Waktu HH:MM:SS
* **Deskripsi**: Menampilkan seek bar, volume, dropdown kecepatan (0.25x hingga 3.0x), panel navigasi file di sebelah kiri, dan tombol navigasi kontrol.
* **Tampilan Waktu**: Format waktu disederhanakan menjadi `HH:MM:SS` (tanpa milidetik) dengan dua informasi: waktu berjalan (elapsed) di sebelah kiri, dan sisa waktu episode (hitung mundur/remaining dengan tanda minus `-`) di sebelah kanan.

---

## 5. Rencana Pengembangan Fitur Masa Depan (Roadmap)

### Fase 1: Pembaruan UI/UX Premium (CustomTkinter)
* Mengubah tampilan dari Tkinter klasik menjadi Dark Mode modern dengan sudut tombol melengkung (*rounded corners*) dan transisi hover yang halus.
* Dukungan penuh drag-and-drop file video langsung dari Windows Explorer ke layar pemutar.

### Fase 2: Integrasi Online API (AniSkip/MyAnimeList)
* Mengintegrasikan API AniSkip secara online. Saat video anime dibuka, aplikasi secara otomatis mencocokkan judul/hash video ke database AniSkip dan mengunduh stempel waktu lagu pembuka/penutup tanpa pengguna harus mengaturnya secara manual.

### Fase 3: Peningkatan Fungsional Media
* **Multi-Subtitle Selection**: Mengizinkan pengguna memilih trek subtitle tertentu jika file `.mkv` memiliki lebih dari satu bahasa.
* **Seekbar Hover Thumbnail**: Menampilkan cuplikan gambar kecil (thumbnail) frame video saat kursor tetikus diarahkan di sepanjang slider seek bar.

---

## 6. Persyaratan Teknis & Platform
* **Bahasa**: Python 3.10+
* **Library Utama**: OpenCV (`opencv-python`), `ffpyplayer` (SDL2 backend), Pillow (`PIL`), Tkinter (GUI)
* **Kompilasi**: PyInstaller (untuk distribusi mandiri portabel tanpa instalasi python)
* **Platform Target**: Windows 10/11 (utama) & macOS
