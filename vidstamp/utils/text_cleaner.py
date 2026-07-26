"""
vidstamp/utils/text_cleaner.py - Helper pembersihan teks dan penamaan catatan
"""
import os
import re

def get_first_4_words(filename):
    """
    Mengambil 4 kata pertama dari judul berkas (tanpa ekstensi).
    Jika judul memiliki kata kurang dari 4, ambil semua kata.
    """
    # Hapus ekstensi
    name, _ = os.path.splitext(filename)
    
    # Ganti pemisah karakter seperti _, ., -, [, ], (, ) menjadi spasi
    name_clean = re.sub(r"[_\.\-\[\]\(\)]", " ", name)
    
    # Split kata dan bersihkan spasi ganda
    words = [w for w in name_clean.split() if w]
    
    if not words:
        return "Adegan"
        
    take = words[:4]
    return " ".join(take)
