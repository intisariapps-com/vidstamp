"""
vidstamp/core/subtitle.py - Ekstraktor dan parser subtitle MKV
"""
import os
import subprocess
import re

def parse_srt_timestamp(ts_str):
    """Konversi format SRT HH:MM:SS,mmm atau HH:MM:SS.mmm ke detik float"""
    match = re.match(r"(\d+):(\d+):(\d+)[.,](\d+)", ts_str.strip())
    if not match:
        return 0.0
    h, m, s, ms = map(int, match.groups())
    return h * 3600 + m * 60 + s + ms / 1000.0

def parse_srt_file(srt_path):
    """
    Memparsing file SRT ke list of dict format:
    [{'start': float, 'end': float, 'text': str}]
    """
    subtitles = []
    if not os.path.exists(srt_path):
        return subtitles

    try:
        with open(srt_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().replace('\r\n', '\n')
            
        blocks = content.strip().split('\n\n')
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                time_line = ""
                text_start_idx = 2
                
                for idx, line in enumerate(lines):
                    if "-->" in line:
                        time_line = line
                        text_start_idx = idx + 1
                        break
                        
                if not time_line:
                    continue
                    
                times = time_line.split("-->")
                if len(times) == 2:
                    start_sec = parse_srt_timestamp(times[0].strip())
                    end_sec = parse_srt_timestamp(times[1].strip())
                    text = " ".join(lines[text_start_idx:])
                    # Bersihkan tag HTML (seperti <font>) dan tag ASS/SSA (seperti {\an8})
                    text_clean = re.sub(r"<[^>]*>", "", text)
                    text_clean = re.sub(r"\{[^}]*\}", "", text_clean).strip()
                    subtitles.append({
                        'start': start_sec,
                        'end': end_sec,
                        'text': text_clean
                    })
    except Exception as e:
        print(f"Error parsing SRT: {e}")
        
    return subtitles

def extract_mkv_subtitles(video_path, temp_srt_path):
    """
    Mengekstrak trek subtitle internal pertama (0:s:0) dari berkas MKV
    ke berkas SRT temporer menggunakan subprocess FFmpeg.
    """
    if not video_path.lower().endswith('.mkv'):
        return False
        
    if os.path.exists(temp_srt_path):
        try:
            os.remove(temp_srt_path)
        except:
            pass

    from vidstamp.utils.path_helper import get_ffmpeg_path
    ffmpeg_cmd = get_ffmpeg_path()
    cmd = [
        ffmpeg_cmd, '-y',
        '-i', video_path,
        '-map', '0:s:0',
        temp_srt_path
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
        if os.path.exists(temp_srt_path) and os.path.getsize(temp_srt_path) > 0:
            return True
    except Exception as e:
        print(f"FFmpeg subtitle extraction error: {e}")
        
    return False

def extract_audio_from_video(video_path, output_audio_path):
    """
    Mengekstrak audio track dari video (MP4/MKV) ke file audio (MP3/WAV)
    menggunakan subprocess FFmpeg.
    """
    if os.path.exists(output_audio_path):
        try:
            os.remove(output_audio_path)
        except:
            pass

    from vidstamp.utils.path_helper import get_ffmpeg_path
    ffmpeg_cmd = get_ffmpeg_path()
    
    cmd = [
        ffmpeg_cmd, '-y',
        '-i', video_path,
        '-vn',
        '-c:a', 'libmp3lame' if output_audio_path.lower().endswith('.mp3') else 'pcm_s16le',
        '-q:a', '2' if output_audio_path.lower().endswith('.mp3') else '0',
        output_audio_path
    ]
    
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0

    try:
        res = subprocess.run(
            cmd,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180 # 3 menit untuk audio 2 jam
        )
        if os.path.exists(output_audio_path) and os.path.getsize(output_audio_path) > 0:
            return True, "Sukses"
        else:
            return False, f"FFmpeg error: {res.stderr}"
    except Exception as e:
        return False, str(e)

def get_subtitles_in_range(subtitles_list, start_sec, end_sec):
    """
    Mengambil daftar subtitle yang beririsan dengan interval waktu [start_sec, end_sec].
    """
    result = []
    for sub in subtitles_list:
        if not (sub['end'] < start_sec or sub['start'] > end_sec):
            result.append(sub)
    return result

def find_external_subtitle(video_path):
    """
    Mencari apakah ada file subtitle eksternal (.srt) yang cocok dengan nama video
    di direktori yang sama. Mendukung nama yang persis sama atau yang diakhiri _clean.srt / .clean.srt
    """
    if not video_path:
        return None
        
    dir_name = os.path.dirname(video_path)
    base_name, _ = os.path.splitext(os.path.basename(video_path))
    
    # Pola pencarian file subtitle srt eksternal
    candidates = [
        f"{base_name}.srt",
        f"{base_name}_clean.srt",
        f"{base_name}.clean.srt"
    ]
    
    for c in candidates:
        full_path = os.path.join(dir_name, c)
        if os.path.exists(full_path) and os.path.isfile(full_path) and os.path.getsize(full_path) > 0:
            return full_path
            
    return None
