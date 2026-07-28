"""
vidstamp/core/exporter.py - Logika pemotongan video, deteksi chapter, dan pergeseran subtitel
"""
import os
import re
import sys
import json
import subprocess
import time
from vidstamp.utils.path_helper import get_ffmpeg_path, get_ffprobe_path

# Kata kunci chapter skip (Opening & Ending)
SKIP_KEYWORDS_OP = ["opening", "op ", "op1", "op2", "op3", "lagu pembuka", "theme"]
SKIP_KEYWORDS_ED = ["ending", "ed ", "ed1", "ed2", "ed3", "lagu penutup", "closing"]

def get_mkv_chapters(file_path):
    """
    Membaca daftar bab (chapters) dari file MKV dan mencoba mengidentifikasi
    waktu Opening (OP) dan Ending (ED).
    """
    ffprobe_exe = get_ffprobe_path()
    if not file_path.lower().endswith('.mkv'):
        return {}
        
    try:
        cmd = [
            ffprobe_exe, "-v", "error", "-show_chapters", "-print_format", "json", file_path
        ]
        sub_kw = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.DEVNULL,
            'encoding': 'utf-8',
            'errors': 'replace'
        }
        if os.name == 'nt': 
            sub_kw['creationflags'] = 0x08000000
            
        res = subprocess.run(cmd, **sub_kw, timeout=10)
        data = json.loads(res.stdout)
        
        raw_chapters = data.get("chapters", [])
        if not raw_chapters:
            return {}
            
        op_start, op_end = None, None
        ed_start, ed_end = None, None
        
        for rc in raw_chapters:
            title = rc.get("tags", {}).get("title", "").lower()
            start = float(rc.get("start_time", 0.0))
            end = float(rc.get("end_time", 0.0))
            
            # Cek Opening
            if op_start is None and any(kw in title for kw in SKIP_KEYWORDS_OP):
                op_start = start
                op_end = end
            # Cek Ending
            elif ed_start is None and any(kw in title for kw in SKIP_KEYWORDS_ED):
                ed_start = start
                ed_end = end
                
        result = {}
        if op_start is not None and op_end is not None:
            result["op_start"] = op_start
            result["op_end"] = op_end
        if ed_start is not None and ed_end is not None:
            result["ed_start"] = ed_start
            result["ed_end"] = ed_end
            
        return result
    except Exception as e:
        print(f"Gagal membaca bab dari MKV: {e}")
        return {}

def get_video_duration(file_path):
    """Mendapatkan total durasi video dalam detik menggunakan ffprobe."""
    ffprobe_exe = get_ffprobe_path()
    try:
        cmd = [
            ffprobe_exe, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        sub_kw = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.DEVNULL,
            'encoding': 'utf-8',
            'errors': 'replace'
        }
        if os.name == 'nt': 
            sub_kw['creationflags'] = 0x08000000
        res = subprocess.run(cmd, **sub_kw, timeout=10)
        return float(res.stdout.strip())
    except Exception as e:
        print(f"Gagal mendeteksi durasi video: {e}")
        return 0.0

def srt_time_to_seconds(time_str):
    """Mengonversi string waktu SRT (HH:MM:SS,mmm) ke detik float."""
    match = re.match(r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})", time_str.strip())
    if not match:
        return 0.0
    h, m, s, ms = map(int, match.groups())
    return h * 3600 + m * 60 + s + ms / 1000.0

