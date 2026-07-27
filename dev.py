"""
dev.py - Development launcher with Auto-Reload (Hot Reload) for VidStamp
Memantau perubahan file .py di dalam folder 'vidstamp/' dan me-restart aplikasi secara otomatis.
"""
import os
import sys
import time
import subprocess

def get_py_files_mtime(watch_dir):
    """Mendapatkan kamus path berkas dan waktu modifikasi terakhir."""
    mtimes = {}
    for root, _, files in os.walk(watch_dir):
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                try:
                    mtimes[full_path] = os.path.getmtime(full_path)
                except OSError:
                    pass
    return mtimes

def main():
    # Direktori target pengawasan
    watch_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vidstamp')
    print(f"[*] Memulai launcher auto-reload. Mengawasi: {watch_dir}")
    print("[*] Jalankan pengeditan pada file Python Anda untuk memicu restart otomatis.")
    
    current_state = get_py_files_mtime(watch_dir)
    process = None
    
    # Perintah eksekusi aplikasi
    cmd = [sys.executable, '-m', 'vidstamp']
    
    try:
        # Jalankan instance pertama
        process = subprocess.Popen(cmd)
        
        while True:
            time.sleep(0.8) # Cek setiap 800 milidetik
            
            # Cek perubahan berkas
            new_state = get_py_files_mtime(watch_dir)
            changed = False
            
            # 1. Periksa berkas baru / modifikasi
            for path, mtime in new_state.items():
                if path not in current_state or current_state[path] < mtime:
                    changed = True
                    break
                    
            # 2. Periksa berkas dihapus
            if not changed:
                for path in current_state:
                    if path not in new_state:
                        changed = True
                        break
            
            # Jika terdeteksi perubahan
            if changed:
                print("\n[+] Perubahan berkas terdeteksi! Memulai ulang aplikasi...")
                current_state = new_state
                
                # Matikan proses lama jika masih aktif
                if process and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        process.kill()
                
                # Mulai instance baru
                process = subprocess.Popen(cmd)
            
            # Jika proses mati (misalnya ditutup user), biarkan watcher tetap hidup.
            # Jadi ketika user mengedit file lagi, aplikasi akan terbuka kembali secara otomatis.
            
    except KeyboardInterrupt:
        print("\n[*] Menghentikan watcher...")
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1.0)
            except:
                process.kill()
        sys.exit(0)

if __name__ == '__main__':
    main()
