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
  * Menyertakan aksi cepat:
    1. **Batch Merger Wizard**: Penggabungan segmen video massal.
    2. **Ekstraktor Subtitle & Audio**: Ekstraksi asinkron track audio/sub.
    3. **Buka Folder Catatan**: Membuka folder ekspor catatan adegan (`_catatan_adegan.txt`) aktif saat ini di Windows Explorer.

## 4. Struktur Data Baru di Controller & View
* `self.video_list` (list string): Daftar path absolut seluruh video di folder aktif saat ini.
* `self.current_folder` (string): Path folder aktif saat ini.
* `self.video_select_combo` (ttk.Combobox): Widget dropdown di `top_bar` untuk memilih video dari `self.video_list`.

## 5. Kontrol Tampilan Overlay & Subtitel Cerdas
* **Checkbutton "Subtitel" (Live Preview Toggle)**:
  * Lokasi: Di sebelah kanan opsi "Timestamp" pada `top_bar`.
  * Status Default: Nonaktif (`BooleanVar(value=False)`).
  * Perilaku: Mencegah penggambaran teks subtitle manual menggunakan `cv2.putText` di atas canvas video ketika pemutaran berlangsung. Hal ini memberikan kenyamanan maksimal bagi pengguna yang menonton video MKV dengan hardsubs bawaan (misalnya rilis Kusonime) agar tidak terjadi penumpukan teks. Jika dicentang, teks subtitle hasil ekstraksi akan digambar ulang secara manual.
* **Pemicu Refresh Instan (Instant Refresh Trigger)**:
  * Aksi: Menghubungkan seluruh checkbox overlay (`Timestamp`, `ms`, `Subtitel`) ke fungsi `self.render_current_frame`.
  * Hasil: Ketika status checkbox diubah oleh pengguna, tampilan video canvas langsung menyegarkan overlay detik dan subtitle-nya saat itu juga (real-time) tanpa harus memutar video terlebih dahulu.