def seconds_to_srt_time(total_seconds):
    """Mengonversi detik float ke format waktu SRT (HH:MM:SS,mmm)."""
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int(round((total_seconds - int(total_seconds)) * 1000))
    if milliseconds >= 1000:
        seconds += 1
        milliseconds -= 1000
    if seconds >= 60:
        minutes += 1
        seconds -= 60
    if minutes >= 60:
        hours += 1
        minutes -= 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def clean_srt_text(raw_text):
    """Membersihkan format tag ASS/HTML dari teks SRT."""
    text = re.sub(r'\{[^}]*\}', '', raw_text)
    text = re.sub(r'<[^>]*>', '', text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    cleaned = "\n".join(lines).strip()
    return cleaned

def cut_and_shift_srt(input_srt_path, keep_ranges, output_srt_path):
    """
    Membaca berkas SRT input, mempertahankan subtitle yang masuk dalam keep_ranges,
    menggeser waktunya agar selaras dengan video baru yang terpotong,
    dan menyimpannya ke berkas SRT output.
    """
    if not os.path.exists(input_srt_path):
        return False
        
    try:
        with open(input_srt_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        if content.startswith('\ufeff'):
            content = content[1:]
            
        # Pisahkan blok berdasarkan baris kosong ganda atau baris kosong tunggal yang memisahkan angka indeks
        blocks = re.split(r'\n\s*\n', content.strip())
        shifted_blocks = []
        current_index = 1
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 2:
                ts_line_idx = -1
                for idx, line in enumerate(lines):
                    if "-->" in line:
                        ts_line_idx = idx
                        break
                        
                if ts_line_idx != -1:
                    dialogue_lines = lines[ts_line_idx+1:]
                    clean_text = clean_srt_text("\n".join(dialogue_lines))
                    
                    if clean_text:
                        ts_line = lines[ts_line_idx]
                        parts = ts_line.split("-->")
                        if len(parts) == 2:
                            start_sec = srt_time_to_seconds(parts[0])
                            end_sec = srt_time_to_seconds(parts[1])
                            
                            mapped_start = None
                            mapped_end = None
                            
                            acc_keep_duration = 0.0
                            for k_start, k_end in keep_ranges:
                                # Jika timestamp dialog masuk dalam rentang segmen ini
                                if k_start <= start_sec < k_end:
                                    mapped_start = (start_sec - k_start) + acc_keep_duration
                                    mapped_end = (end_sec - k_start) + acc_keep_duration
                                    break
                                acc_keep_duration += (k_end - k_start)
                                
                            if mapped_start is not None and mapped_end is not None:
                                new_ts_line = f"{seconds_to_srt_time(mapped_start)} --> {seconds_to_srt_time(mapped_end)}"
                                block_str = f"{current_index}\n{new_ts_line}\n{clean_text}"
                                shifted_blocks.append(block_str)
                                current_index += 1
                                
        with open(output_srt_path, 'w', encoding='utf-8') as out_f:
            out_f.write("\n\n".join(shifted_blocks))
        return True
    except Exception as e:
        print(f"Gagal menyelaraskan subtitel: {e}")
        return False

def escape_path_for_ffmpeg_filter(path):
    """Mengamankan path berkas agar kompatibel dengan filter complex FFmpeg."""
    safe_path = path.replace("\\", "/")
    safe_path = safe_path.replace(":", "\\:")
    safe_path = safe_path.replace("'", "'\\\\''")
    safe_path = safe_path.replace(",", "\\,")
    return safe_path

def run_ffmpeg_process(cmd, total_duration, progress_callback=None, cancel_event=None):
    """
    Menjalankan proses FFmpeg dan membaca stderr secara real-time untuk memperbarui progress bar.
    """
    sub_kw = {
        'stdin': subprocess.DEVNULL,
        'stdout': subprocess.DEVNULL,
        'stderr': subprocess.PIPE,
        'universal_newlines': True,
        'encoding': 'utf-8',
        'errors': 'replace'
    }
    if os.name == 'nt':
        sub_kw['creationflags'] = 0x08004000 # CREATE_NO_WINDOW
        
    process = subprocess.Popen(cmd, **sub_kw)
    time_regex = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})[.,](\d{2})")
    
    try:
        while True:
            # Cek pembatalan oleh pengguna
            if cancel_event and cancel_event.is_set():
                process.terminate()
                return False, "Dibatalkan oleh pengguna"
                
            line = process.stderr.readline()
            if not line:
                break
                
            time_match = time_regex.search(line)
            if time_match and total_duration > 0 and progress_callback:
                h, m, s, ms = time_match.groups()
                processed_seconds = int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 100.0
                percentage = min(100.0, (processed_seconds / total_duration) * 100)
                progress_callback(percentage)
                
        process.wait()
        if process.returncode == 0:
            return True, "Sukses"
        else:
            return False, f"FFmpeg keluar dengan kode error: {process.returncode}"
    except Exception as e:
        process.terminate()
        return False, str(e)

