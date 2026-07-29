import sys
import os
import json
import subprocess
from vidstamp.core.exporter import get_mkv_chapters, get_ffprobe_path

def main():
    file_path = r"E:\ANIME\[Kusonime] Ragna Crimson 01-12 1080p\[Kusonime] Ragna Crimson 01-12 1080p\[Kusonime] Ragna Crimson - 01.mkv"
    print(f"Memeriksa file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"[-] ERROR: File tidak ditemukan pada jalur tersebut!")
        return
        
    print("[+] File ditemukan! Mengekstrak data bab (chapters) menggunakan ffprobe...")
    
    # Deteksi bab terfilter (OP/ED) via exporter
    detected = get_mkv_chapters(file_path)
    print("\n--> HASIL DETEKSI FILTER OP/ED:")
    print(json.dumps(detected, indent=4))
    
    # Ambil data seluruh bab secara mentah untuk analisis tambahan
    ffprobe_exe = get_ffprobe_path()
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
        
    try:
        res = subprocess.run(cmd, **sub_kw, timeout=10)
        data = json.loads(res.stdout)
        raw_chapters = data.get("chapters", [])
        
        print(f"\n--> DAFTAR SELURUH BAB RAW ({len(raw_chapters)} ditemukan):")
        for idx, rc in enumerate(raw_chapters, 1):
            title = rc.get("tags", {}).get("title", "No Title")
            start = float(rc.get("start_time", 0.0))
            end = float(rc.get("end_time", 0.0))
            
            # Ubah detik ke format waktu menit:detik
            start_min = f"{int(start//60):02d}:{start%60:05.2f}"
            end_min = f"{int(end//60):02d}:{end%60:05.2f}"
            print(f"  [{idx}] \"{title}\": {start_min} --> {end_min} ({start:.2f}s - {end:.2f}s)")
            
    except Exception as e:
        print(f"[-] Gagal membaca data mentah bab: {e}")

if __name__ == "__main__":
    main()
