# CODEBASE.md — Peta Kode Lengkap VidStamp

> **Tujuan file ini**: Memberikan referensi cepat bagi AI agar tidak perlu membuka file sumber untuk memahami struktur, fungsi, dan dependensi antar modul. Baca file ini di awal sesi sebelum melakukan perubahan kode.
>
> **Lokasi**: `.agents/CODEBASE.md`
> **Diperbarui**: 2026-07-27

---

## 📦 Struktur Paket `vidstamp/`

```
vidstamp/
├── __main__.py         # Entry point (python -m vidstamp)
├── __init__.py         # Marker paket
├── config.py           # Konstanta global (warna, font, ekstensi, ROOT_DIRS)
├── core/
│   ├── player.py       # Engine pemutar video+audio (OpenCV + ffpyplayer)
│   └── subtitle.py     # Ekstraktor & parser subtitle MKV/SRT
├── ui/
│   ├── main_window.py  # Koordinator jendela utama + event loop pemutaran
│   ├── player_view.py  # Panel kanan: Canvas video + kontrol + catatan adegan
│   └── browser.py      # Panel kiri: Navigasi folder & daftar file video
└── utils/
    ├── file_manager.py  # I/O JSON: skip config, playback state, scenes data
    ├── logger.py        # Crash logger global (sys.excepthook + Tkinter handler)
    ├── path_helper.py   # Deteksi path FFmpeg & resource (PyInstaller-aware)
    ├── text_cleaner.py  # Pembersih teks nama file untuk label catatan
    └── time_formatter.py # Format waktu HH:MM:SS + hitung mundur
```

---

## 🔍 Referensi Cepat Per File

---

### `vidstamp/__main__.py`
**Fungsi**: Entry point. Menambahkan parent dir ke `sys.path` secara dinamis, menginisialisasi logger global, lalu memanggil `start_gui()`.
```python
# Cara menjalankan:
python -m vidstamp
python -m vidstamp "E:\ANIME\video.mkv"  # Buka langsung ke file/folder
```

---

### `vidstamp/config.py`
**Fungsi**: Konstanta global yang diimpor oleh seluruh modul UI dan rendering.
| Konstanta | Tipe | Nilai/Keterangan |
|---|---|---|
| `VIDEO_EXTS` | `set` | Ekstensi video yang didukung |
| `COLOR_TS` | `tuple BGR` | Warna teks timestamp di canvas |
| `COLOR_MARK` | `tuple BGR` | Warna teks mark START |
| `COLOR_END` | `tuple BGR` | Warna teks mark END |
| `COLOR_BG` | `tuple BGR` | Warna bayangan teks (hitam) |
| `FONT` | `int` | `cv2.FONT_HERSHEY_DUPLEX` (nilai `2`) |
| `ROOT_DIRS` | `list` | Direktori pencarian video default (`E:\ANIME`, `~/Videos`) |

---

### `vidstamp/core/player.py` — `VideoPlayerEngine`
**Fungsi**: Mesin pemutaran video menggunakan OpenCV untuk frame decoding dan ffpyplayer untuk audio. Sinkronisasi dilakukan berdasarkan PTS (Presentation Timestamp) audio.

**State Variables Kunci:**
| Atribut | Tipe | Keterangan |
|---|---|---|
| `self.cap` | `cv2.VideoCapture` | Stream video OpenCV, `None` jika belum dimuat |
| `self.audio_player` | `MediaPlayer` | Audio player ffpyplayer, `None` jika tidak ada audio |
| `self.fps` | `float` | Frame per detik video (default 30.0) |
| `self.total_frames` | `int` | Total frame video |
| `self.cur_idx` | `int` | Indeks frame yang sedang aktif (**pelacakan manual in-memory**) |
| `self.playing` | `bool` | Status pemutaran |
| `self.speed` | `float` | Kecepatan putar (default 1.0) |
| `self._seek_target` | `int\|None` | Antrean seek, diproses di iterasi `get_next_frame()` berikutnya |

**API Publik:**
```python
engine.load(path: str) -> bool          # Muat video, reset semua state
engine.set_playing(state: bool)         # Play/Pause (sinkron dengan audio)
engine.set_speed(val: float)            # Ubah kecepatan
engine.seek_to(frame_idx: int)          # Seek ke frame tertentu
engine.get_next_frame() -> (bool, frame) # Ambil frame berikutnya (dipanggil di loop)
engine.read_single_frame(idx) -> frame  # Baca frame tanpa geser posisi playback
engine.release()                        # Tutup semua stream
```

