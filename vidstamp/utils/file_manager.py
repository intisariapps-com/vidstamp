"""
vidstamp/utils/file_manager.py - Helper pengelolaan direktori dan berkas catatan
"""
import os

def ensure_note_folder(video_path):
    """
    Membuat folder penyimpanan khusus catatan di dalam direktori video yang sama,
    menggunakan pola nama "[Judul Video]_Catatan".
    Mengembalikan absolute path folder tersebut.
    """
    dir_name = os.path.dirname(video_path)
    base_name, _ = os.path.splitext(os.path.basename(video_path))
    
    # Penamaan folder khusus
    folder_name = f"{base_name}_Catatan"
    note_dir = os.path.join(dir_name, folder_name)
    
    if not os.path.exists(note_dir):
        os.makedirs(note_dir, exist_ok=True)
        
    return note_dir

def load_skip_config(video_path):
    """
    Membaca konfigurasi skip OP/ED. Mendukung pembacaan dari folder catatan video
    atau template season_skip_template.json di folder induk video.
    """
    import json
    if not video_path:
        return {}
        
    # Coba baca dari folder catatan video spesifik terlebih dahulu
    try:
        note_dir = ensure_note_folder(video_path)
        specific_path = os.path.join(note_dir, "skip_config.json")
        if os.path.exists(specific_path):
            with open(specific_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
        
    # Coba baca dari template season di folder induk video
    try:
        parent_dir = os.path.dirname(video_path)
        template_path = os.path.join(parent_dir, "season_skip_template.json")
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
        
    return {}

def save_skip_config(video_path, config_data, as_template=False):
    """
    Menyimpan konfigurasi skip OP/ED ke skip_config.json spesifik video.
    Jika as_template=True, simpan juga sebagai season_skip_template.json di folder induk video.
    """
    import json
    if not video_path:
        return False
        
    try:
        # Simpan ke folder spesifik video
        note_dir = ensure_note_folder(video_path)
        specific_path = os.path.join(note_dir, "skip_config.json")
        with open(specific_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
            
        # Simpan ke template season jika dicentang
        if as_template:
            parent_dir = os.path.dirname(video_path)
            template_path = os.path.join(parent_dir, "season_skip_template.json")
            with open(template_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Gagal menyimpan konfigurasi skip: {e}")
        return False
