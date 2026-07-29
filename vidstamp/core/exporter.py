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

def merge_duplicate_ocr_subtitles(subs_list):
    """
    Menggabungkan teks subtitle berturut-turut yang identik atau sangat mirip (OCR duplicate spam).
    Dan menyatukan durasi waktunya dari start pertama hingga end terakhir.
    """
    if not subs_list:
        return []
    
    # Normalisasi teks untuk perbandingan (lowercase, hapus tag, hapus spasi/simbol berlebih)
    def normalize_text(t):
        t = t.lower()
        t = re.sub(r'<[^>]*>', '', t)
        t = re.sub(r'[\s.,\/#!$%\^&\*;:{}=\-_`~()]+', '', t)
        return t.strip()

    merged = []
    current = subs_list[0].copy()
    
    for next_sub in subs_list[1:]:
        norm_curr = normalize_text(current['text'])
        norm_next = normalize_text(next_sub['text'])
        
        # Jarak waktu antar subtitle (gap)
        gap = next_sub['start'] - current['end']
        
        # Jika teks sama dan jarak waktu sangat dekat (misal <= 2.5 detik)
        if norm_curr == norm_next and gap <= 2.5:
            # Perluas durasi subtitle saat ini
            current['end'] = max(current['end'], next_sub['end'])
        else:
            merged.append(current)
            current = next_sub.copy()
            
    merged.append(current)
    return merged