**Catatan Penting (Anti-Stuttering Optimization):**
- `cur_idx` diperbarui secara **manual** (bukan via `cap.get()`), untuk menghindari latency query ke backend OS.
- Di `get_next_frame()`: jika ada seek target → set ke target; jika ada desync audio > 6 frame → re-seek; jika normal → `target_idx = cur_idx + 1`.
- `read_single_frame()` mengembalikan posisi cap ke `cur_idx + 1` setelah dibaca.

---

### `vidstamp/core/subtitle.py`
**Fungsi**: Mengekstrak subtitle dari MKV dan memparse file SRT.

**API Publik:**
```python
parse_srt_timestamp(ts_str: str) -> float         # "01:23:45,678" -> 5025.678
parse_srt_file(srt_path: str) -> list[dict]       # -> [{'start':f, 'end':f, 'text':str}]
extract_mkv_subtitles(video_path, temp_srt) -> bool  # Ekstrak via FFmpeg subprocess
get_subtitles_in_range(subs, start, end) -> list  # Filter subtitle dalam rentang waktu
find_external_subtitle(video_path) -> str|None    # Cari .srt / _clean.srt di folder video
```

**Catatan**: `extract_mkv_subtitles` menggunakan `get_ffmpeg_path()` dari `path_helper.py`. Pada Windows, window CMD hitam disembunyikan via `STARTUPINFO`.

---

### `vidstamp/ui/main_window.py` — `VideoAppController`
**Fungsi**: Controller pusat. Mengelola PanedWindow (kiri/kanan), event binding keyboard, loop pemutaran, dan auto-save.

**State Variables Kunci:**
| Atribut | Keterangan |
|---|---|
| `self.engine` | Referensi ke `VideoPlayerEngine` |
| `self.left_panel` | Referensi ke `LeftBrowserPanel` |
| `self.right_panel` | Referensi ke `RightPlayerPanel` |
| `self.browser_visible` | Bool visibilitas panel kiri |
| `self.skipped_op / skipped_ed` | Flag satu kali skip OP/ED per video |
| `self.temp_srt_path` | Path file SRT temporer di home dir |

**Fungsi Kunci:**
```python
load_video(video_path)    # Muat video + subtitle + skip config + resume state
toggle_browser()          # Tampilkan/sembunyikan panel kiri
playback_loop()           # Loop via root.after(); mengupdate frame, lbl_cur, lbl_tot, seekbar
_start_auto_save_loop()   # Auto-save posisi tiap 5 detik
quit_app()                # Simpan state + release engine + tutup
```

**Label Waktu di Playback Loop:**
- `lbl_cur` (kiri, merah) → `format_time(cur_sec)` → **HH:MM:SS** (hitung maju)
- `lbl_tot` (kanan, cyan) → `format_remaining(cur_sec, total_sec)` → **-HH:MM:SS** (hitung mundur)

**Keyboard Shortcuts (binding di `_bind_global_shortcuts`):**
| Key | Aksi |
|---|---|
| `Space` | Play/Pause |
| `←` / `→` | ±1 detik |
| `Shift+←` / `Shift+→` | ±10 detik |
| `Tab` | Toggle browser |
| `F11` | Fullscreen |
| `Escape` | Keluar fullscreen |
| `Ctrl+T` | Mark Start → Mark End → Save |
| `Ctrl+Space` | Batal rekam |
| `Q` | Quit |

---

### `vidstamp/ui/player_view.py` — `RightPlayerPanel(tk.Frame)`
**Fungsi**: Panel kanan seluruh UI player: canvas video, seekbar, kontrol, catatan adegan.

