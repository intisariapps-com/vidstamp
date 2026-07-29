import os
import re
import sys

def srt_time_to_seconds(ts_str):
    ts_str = ts_str.strip().replace(',', '.')
    parts = ts_str.split(':')
    if len(parts) != 3:
        return 0.0
    try:
        h = int(parts[0])
        m = int(parts[1])
        s = float(parts[2])
        return h * 3600 + m * 60 + s
    except:
        return 0.0

def seconds_to_srt_time(secs):
    hours = int(secs // 3600)
    minutes = int((secs % 3600) // 60)
    seconds = int(secs % 60)
    milliseconds = int(round((secs - int(secs)) * 1000))
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

def normalize_text(t):
    t = t.lower()
    t = re.sub(r'<[^>]*>', '', t)
    t = re.sub(r'\{[^}]*\}', '', t)
    t = re.sub(r'[\s.,\/#!$%\^&\*;:{}=\-_`~()\"\'\[\]\\]+', '', t)
    return t.strip()

def merge_duplicate_ocr_subtitles(subs_list):
    if not subs_list:
        return []
    
    merged = []
    
    for sub in subs_list:
        norm_sub = normalize_text(sub['text'])
        
        # Cari ke belakang di merged list (mulai dari yang paling baru)
        found = False
        for m in reversed(merged):
            norm_m = normalize_text(m['text'])
            if norm_m == norm_sub:
                # Cek jarak waktu
                gap = sub['start'] - m['end']
                if gap <= 2.5:
                    m['end'] = max(m['end'], sub['end'])
                    found = True
                break  # Berhenti mencari karena ini adalah kemunculan paling akhir dari teks tersebut
                
        if not found:
            merged.append(sub.copy())
            
    # Urutkan kembali berdasarkan waktu mulai (start time)
    merged.sort(key=lambda x: x['start'])
    return merged

def main():
    input_path = r"E:\ANIME\Solo Leveling S1\Solo Leveling S1.srt"
    output_path = r"E:\ANIME\Solo Leveling S1\Solo Leveling S1_clean.srt"
    
    if not os.path.exists(input_path):
        print(f"[-] File tidak ditemukan: {input_path}")
        return
        
    print(f"--> Membaca file subtitle: {input_path}")
    
    # Coba baca file dengan encoding utf-8, jika gagal gunakan latin1/utf-16
    content = ""
    for enc in ['utf-8-sig', 'utf-16', 'latin1', 'cp1252']:
        try:
            with open(input_path, 'r', encoding=enc) as f:
                content = f.read()
            print(f"[+] Berhasil membaca file dengan encoding: {enc}")
            break
        except Exception:
            continue
            
    if not content:
        print("[-] Gagal membaca file dengan encoding apa pun.")
        return
        
    # Split content by double newline
    blocks = re.split(r'\n\s*\n', content.strip())
    print(f"[*] Jumlah blok subtitle mentah: {len(blocks)}")
    
    subs_list = []
    for b in blocks:
        lines = [l.strip() for l in b.split('\n') if l.strip()]
        if len(lines) >= 3:
            # Cari baris timestamp
            ts_idx = -1
            for idx, line in enumerate(lines):
                if "-->" in line:
                    ts_idx = idx
                    break
            if ts_idx != -1 and len(lines) > ts_idx + 1:
                ts_line = lines[ts_idx]
                text = "\n".join(lines[ts_idx+1:])
                
                parts = ts_line.split("-->")
                if len(parts) == 2:
                    start = srt_time_to_seconds(parts[0])
                    end = srt_time_to_seconds(parts[1])
                    subs_list.append({
                        'start': start,
                        'end': end,
                        'text': text
                    })
                    
    print(f"[*] Berhasil memparsing {len(subs_list)} subtitle.")
    
    # Lakukan deduplikasi
    print("--> Menjalankan proses deduplikasi OCR...")
    cleaned_subs = merge_duplicate_ocr_subtitles(subs_list)
    
    # Tulis hasil bersih ke file SRT baru
    print(f"--> Menulis hasil bersih ke: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        for idx, sub in enumerate(cleaned_subs):
            f.write(f"{idx + 1}\n")
            f.write(f"{seconds_to_srt_time(sub['start'])} --> {seconds_to_srt_time(sub['end'])}\n")
            f.write(f"{sub['text']}\n\n")
            
    print("\n============================================================")
    print("[+] PROSES DEDUPLIKASI SUKSES BESAR!")
    print(f"[*] Jumlah Subtitle Asli    : {len(subs_list)}")
    print(f"[*] Jumlah Subtitle Bersih  : {len(cleaned_subs)}")
    reduction = (1 - (len(cleaned_subs) / len(subs_list))) * 100
    print(f"[+] Rasio Pemadatan Ukuran  : {reduction:.2f}% (Telah dibersihkan)")
    print("============================================================")

if __name__ == "__main__":
    main()
