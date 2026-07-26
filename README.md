# 🎬 VidStamp

**VidStamp** (Video Timestamp & Marker) adalah aplikasi desktop berbasis Python yang dirancang untuk memutar video dengan overlay timestamp (detik berjalan) yang presisi, serta memudahkan Anda untuk menandai adegan-adegan penting dalam video (*scene marking*) beserta transkrip subtitlenya.

Aplikasi ini sangat cocok digunakan oleh pembuat konten, analis video, editor, atau profesional SEO/AI yang ingin mengambil cuplikan percakapan dari video berdasarkan detik tertentu secara instan untuk disalin ke ChatGPT/Claude.

---

## ✨ Fitur Utama

- **Suara Tersinkronisasi Tanpa Lag**: Mengintegrasikan OpenCV dengan library `ffpyplayer` secara optimal pada main thread untuk menjamin pemutaran video 1080p yang mulus (stutter-free) dengan audio yang sinkron.
- **Deteksi Subtitle Eksternal & Internal**:
  - Secara otomatis memindai dan memuat file subtitle `.srt` dengan nama yang cocok di direktori video.
  - Fallback otomatis mengekstrak trek subtitle pertama pada file kontainer `.mkv` menggunakan FFmpeg CLI.
- **Auto-Skip Opening & Ending (OP/ED) Cerdas**:
  - Secara otomatis melompati lagu opening dan ending anime sesuai timestamp yang diatur.
  - Mendukung konfigurasi template folder (`season_skip_template.json`) — Cukup setel satu kali di episode pertama, seluruh episode lain dalam folder yang sama otomatis mengikuti durasinya.
- **Pencatatan Adegan "Recorder Style"**: Gunakan shortcut `Ctrl+T` untuk menandai awal dan akhir adegan, berikan nama adegan, dan simpan.
- **Folder Ekspor Rapi**: Seluruh catatan adegan dan dialog subtitle yang diucapkan pada detik tersebut diexport ke dalam subfolder khusus di samping file video tersebut.
- **Antarmuka Fleksibel**: Panel navigasi kiri (folder browser) dapat disembunyikan (`Tab`) untuk tampilan video yang lebih luas, dan mendukung mode layar penuh (F11 / Double-Click).

---

## 🚀 Persyaratan Sistem & Instalasi

Pastikan komputer Anda sudah terpasang **Python 3.8+** dan **FFmpeg** (terdapat di sistem path Anda).

1. Clone repositori ini atau unduh kode sumbernya.
2. Masuk ke direktori proyek dan pasang pustaka dependensi yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Cara Menjalankan

Jalankan aplikasi sebagai modul Python melalui terminal Anda:

```bash
# Opsi 1: Menjalankan dengan folder browser default
python -m vidstamp

# Opsi 2: Membuka aplikasi mengarah langsung ke folder video tertentu
python -m vidstamp "D:\Koleksi Video"

# Opsi 3: Membuka aplikasi langsung memutar berkas video tertentu
python -m vidstamp "D:\Koleksi Video\Anime\episode01.mkv"
```

---

## ⌨️ Daftar Shortcut Keyboard

| Tombol Pintas | Aksi / Fungsi |
|---|---|
| `Space` / `Klik Layar` | Play / Pause |
| `←` / `→` | Mundur / Maju 1 Detik |
| `Shift` + `←` / `→` | Mundur / Maju 10 Detik |
| `Ctrl` + `T` (Pertama) | **Mulai Rekam** (Tandai Awal Adegan) |
| `Ctrl` + `T` (Kedua) | **Berhenti Rekam** (Tandai Akhir Adegan & Simpan) |
| `Tab` | Sembunyikan / Tampilkan Panel Browser Kiri |
| `F11` / `Double Click` | Masuk / Keluar Fullscreen |
| `Escape` | Keluar Fullscreen |
| `Q` | Keluar dari Aplikasi |

---

## 📝 Kontribusi & Lisensi

Proyek ini dirilis di bawah lisensi MIT. Segala kontribusi berupa perbaikan bug, saran fitur baru, atau optimasi dipersilakan dengan membuat Pull Request atau Issue.

*Developed by [intisariapps.com](https://intisariapps.com)*