**State Variables Kunci:**
| Atribut | Keterangan |
|---|---|
| `self.engine` | Referensi ke VideoPlayerEngine |
| `self._seeking` | Bool; True saat user drag seekbar |
| `self.mark_start / mark_end` | Detik float; posisi awal/akhir adegan yg ditandai |
| `self.scenes` | List tuple `(start_sec, end_sec, label, subtitle_text)` |
| `self.subtitle_list` | List dict subtitle yang aktif dari video saat ini |
| `self.is_fullscreen` | Bool state fullscreen |
| `self.skip_overlay_text` | Teks notifikasi skip OP/ED yang ditampilkan di canvas |
| `self.skip_overlay_timer` | Counter frame notifikasi skip (dikurangi per frame) |
| `self.show_ts` | BooleanVar; toggle tampilan timestamp overlay di canvas |
| `self.show_ms` | BooleanVar; (legacy, tidak aktif digunakan setelah format HH:MM:SS) |
| `self.auto_skip` | BooleanVar; toggle auto-skip OP/ED |
| `self.op_start/end, ed_start/end` | Detik float; batas waktu OP/ED untuk auto-skip |

**Fungsi Rendering Kunci:**
```python
draw_frame(frame)           # Gambar frame ke Canvas (resize proporsional, overlay timestamp/mark/skip)
render_current_frame()      # Baca engine.cur_idx → read_single_frame() → draw_frame()
```

**Catatan Penting (Optimasi):**
- `draw_frame()` TIDAK memanggil `update_idletasks()` — ini sengaja dihapus untuk anti-stuttering.
- Dimensi Canvas dibaca langsung via `winfo_width()/winfo_height()` dengan fallback 760x428.
- Interpolasi resize: `cv2.INTER_NEAREST` (tercepat).

**Fungsi Catatan Adegan:**
```python
mark_start_action()         # Set mark_start ke detik saat ini
mark_end_action()           # Set mark_end ke detik saat ini
save_scene_action()         # Dialog nama → append ke self.scenes → save JSON + auto-export TXT
load_saved_scenes()         # Muat scenes.json ke listbox (dipanggil saat video dimuat)
_auto_export_scenes()       # Ekspor otomatis ke [video]_catatan_adegan.txt
_del_sc() / _jump_sc()      # Hapus / lompat ke adegan terpilih
_exp_sc()                   # Ekspor manual via dialog saveas
```

---

### `vidstamp/ui/browser.py` — `LeftBrowserPanel(tk.Frame)`
**Fungsi**: Panel kiri navigasi folder dan pemilihan file video.
- Daftar folder dan file video dalam direktori aktif.
- Double-klik file → panggil `on_video_select_callback(path)`.
- Highlight file video yang sedang diputar.

---

### `vidstamp/utils/file_manager.py`
**Fungsi**: Seluruh operasi I/O JSON untuk penyimpanan status dan konfigurasi.

**Sistem Folder Catatan**: Setiap video memiliki folder catatan `[NamaVideo]_Catatan/` di direktori yang sama.

**API Publik:**
```python
ensure_note_folder(video_path) -> str   # Buat/dapatkan path folder catatan video
load_skip_config(video_path) -> dict    # Baca skip_config.json (atau season template)
save_skip_config(video_path, data, as_template=False) -> bool  # Simpan konfigurasi skip
load_playback_state(video_path) -> dict  # Baca {'last_position_sec': float}
save_playback_state(video_path, sec) -> bool  # Simpan posisi terakhir
load_scenes_data(video_path) -> list    # Baca scenes.json -> list of dict
save_scenes_data(video_path, scenes_list) -> bool  # Simpan list tuple -> scenes.json
```

**Struktur File JSON yang Dihasilkan:**
- `skip_config.json`: `{op_start, op_end, ed_start, ed_end, auto_skip_enabled}`
- `season_skip_template.json`: Format sama, berlaku untuk seluruh folder season
- `playback_state.json`: `{last_position_sec: float}`
- `scenes.json`: `[{start, end, label, subtitles}]`

---

### `vidstamp/utils/logger.py`
**Fungsi**: Crash logger global. Dipanggil satu kali di `__main__.py` saat startup.

```python
init_logger()                            # Set sys.excepthook ke logger + buat crash.log
register_tkinter_exception_handler(root) # Set root.report_callback_exception ke logger
show_crash_dialog(error_detail)          # Tampilkan messagebox error ke user
```
- Output log: `crash.log` di CWD aplikasi.
- Format: timestamp + stack trace lengkap.

---

### `vidstamp/utils/path_helper.py`
**Fungsi**: Abstraksi path yang bekerja baik di dev (source) maupun setelah dikompilasi PyInstaller.

