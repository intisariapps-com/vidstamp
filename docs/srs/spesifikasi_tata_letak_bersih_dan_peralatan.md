# Spesifikasi Kebutuhan Perangkat Lunak (SRS): Tata Letak Bersih & Akses Peralatan Atas

Dokumen ini mendokumentasikan spesifikasi kebutuhan untuk restrukturisasi tata letak antarmuka pengguna VidStamp, yang berfokus pada efisiensi layar (screen real estate) dengan menyingkirkan panel kiri dan memusatkan peralatan navigasi serta ekstraksi di bagian menu atas.

## 1. Perubahan Tata Letak Utama (Layout)
* **Status**: Direncanakan
* **Deskripsi**: Menghapus widget `LeftBrowserPanel` dari `self.paned_window`. RightPlayerPanel akan dikemas langsung ke root window (`self.root`) secara penuh (`fill="both", expand=True`).
* **Manfaat**: Pemutar video akan mendapatkan area visual maksimum, mempermudah pengguna untuk melihat adegan detail dan teks pratinjau subtitel.

## 2. Fitur Navigasi Video Atas
* **Tombol "Buka Video"**:
  * Pemicu: Klik tombol "Buka Video" di kiri atas `top_bar`.
  * Aksi: Menampilkan dialog pemilihan file (`filedialog.askopenfilename`).
  * Hasil: Memuat file video terpilih ke pemutar, dan mengisi daftar dropdown episode dengan file video lain yang berada di folder yang sama.
* **Tombol "Buka Folder"**:
  * Pemicu: Klik tombol "Buka Folder" di kiri atas `top_bar`.
  * Aksi: Menampilkan dialog pemilihan folder (`filedialog.askdirectory`).
  * Hasil: Mencari seluruh berkas video yang didukung di folder tersebut, mengisi dropdown episode, dan secara otomatis memuat video pertama.
* **Dropdown "Pilih Video" (Combobox)**:
  * Lokasi: Di sebelah kanan tombol Buka Folder di `top_bar`.
  * Perilaku: Menampilkan nama-nama berkas video di folder aktif saat ini. Memilih nama berkas dari dropdown akan langsung memuat video tersebut ke pemutar.

## 3. Akses Peralatan & Ekstraksi Subtitle Atas
* **Menu "Peralatan"**:
  * Harus diperbaiki dengan menghapus parameter warna tidak standar (`bg`, `fg`, `activebackground`) pada instansiasi `tk.Menu` agar dirender dengan benar secara native oleh Windows Win32 API.
  * **Penyatuan Seluruh Pengaturan Overlay & Konfigurasi**: Untuk meminimalkan clutter visual pada `top_bar`, seluruh checkbox toggle overlay dan pengaturan skip OP/ED dipindahkan ke dalam menu "Peralatan" ini sebagai menu interaktif (`add_checkbutton` & `add_command`):
    1. **Tampilkan Timestamp** (Checkbutton): Menampilkan/menyembunyikan overlay durasi berjalan.
    2. **Detail Milidetik (ms)** (Checkbutton): Menampilkan/menyembunyikan detail milidetik pada timestamp.
    3. **Tampilkan Subtitel Overlay** (Checkbutton, Default: Nonaktif): Menampilkan/menyembunyikan render teks subtitle manual via OpenCV.
    4. **Aktifkan Auto-Skip OP/ED** (Checkbutton): Menyalakan/mematikan pemotongan lompat Opening/Ending otomatis selama playback.
    5. **Set Skip OP/ED Manual...** (Command): Membuka dialog form pengaturan durasi OP/ED untuk berkas video aktif.
    6. **Batch Merger Wizard (Ctrl+M)** (Command): Penggabungan segmen video massal.
    7. **Ekstraktor Subtitle & Audio** (Command): Ekstraksi asinkron track audio/sub.
    8. **Buka Folder Catatan** (Command): Membuka folder ekspor catatan adegan (`_catatan_adegan.txt`) aktif saat ini di Windows Explorer.

## 4. Struktur Data Baru di Controller & View
* `self.video_list` (list string): Daftar path absolut seluruh video di folder aktif saat ini.
* `self.current_folder` (string): Path folder aktif saat ini.
* `self.video_select_combo` (ttk.Combobox): Widget dropdown di `top_bar` untuk memilih video dari `self.video_list`.

## 5. Kontrol Tampilan Overlay & Subtitel Cerdas
* **Checkbutton "Subtitel" (Live Preview Toggle)**:
  * Status Default: Nonaktif (`BooleanVar(value=False)`).
  * Perilaku: Mencegah penggambaran teks subtitle manual menggunakan `cv2.putText` di atas canvas video ketika pemutaran berlangsung. Hal ini memberikan kenyamanan maksimal bagi pengguna yang menonton video MKV dengan hardsubs bawaan (misalnya rilis Kusonime) agar tidak terjadi penumpukan teks. Jika dicentang, teks subtitle hasil ekstraksi akan digambar ulang secara manual.
* **Pemicu Refresh Instan (Instant Refresh Trigger)**:
  * Aksi: Menghubungkan seluruh checkbox overlay (`Timestamp`, `ms`, `Subtitel`) ke fungsi `self.render_current_frame`.
  * Hasil: Ketika status checkbox diubah oleh pengguna, tampilan video canvas langsung menyegarkan overlay detik dan subtitle-nya saat itu juga (real-time) tanpa harus memutar video terlebih dahulu.

## 6. Toggle Kontrol pada Mode Layar Penuh (Fullscreen Overlay Toggle)
* **Penyembunyian Default**: Saat memasuki mode layar penuh (`F11` / Double Click), seluruh bar kontrol (`top_bar`, `seek_frame`, `ctrl_panel`, `inf_bar`, dll.) akan disembunyikan untuk memberikan visual penuh film (*borderless immersive mode*).
* **Toggle Tampilan**:
  * Pemicu: Pengguna menekan tombol **`Tab`** atau melakukan **Klik Kiri (Left Click)** pada area video canvas.
  * Perilaku:
    * Jika bar kontrol sedang disembunyikan, tampilkan kembali (`pack` ulang di atas dan di bawah canvas video) sehingga pengguna dapat menggunakan tombol navigasi, seek bar, mengubah kecepatan, atau mengganti episode *tanpa harus keluar dari mode fullscreen*.
    * Jika bar kontrol sedang ditampilkan, sembunyikan kembali (`pack_forget`) untuk kembali ke visual bersih.
  * Catatan Play/Pause: Untuk menghindari konflik, klik kiri pada area video hanya memicu toggle kontrol saat fullscreen aktif. Play/Pause dalam mode fullscreen dialihkan sepenuhnya ke tombol **`Space`** (Spasi) global.


