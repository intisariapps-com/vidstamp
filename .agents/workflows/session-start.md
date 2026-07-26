---
description: Memuat konteks pekerjaan dari folder memory/ dan mengecek sinkronisasi Git lokal dengan remote.
---

Setiap kali workflow ini dipanggil, kamu WAJIB melakukan hal berikut secara berurutan:
1. **CEK SINKRONISASI GIT & OTORISASI AKUN**:
   - Jalankan perintah terminal `git fetch` dilanjutkan dengan `git status` secara proaktif. Tujuannya untuk memeriksa apakah branch lokal sudah sinkron dengan remote. Jika branch lokal tertinggal (behind), berikan peringatan keras kepada saya dan berikan perintah terminal `git pull` yang bisa saya salin sebelum mulai mengubah kode.
   - Jalankan `git remote -v` untuk mengidentifikasi nama organisasi/akun pemilik repositori remote (misalnya `intisariapps-com`).
   - Jalankan `gh auth status` secara proaktif. Jika akun GitHub CLI yang aktif tidak sesuai dengan pemilik repositori remote, jalankan perintah `gh auth switch --user [owner]` untuk beralih akun secara otomatis guna mencegah kegagalan otorisasi (error 403) di akhir sesi.
2. Cek secara proaktif apakah ada direktori `memory/`, `docs/`, atau file seperti `MEMORY.md` di proyek ini.
3. Jika ada, buka dan baca file tersebut untuk memahami standar, arsitektur, dan status proyek saat ini.
4. Baca juga daftar tugas yang masih tertunda jika ada (misal `INCOMPLETE_PLANS.md` atau file TODO lainnya).
5. Berikan ringkasan singkat dalam Bahasa Indonesia tentang di mana posisi kita saat ini dan apa fokus pengembangannya.
6. Ekstrak sisa TODO list yang ada di MEMORY.md, lalu WAJIB gunakan tool ask_question untuk memunculkan pop-up interaktif kepada saya agar saya bisa memilih tugas mana yang akan dieksekusi hari ini.
