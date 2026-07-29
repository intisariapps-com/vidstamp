---
name: video-playback-optimization
description: Panduan diagnosis dan optimasi performa pemutaran video OpenCV + ffpyplayer agar lancar bebas lag/patah-patah.
---

# Video Playback Optimization Skill

Skill ini mendokumentasikan panduan dan praktik terbaik untuk mengoptimalkan performa pemutaran video real-time di aplikasi VidStamp yang menggunakan mesin pemutaran hibrida **OpenCV (Video)** + **ffpyplayer (Audio)**.

## 1. Penyebab Utama Video Patah-Patah (Lag/Stutter)

Pemutaran video hibrida rentan terhadap desinkronisasi antara jam audio (`ffpyplayer.player.MediaPlayer`) dan decoder video (`cv2.VideoCapture`). Masalah utama meliputi:

1. **Pemanggilan `cap.set(cv2.CAP_PROP_POS_FRAMES, ...)` Berlebihan**:
   - Fungsi `cap.set` pada OpenCV adalah operasi pemindahan keyframe yang berat karena memaksa decoder untuk mencari keyframe terdekat (I-frame) dan men-decode maju hingga ke frame target.
   - Jika desinkronisasi kecil diselesaikan dengan `cap.set`, pemutaran akan terganggu secara konstan (stuttering).
2. **Beban Rendering Thread Utama (GUI Thread)**:
   - Pengubahan ukuran gambar (`cv2.resize`) dan konversi warna (`cv2.cvtColor`) untuk ribuan frame video resolusi tinggi (1080p/4K) di thread utama Tkinter dapat menghambat antrean event Tkinter.
3. **Penggunaan Algoritma Resize yang Berat**:
   - Menggunakan interpolasi interpolasi berkualitas tinggi seperti `cv2.INTER_CUBIC` atau `cv2.INTER_AREA` untuk rendering live preview sangat memperlambat FPS. Gunakan `cv2.INTER_NEAREST` atau `cv2.INTER_LINEAR` saat playback berjalan.

---

## 2. Strategi Optimasi Sinkronisasi (Sync Strategy)

Untuk mencegah patah-patah, mesin pemutar harus menggunakan tiga strategi berdasarkan selisih frame (`diff = target_frame - cur_idx`):

### A. Grab Cepat untuk Ketertinggalan Kecil (0 < diff < 30)
Bila video tertinggal sedikit (di bawah 1 detik), hindari `cap.set`. Alih-alih, lakukan loop `cap.grab()` sebanyak `diff - 1` kali untuk membuang paket tanpa mem-decode-nya secara penuh, diikuti oleh satu kali `cap.read()`. Ini sangat cepat (~1-2 ms per frame).

### B. Frame Reuse untuk Keterlaluan Cepat (-15 < diff < 0)
Bila video berjalan lebih cepat daripada audio (di bawah 500 ms), hindari membaca frame baru dari berkas. Gunakan kembali (reuse) frame terakhir (`self.last_frame`) agar audio dapat mengejar ketertinggalannya.

### C. Hard Seek untuk Desinkronisasi Besar
Bila desinkronisasi lebih dari 1 detik lambat (`diff >= 30`) atau lebih dari 500 ms cepat (`diff <= -15`), lakukan seek paksa menggunakan `cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)`.

---

## 3. Langkah Pemecahan Masalah (Troubleshooting Checklist)

- [ ] Pastikan driver kartu grafis dan kodek video terinstal dengan baik di sistem operasi.
- [ ] Hindari rendering teks overlay yang terlalu rumit di setiap frame.
- [ ] Gunakan cache frame (`self.last_frame`) untuk meminimalisasi operasi decoding yang tidak perlu.
- [ ] Optimalkan ukuran canvas agar sesuai dengan rasio aspek video asli untuk menghindari distorsi selama resize.
