"""
scratch/test_sao_sub.py - Tes analisis kegagalan pemuatan subtitle berkas SAO Eps 1
"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vidstamp.core.subtitle import extract_mkv_subtitles, parse_srt_file

def test():
    video_path = r"E:\ANIME\Sword Art Online\Sword Art Online S1\[Kusonime] Sword Art Online BD - 02.mkv"
    temp_srt = r"C:\Users\ripal\temp_video_sub.srt"
    
    print(f"Video path exists: {os.path.exists(video_path)}")
    if not os.path.exists(video_path):
        # Fallback jika tidak ada episode 2, coba ke episode 1 di folder atas
        video_path = r"E:\ANIME\Sword Art Online\[Kusonime] Seni Pedan Online S1 BD 720P\[KS] Sword Art Online BD 720P\[Kusonime] Sword Art Online BD - 01.mkv"
        print(f"Fallback to Eps 1 path exists: {os.path.exists(video_path)}")
        if not os.path.exists(video_path):
            return
        
    print("Mengekstrak...")
    extracted = extract_mkv_subtitles(video_path, temp_srt)
    print(f"Extracted: {extracted}")
    
    if extracted:
        print("Memparsing...")
        subtitles = parse_srt_file(temp_srt)
        print(f"Jumlah subtitle termuat: {len(subtitles)}")
        if subtitles:
            print("Contoh 3 subtitle pertama:")
            for i, sub in enumerate(subtitles[:3]):
                print(f"{i+1}. [{sub['start']:.2f}s - {sub['end']:.2f}s] {sub['text']}")

if __name__ == "__main__":
    test()