def export_clean_video_and_srt(video_path, op_start, op_end, ed_start, ed_end, output_video_path, output_srt_path, mode="softsub", progress_callback=None, cancel_event=None):
    """
    Fungsi utama untuk melakukan pemotongan video (dan hardsub jika dipilih) serta penyelarasan subtitel.
    """
    ffmpeg_exe = get_ffmpeg_path()
    total_duration = get_video_duration(video_path)
    if total_duration <= 0.0:
        return False, "Gagal mendeteksi durasi video asli."
        
    # Hitung keep ranges berdasarkan skip ranges
    skip_ranges = []
    if op_start is not None and op_end is not None:
        skip_ranges.append((op_start, op_end))
    if ed_start is not None and ed_end is not None:
        skip_ranges.append((ed_start, ed_end))
        
    # Buat keep ranges
    keep_ranges = []
    current = 0.0
    for s_start, s_end in sorted(skip_ranges):
        if s_start > current:
            keep_ranges.append((current, s_start))
        current = max(current, s_end)
    if current < total_duration:
        keep_ranges.append((current, total_duration))
        
    if not keep_ranges:
        return False, "Tidak ada bagian video yang tersisa untuk disimpan!"
        
    total_keep_duration = sum(end - start for start, end in keep_ranges)
    
    # 1. Penyelarasan Subtitel
    # Cari berkas SRT eksternal, atau ekstrak dari mkv jika ada
    temp_extract_srt = output_srt_path + ".temp_extract.srt"
    srt_to_shift = None
    
    # Deteksi srt eksternal
    from vidstamp.core.subtitle import find_external_subtitle, extract_mkv_subtitles
    external_srt = find_external_subtitle(video_path)
    
    if external_srt:
        srt_to_shift = external_srt
    elif video_path.lower().endswith('.mkv'):
        # Ekstrak subtitle internal ke temp
        if extract_mkv_subtitles(video_path, temp_extract_srt):
            srt_to_shift = temp_extract_srt
            
    # Selaraskan subtitle
    srt_success = False
    if srt_to_shift:
        srt_success = cut_and_shift_srt(srt_to_shift, keep_ranges, output_srt_path)
        if os.path.exists(temp_extract_srt):
            try: os.remove(temp_extract_srt)
            except: pass
            
    # 2. Pemotongan Video & Audio via FFmpeg
    # Bangun filter complex concat
    filter_v_nodes = []
    filter_a_nodes = []
    for idx, (start, end) in enumerate(keep_ranges):
        filter_v_nodes.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{idx}]")
        filter_a_nodes.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{idx}]")
        
    concat_inputs = "".join(f"[v{k}][a{k}]" for k in range(len(keep_ranges)))
    concat_node = f"{concat_inputs}concat=n={len(keep_ranges)}:v=1:a=1[v_cut][a_cut]"
    
    # Hardsub atau Softsub
    if mode == "hardsub" and srt_success and os.path.exists(output_srt_path):
        srt_escaped = escape_path_for_ffmpeg_filter(output_srt_path)
        subtitle_node = f"[v_cut]subtitles='{srt_escaped}'[v_final]"
        filter_complex = "; ".join(filter_v_nodes + filter_a_nodes) + "; " + concat_node + "; " + subtitle_node
        map_video = "[v_final]"
    else:
        filter_complex = "; ".join(filter_v_nodes + filter_a_nodes) + "; " + concat_node
        map_video = "[v_cut]"
        
    cmd = [
        ffmpeg_exe, "-y", "-i", video_path,
        "-filter_complex", filter_complex,
        "-map", map_video, "-map", "[a_cut]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        output_video_path
    ]
    
    # Jalankan render FFmpeg
    success, msg = run_ffmpeg_process(cmd, total_keep_duration, progress_callback, cancel_event)
    return success, msg