def wrap_text_by_char_limit(text, limit):
    """
    Membagi teks menjadi maksimal dua baris secara seimbang jika melebihi batas limit karakter.
    Mempertahankan kata agar tidak terpotong di tengah jalan.
    """
    if not limit or limit <= 0:
        return text
        
    # Gabungkan baris yang terpisah spasi/baris baru agar bersih
    single_line = " ".join([l.strip() for l in text.split('\n') if l.strip()])
    if len(single_line) <= limit:
        return single_line
        
    words = single_line.split()
    line1 = []
    line2 = []
    
    total_len = len(single_line)
    mid_point = total_len // 2
    
    current_len = 0
    for word in words:
        # Tumpuk ke baris pertama selama di bawah batas limit dan berada di sebelah kiri split point tengah
        if not line2 and (current_len + len(word) <= limit) and (current_len < mid_point or current_len + len(word)//2 < mid_point):
            line1.append(word)
            current_len += len(word) + 1
        else:
            line2.append(word)
            
    if line2:
        return " ".join(line1) + "\n" + " ".join(line2)
    return " ".join(line1)

def extract_mkv_ass_subtitles(video_path, temp_ass_path):
    """
    Mengekstrak trek subtitle internal pertama (0:s:0) dari berkas MKV
    ke berkas ASS temporer menggunakan subprocess FFmpeg.
    """
    if not video_path.lower().endswith('.mkv'):
        return False
        
    if os.path.exists(temp_ass_path):
        try:
            os.remove(temp_ass_path)
        except:
            pass

    ffmpeg_cmd = get_ffmpeg_path()
    cmd = [
        ffmpeg_cmd, '-y',
        '-i', video_path,
        '-map', '0:s:0',
        temp_ass_path
    ]
    
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0 # Sembunyikan window CMD hitam

    try:
        subprocess.run(
            cmd,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )
        if os.path.exists(temp_ass_path) and os.path.getsize(temp_ass_path) > 0:
            return True
    except Exception as e:
        print(f"FFmpeg ASS subtitle extraction error: {e}")
        
    return False

def ass_time_to_seconds(time_str):
    """Mengonversi format waktu ASS (H:MM:SS.cs) ke detik float."""
    parts = time_str.split(":")
    if len(parts) != 3:
        return 0.0
    h = int(parts[0])
    m = int(parts[1])
    s_parts = parts[2].split(".")
    s = int(s_parts[0])
    cs = int(s_parts[1]) if len(s_parts) > 1 else 0
    # cs adalah centiseconds (seperseratus detik)
    return h * 3600 + m * 60 + s + cs / 100.0

def seconds_to_ass_time(total_seconds):
    """Mengonversi detik float ke format waktu ASS (H:MM:SS.cs)."""
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    centiseconds = int(round((total_seconds - int(total_seconds)) * 100))
    if centiseconds >= 100:
        seconds += 1
        centiseconds -= 100
    if seconds >= 60:
        minutes += 1
        seconds -= 60
    if minutes >= 60:
        hours += 1
        minutes -= 60
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

def cut_and_shift_ass(input_ass_path, keep_ranges, output_ass_path):
    """
    Membaca berkas ASS input, mempertahankan subtitle Dialogue yang masuk dalam keep_ranges,
    menggeser waktunya agar selaras dengan video baru yang terpotong,
    dan menyimpannya ke berkas ASS output dengan gaya/format asli tetap utuh.
    """
    if not os.path.exists(input_ass_path):
        return False
        
    try:
        with open(input_ass_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
        dialogue_pattern = re.compile(r'^(Dialogue:\s*[^,]+,)([^,]+),([^,]+),(.*)$')
        shifted_lines = []
        
        for line in lines:
            match = dialogue_pattern.match(line)
            if match:
                prefix = match.group(1)
                start_str = match.group(2)
                end_str = match.group(3)
                suffix = match.group(4)
                
                try:
                    start_sec = ass_time_to_seconds(start_str)
                    end_sec = ass_time_to_seconds(end_str)
                except Exception:
                    shifted_lines.append(line)
                    continue
                
                mapped_start = None
                mapped_end = None
                
                acc_keep_duration = 0.0
                for k_start, k_end in keep_ranges:
                    if k_start <= start_sec < k_end:
                        mapped_start = (start_sec - k_start) + acc_keep_duration
                        mapped_end = (end_sec - k_start) + acc_keep_duration
                        break
                    acc_keep_duration += (k_end - k_start)
                    
                if mapped_start is not None and mapped_end is not None:
                    new_start_str = seconds_to_ass_time(mapped_start)
                    new_end_str = seconds_to_ass_time(mapped_end)
                    shifted_lines.append(f"{prefix}{new_start_str},{new_end_str},{suffix}\n")
            else:
                # Pertahankan line non-dialogue (script info, styles, dll)
                shifted_lines.append(line)
                
        with open(output_ass_path, 'w', encoding='utf-8') as f:
            f.writelines(shifted_lines)
        return True
    except Exception as e:
        print(f"Gagal menyelaraskan subtitel ASS: {e}")
        return False

def cut_and_shift_srt(input_srt_path, keep_ranges, output_srt_path, line_limit=None):
    """
    Membaca berkas SRT input, mempertahankan subtitle yang masuk dalam keep_ranges,
    menggeser waktunya agar selaras dengan video baru yang terpotong,
    mengjalankan pembersih duplikat OCR spam, membatasi panjang karakter baris,
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
        subs_list = []
        
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
                        # Terapkan pembatasan panjang karakter per baris jika diatur
                        if line_limit:
                            clean_text = wrap_text_by_char_limit(clean_text, line_limit)
                            
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
                                subs_list.append({
                                    'start': mapped_start,
                                    'end': mapped_end,
                                    'text': clean_text
                                })
                                
        # Jalankan deduplikasi OCR spam duplikat
        deduplicated_subs = merge_duplicate_ocr_subtitles(subs_list)
        
        # Konversi kembali ke format SRT
        shifted_blocks = []
        for idx, sub in enumerate(deduplicated_subs, 1):
            new_ts_line = f"{seconds_to_srt_time(sub['start'])} --> {seconds_to_srt_time(sub['end'])}"
            block_str = f"{idx}\n{new_ts_line}\n{sub['text']}"
            shifted_blocks.append(block_str)
                                
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

def export_clean_video_and_srt(video_path, op_start, op_end, ed_start, ed_end, output_video_path, output_srt_path, mode="softsub", progress_callback=None, cancel_event=None, font_size=None, line_limit=None):
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
    import uuid
    unique_suffix = uuid.uuid4().hex[:8]
    temp_extract_srt = output_srt_path + f".temp_extract_{unique_suffix}.srt"
    temp_extract_ass = output_srt_path + f".temp_extract_{unique_suffix}.ass"
    temp_shifted_ass = output_srt_path + f".temp_shifted_{unique_suffix}.ass"
    
    srt_to_shift = None
    ass_to_shift = None
    
    # Deteksi srt eksternal
    from vidstamp.core.subtitle import find_external_subtitle, extract_mkv_subtitles
    external_srt = find_external_subtitle(video_path)
    
    if external_srt:
        srt_to_shift = external_srt
    elif video_path.lower().endswith('.mkv'):
        # Ekstrak subtitle internal ke temp SRT (untuk output SRT bersih)
        if extract_mkv_subtitles(video_path, temp_extract_srt):
            srt_to_shift = temp_extract_srt
        # Ekstrak subtitle internal ke temp ASS (untuk burn native style)
        if extract_mkv_ass_subtitles(video_path, temp_extract_ass):
            ass_to_shift = temp_extract_ass
            
    # Selaraskan subtitle
    srt_success = False
    if srt_to_shift:
        srt_success = cut_and_shift_srt(srt_to_shift, keep_ranges, output_srt_path, line_limit=line_limit)
        if os.path.exists(temp_extract_srt):
            try: os.remove(temp_extract_srt)
            except: pass
            
    ass_success = False
    if ass_to_shift:
        ass_success = cut_and_shift_ass(ass_to_shift, keep_ranges, temp_shifted_ass)
        if os.path.exists(temp_extract_ass):
            try: os.remove(temp_extract_ass)
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
    # Prioritaskan menggunakan ASS (native mkv styling) untuk hardsub jika sukses diekstraksi
    if mode == "hardsub" and os.path.exists(temp_shifted_ass) and ass_success:
        srt_escaped = escape_path_for_ffmpeg_filter(temp_shifted_ass)
        # Untuk ASS, tidak perlu force_style karena font & ukuran bawaan mkv sudah didefinisikan secara presisi di file ASS
        subtitle_node = f"[v_cut]subtitles='{srt_escaped}'[v_final]"
        filter_complex = "; ".join(filter_v_nodes + filter_a_nodes) + "; " + concat_node + "; " + subtitle_node
        map_video = "[v_final]"
    elif mode == "hardsub" and srt_success and os.path.exists(output_srt_path):
        srt_escaped = escape_path_for_ffmpeg_filter(output_srt_path)
        if font_size and str(font_size).lower() != "default":
            subtitle_node = f"[v_cut]subtitles='{srt_escaped}':force_style='Fontsize={font_size},Outline=2,Shadow=0'[v_final]"
        else:
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
 
def export_bulk_and_merge(parent_dir, mode="softsub", merge_to_one=True, progress_callback=None, cancel_event=None, font_size=None, line_limit=None, video_files_list=None):
    """
    Memproses seluruh episode dalam folder: memotong OP/ED, menggeser subtitle,
    dan jika merge_to_one=True, menggabungkannya menjadi 1 file MP4 utama dan 1 file SRT global.
    """
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    from vidstamp.config import VIDEO_EXTS
    from vidstamp.utils.file_manager import load_skip_config
    from vidstamp.core.subtitle import find_external_subtitle, extract_mkv_subtitles
    
    # 1. Cari semua file video
    if video_files_list is not None:
        files = sorted(video_files_list)
    else:
        try:
            files = sorted([
                os.path.join(parent_dir, f) for f in os.listdir(parent_dir)
                if os.path.splitext(f)[1].lower() in VIDEO_EXTS and "_clean" not in f.lower()
            ])
        except Exception as e:
            return False, f"Gagal membaca isi direktori: {e}"
    
    if not files:
        return False, "Tidak ditemukan berkas video di folder tersebut."
        
    total_files = len(files)
    episode_temp_videos = []
    global_subs_list = []
    accumulated_offset = 0.0
    
    folder_name = os.path.basename(parent_dir.rstrip(r"\/"))
    output_mp4_final = os.path.join(parent_dir, f"{folder_name}_clean.mp4")
    output_srt_final = os.path.join(parent_dir, f"{folder_name}_clean.srt")
    
    ffmpeg_exe = get_ffmpeg_path()
    
    for idx, file in enumerate(files):
        if cancel_event and cancel_event.is_set():
            return False, "Dibatalkan oleh pengguna"
            
        # Update progress callback for current file start
        if progress_callback:
            progress_callback(idx, total_files, 0.0, f"Memulai {os.path.basename(file)}")
            
        # Dapatkan skip config
        skip_data = load_skip_config(file)
        op_s = skip_data.get("op_start")
        op_e = skip_data.get("op_end")
        ed_s = skip_data.get("ed_start")
        ed_e = skip_data.get("ed_end")
        
        if not skip_data and file.lower().endswith(".mkv"):
            detected = get_mkv_chapters(file)
            op_s = detected.get("op_start")
            op_e = detected.get("op_end")
            ed_s = detected.get("ed_start")
            ed_e = detected.get("ed_end")
            
        # Tentukan keep ranges
        total_duration = get_video_duration(file)
        if total_duration <= 0.0:
            continue
            
        skip_ranges = []
        if op_s is not None and op_e is not None:
            skip_ranges.append((op_s, op_e))
        if ed_s is not None and ed_e is not None:
            skip_ranges.append((ed_s, ed_e))
            
        keep_ranges = []
        current = 0.0
        for s_start, s_end in sorted(skip_ranges):
            if s_start > current:
                keep_ranges.append((current, s_start))
            current = max(current, s_end)
        if current < total_duration:
            keep_ranges.append((current, total_duration))
            
        if not keep_ranges:
            keep_ranges = [(0.0, total_duration)]
            
        total_keep_duration = sum(end - start for start, end in keep_ranges)
        
        # Proses Subtitle untuk episode ini
        base_name, ext = os.path.splitext(file)
        out_v = f"{base_name}_clean{ext}"
        out_s = f"{base_name}_clean.srt"
        
        # Cari subtitle eksternal atau internal
        import uuid
        unique_suffix = uuid.uuid4().hex[:8]
        temp_extract_srt = out_s + f".temp_extract_{unique_suffix}.srt"
        temp_extract_ass = out_s + f".temp_extract_{unique_suffix}.ass"
        temp_shifted_ass = out_s + f".temp_shifted_{unique_suffix}.ass"
        
        srt_to_shift = None
        ass_to_shift = None
        
        external_srt = find_external_subtitle(file)
        if external_srt:
            srt_to_shift = external_srt
        elif file.lower().endswith('.mkv'):
            if extract_mkv_subtitles(file, temp_extract_srt):
                srt_to_shift = temp_extract_srt
            if extract_mkv_ass_subtitles(file, temp_extract_ass):
                ass_to_shift = temp_extract_ass
                
        srt_success = False
        if srt_to_shift:
            # Shift untuk episode saat ini (selaras dengan video episode ini)
            srt_success = cut_and_shift_srt(srt_to_shift, keep_ranges, out_s, line_limit=line_limit)
            
            # Jika merger diaktifkan, kumpulkan juga sub yang di-offset secara global
            if merge_to_one:
                # Muat sub lama, geser dengan global accumulated_offset, dan tambahkan ke global list
                try:
                    with open(srt_to_shift, 'r', encoding='utf-8', errors='replace') as sf:
                        content = sf.read()
                    if content.startswith('\ufeff'): content = content[1:]
                    blocks = re.split(r'\n\s*\n', content.strip())
                    for b in blocks:
                        lines = b.strip().split('\n')
                        if len(lines) >= 2:
                            ts_line_idx = -1
                            for l_i, line in enumerate(lines):
                                if "-->" in line:
                                    ts_line_idx = l_i
                                    break
                            if ts_line_idx != -1:
                                dialogue_lines = lines[ts_line_idx+1:]
                                clean_txt = clean_srt_text("\n".join(dialogue_lines))
                                if clean_txt:
                                    if line_limit:
                                        clean_txt = wrap_text_by_char_limit(clean_txt, line_limit)
                                        
                                    parts = lines[ts_line_idx].split("-->")
                                    if len(parts) == 2:
                                        start_s = srt_time_to_seconds(parts[0])
                                        end_s = srt_time_to_seconds(parts[1])
                                        
                                        # Map ke global timeline
                                        mapped_s = None
                                        mapped_e = None
                                        acc_keep = 0.0
                                        for k_s, k_e in keep_ranges:
                                            if k_s <= start_s < k_e:
                                                mapped_s = (start_s - k_s) + acc_keep + accumulated_offset
                                                mapped_e = (end_s - k_s) + acc_keep + accumulated_offset
                                                break
                                            acc_keep += (k_e - k_s)
                                            
                                        if mapped_s is not None and mapped_e is not None:
                                            global_subs_list.append({
                                                'start': mapped_s,
                                                'end': mapped_e,
                                                'text': clean_txt
                                            })
                except Exception as ex_sub:
                    print(f"Gagal memproses global subtitle: {ex_sub}")
                    
            if os.path.exists(temp_extract_srt):
                try: os.remove(temp_extract_srt)
                except: pass
                
        ass_success = False
        if ass_to_shift:
            ass_success = cut_and_shift_ass(ass_to_shift, keep_ranges, temp_shifted_ass)
            if os.path.exists(temp_extract_ass):
                try: os.remove(temp_extract_ass)
                except: pass

        # Potong video episode ini
        filter_v_nodes = []
        filter_a_nodes = []
        for r_idx, (start, end) in enumerate(keep_ranges):
            filter_v_nodes.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{r_idx}]")
            filter_a_nodes.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{r_idx}]")
            
        concat_inputs = "".join(f"[v{k}][a{k}]" for k in range(len(keep_ranges)))
        concat_node = f"{concat_inputs}concat=n={len(keep_ranges)}:v=1:a=1[v_cut][a_cut]"
        
        # Hardsub atau Softsub
        # Prioritaskan menggunakan ASS (native mkv styling) untuk hardsub jika sukses diekstraksi
        if mode == "hardsub" and os.path.exists(temp_shifted_ass) and ass_success:
            srt_escaped = escape_path_for_ffmpeg_filter(temp_shifted_ass)
            # Untuk ASS, tidak perlu force_style karena font & ukuran bawaan mkv sudah didefinisikan secara presisi di file ASS
            subtitle_node = f"[v_cut]subtitles='{srt_escaped}'[v_final]"
            filter_complex = "; ".join(filter_v_nodes + filter_a_nodes) + "; " + concat_node + "; " + subtitle_node
            map_video = "[v_final]"
        elif mode == "hardsub" and srt_success and os.path.exists(out_s):
            srt_escaped = escape_path_for_ffmpeg_filter(out_s)
            if font_size and str(font_size).lower() != "default":
                subtitle_node = f"[v_cut]subtitles='{srt_escaped}':force_style='Fontsize={font_size},Outline=2,Shadow=0'[v_final]"
            else:
                subtitle_node = f"[v_cut]subtitles='{srt_escaped}'[v_final]"
            filter_complex = "; ".join(filter_v_nodes + filter_a_nodes) + "; " + concat_node + "; " + subtitle_node
            map_video = "[v_final]"
        else:
            filter_complex = "; ".join(filter_v_nodes + filter_a_nodes) + "; " + concat_node
            map_video = "[v_cut]"
            
        # Target output video untuk concat global jika diaktifkan
        temp_video_out = out_v if not merge_to_one else os.path.join(parent_dir, f"temp_clean_ep{idx}_{unique_id}{ext}")
        episode_temp_videos.append(temp_video_out)
        
        cmd = [
            ffmpeg_exe, "-y", "-i", file,
            "-filter_complex", filter_complex,
            "-map", map_video, "-map", "[a_cut]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            temp_video_out
        ]
        
        def sub_progress_callback(pct):
            if progress_callback:
                progress_callback(idx, total_files, pct, f"Memproses {os.path.basename(file)}")
                
        success, msg = run_ffmpeg_process(cmd, total_keep_duration, sub_progress_callback, cancel_event)
        
        # Bersihkan berkas temp ass episode ini
        if os.path.exists(temp_shifted_ass):
            try: os.remove(temp_shifted_ass)
            except: pass
            
        if not success:
            # Bersihkan berkas temp yang baru dibuat
            for tv in episode_temp_videos:
                if os.path.exists(tv):
                    try: os.remove(tv)
                    except: pass
            return False, f"Gagal pada episode {idx+1}: {msg}"
            
        accumulated_offset += total_keep_duration
        
    # Selesai memproses semua episode secara individual.
    # Jika merge_to_one diaktifkan, gabungkan sekarang!
    if merge_to_one and not (cancel_event and cancel_event.is_set()):
        if progress_callback:
            progress_callback(total_files - 1, total_files, 95.0, "Menggabungkan semua episode bersih...")
            
        # Tulis list file concat
        mylist_path = os.path.join(parent_dir, f"mylist_temp_{unique_id}.txt")
        with open(mylist_path, 'w', encoding='utf-8') as f_list:
            for temp_v in episode_temp_videos:
                # Gunakan relative path (hanya nama file saja) karena mylist_path dan temp_v berada di folder yang sama (parent_dir)
                # Ini menghindari kegagalan pembacaan unicode/spasi path absolut oleh FFmpeg di Windows
                safe_path = os.path.basename(temp_v)
                f_list.write(f"file '{safe_path}'\n")
                
        # Concat lossless
        cmd_concat_final = [
            ffmpeg_exe, "-y", "-f", "concat", "-safe", "0", "-i", mylist_path,
            "-c", "copy", output_mp4_final
        ]
        
        # Tangkap stdout dan stderr agar jika terjadi kegagalan bisa didiagnosis
        sub_kw_concat = {
            'stdin': subprocess.DEVNULL,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'encoding': 'utf-8',
            'errors': 'replace'
        }
        if os.name == 'nt': 
            sub_kw_concat['creationflags'] = 0x08004000
            
        res_final = subprocess.run(cmd_concat_final, **sub_kw_concat)
        
        # Hapus berkas temp daftar concat dan video temp
        if os.path.exists(mylist_path):
            try: os.remove(mylist_path)
            except: pass
            
        for temp_v in episode_temp_videos:
            if os.path.exists(temp_v):
                try: os.remove(temp_v)
                except: pass
                
        if res_final.returncode != 0:
            err_msg = ""
            if res_final.returncode in (4294967268, -28):
                err_msg = " (Kemungkinan: Ruang penyimpanan disk penuh atau batas ukuran file FAT32 4GB terlampaui)"
            
            stderr_detail = res_final.stderr.strip() if res_final.stderr else ""
            if stderr_detail:
                last_lines = stderr_detail.splitlines()[-3:]
                stderr_summary = " | Details: " + " / ".join(last_lines)
            else:
                stderr_summary = ""
                
            return False, f"Gagal merakit video concat final (FFmpeg code: {res_final.returncode}){err_msg}{stderr_summary}"
            
        # Simpan subtitle global gabungan (dengan pembantaian OCR spam!)
        if global_subs_list:
            deduplicated_global = merge_duplicate_ocr_subtitles(global_subs_list)
            
            shifted_blocks = []
            for g_idx, sub in enumerate(deduplicated_global, 1):
                new_ts_line = f"{seconds_to_srt_time(sub['start'])} --> {seconds_to_srt_time(sub['end'])}"
                block_str = f"{g_idx}\n{new_ts_line}\n{sub['text']}"
                shifted_blocks.append(block_str)
                
            with open(output_srt_final, 'w', encoding='utf-8') as out_f:
                out_f.write("\n\n".join(shifted_blocks))
                
        return True, "Sukses menggabungkan folder!"
        
    return True, f"Sukses memproses {total_files} berkas."
