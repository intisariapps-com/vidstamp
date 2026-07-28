---
name: mkv-ffmpeg-processing
description: Prosedur pemrosesan video MKV, ekstraksi subtitle, deteksi bab, dan pemotongan (trimming) menggunakan FFmpeg/FFprobe.
---

# Panduan Pemrosesan Video & Subtitel dengan FFmpeg/FFprobe

Dokumen ini mendokumentasikan praktik terbaik untuk berinteraksi dengan subprocess FFmpeg dan FFprobe secara aman dari dalam aplikasi Python (VidStamp).

## 1. Deteksi Jalur Biner FFmpeg Dinamis
Untuk kompatibilitas bundling portable (PyInstaller), gunakan helper path untuk mencari biner `ffmpeg` dan `ffprobe` di sistem atau di direktori instalan `bin/`:

```python
import os
import sys

def get_ffmpeg_path(binary_name="ffmpeg"):
    # Cek jika berjalan dalam mode PyInstaller bundle
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    # Cari di folder bin/win/ (Windows) atau bin/mac/ (macOS)
    subfolder = "win" if os.name == "nt" else "mac"
    ext = ".exe" if os.name == "nt" else ""
    
    local_path = os.path.join(base_dir, "bin", subfolder, f"{binary_name}{ext}")
    if os.path.exists(local_path):
        return local_path
        
    # Fallback ke biner sistem PATH
    return binary_name
```

## 2. Deteksi Bab MKV Otomatis (FFprobe)
Gunakan `ffprobe` dengan format keluaran JSON untuk memindai chapter/bab dalam kontainer `.mkv`:

```bash
ffprobe -v error -show_chapters -print_format json "nama_video.mkv"
```

Implementasi Python dengan subprocess yang aman (tanpa console window muncul di Windows):

```python
import subprocess
import json

def get_video_chapters(video_path):
    ffprobe_path = get_ffmpeg_path("ffprobe")
    cmd = [
        ffprobe_path,
        "-v", "error",
        "-show_chapters",
        "-print_format", "json",
        video_path
    ]
    
    # Sembunyikan jendela cmd di Windows
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo, encoding="utf-8")
    if result.returncode == 0:
        return json.loads(result.stdout).get("chapters", [])
    return []
```

## 3. Ekstraksi Subtitel MKV (FFmpeg)
Ekstrak trek subtitel internal (biasanya indeks subtitle `0:s:0`) ke file `.srt` eksternal secara asinkron:

```python
def extract_subtitle(video_path, output_srt_path, track_index=0):
    ffmpeg_path = get_ffmpeg_path("ffmpeg")
    cmd = [
        ffmpeg_path,
        "-y",
        "-i", video_path,
        "-map", f"0:s:{track_index}",
        output_srt_path
    ]
    
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    subprocess.run(cmd, startupinfo=startupinfo, check=True)
```

## 4. Pemotongan Segmen Video Bersih (Smart Cut)
Lakukan pemotongan adegan secara lossless menggunakan stream copy (`-c copy`) jika tidak membutuhkan hardsub, atau re-encoding x264 jika membutuhkan hardsub:

### Mode Potong Cepat (Lossless Copy)
```bash
ffmpeg -y -ss [start_sec] -to [end_sec] -i "input.mp4" -c copy "output.mp4"
```

### Mode Hardsub (Re-encoding)
Menyematkan subtitel langsung ke dalam aliran video. **PENTING**: Path ke berkas `.srt` dalam filter `subtitles` FFmpeg harus menggunakan backslash ganda atau slash normal yang di-escape karena FFmpeg memperlakukan string filter secara khusus.

```python
# Format filter subtitle yang kompatibel silang (Windows/macOS)
def format_subtitles_filter(srt_path):
    # Ganti backslash dengan slash normal untuk FFmpeg filter parser
    escaped_path = srt_path.replace("\\", "/").replace(":", "\\:")
    return f"subtitles='{escaped_path}'"
```
Perintah FFmpeg:
```bash
ffmpeg -y -ss [start_sec] -to [end_sec] -i "input.mp4" -vf "subtitles='path_to_sub.srt'" -c:v libx264 -crf 20 -c:a aac "output.mp4"
```