```python
get_resource_path(relative_path) -> str  # sys._MEIPASS (EXE) atau CWD (dev)
get_ffmpeg_path() -> str                 # Urutan: _MEIPASS/bin → ./bin/win/ → PATH sistem
```

---

### `vidstamp/utils/text_cleaner.py`
**Fungsi**: Utilitas penamaan label catatan dari nama file video.

```python
get_first_4_words(filename) -> str  # Ambil 4 kata pertama dari nama file (tanpa ekstensi, tanpa simbol)
# Contoh: "[Kusonime] Solo.Leveling.S02E01.mkv" -> "Kusonime Solo Leveling S02E01"
```

---

### `vidstamp/utils/time_formatter.py`
**Fungsi**: Format waktu untuk tampilan label dan overlay canvas.

```python
format_time(sec: float, ms=False) -> str       # float -> "HH:MM:SS" (hitung maju, kiri)
format_remaining(current, total) -> str         # float, float -> "-HH:MM:SS" (hitung mundur, kanan)
```

---

## 🔗 Dependency Map (Siapa Mengimpor Apa)

```
__main__.py
    └── utils/logger.py (init_logger)
    └── ui/main_window.py (start_gui)

ui/main_window.py
    ├── config.py (ROOT_DIRS)
    ├── utils/time_formatter.py (format_time, format_remaining)
    ├── core/subtitle.py (extract_mkv_subtitles, parse_srt_file, find_external_subtitle)
    ├── core/player.py (VideoPlayerEngine)
    ├── ui/browser.py (LeftBrowserPanel)
    ├── ui/player_view.py (RightPlayerPanel)
    └── utils/file_manager.py (load_skip_config)

ui/player_view.py
    ├── config.py (FONT, COLOR_*)
    ├── utils/time_formatter.py (format_time, format_remaining)
    ├── utils/text_cleaner.py (get_first_4_words)
    ├── utils/file_manager.py (ensure_note_folder, save_skip_config, save/load_scenes_data)
    └── core/subtitle.py (get_subtitles_in_range)

core/subtitle.py
    └── utils/path_helper.py (get_ffmpeg_path) [lazy import]

utils/file_manager.py
    └── (tidak ada import internal vidstamp)

utils/logger.py
    └── (tidak ada import internal vidstamp)
```

---

## 📁 File Data Runtime (Bukan Kode)

| File | Lokasi | Keterangan |
|---|---|---|
| `crash.log` | Root CWD | Log error global, ditulis otomatis |
| `skip_config.json` | `[Folder Video]/[NamaVideo]_Catatan/` | Konfigurasi skip OP/ED per video |
| `season_skip_template.json` | `[Folder Video]/` | Template skip untuk seluruh season |
| `playback_state.json` | `[Folder Video]/[NamaVideo]_Catatan/` | Posisi pemutaran terakhir |
| `scenes.json` | `[Folder Video]/[NamaVideo]_Catatan/` | Database adegan terstruktur |
| `[video]_catatan_adegan.txt` | `[Folder Video]/[NamaVideo]_Catatan/` | Ekspor teks catatan adegan |
| `temp_video_sub.srt` | `~/` (home dir) | SRT temporer hasil ekstraksi MKV |

---

## ⚠️ Catatan Penting untuk AI saat Melakukan Perubahan

1. **Jangan hapus `update_idletasks()`** yang ada di `toggle_fullscreen()` (player_view.py baris ~287) — ini berbeda dengan yang ada di `draw_frame()`. Yang di fullscreen memang diperlukan agar layout widget terbaca dengan benar setelah state berubah.
2. **`cur_idx` adalah source of truth** posisi frame — jangan gunakan `cap.get(cv2.CAP_PROP_POS_FRAMES)` di loop baru.
3. **Selalu sinkronkan `lbl_cur` + `lbl_tot`** bersamaan — keduanya bergantung pada `cur_sec` dan `total_sec`.
4. **`scenes` di `player_view.py`** adalah `list of tuple` `(float, float, str, str)`, bukan list of dict. Konversi ke dict terjadi di `save_scenes_data()`.
5. **Skip OP/ED** menggunakan flag `skipped_op / skipped_ed` di `main_window.py` — reset otomatis jika user seek mundur sebelum `op_start`.
