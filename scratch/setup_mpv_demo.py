import os
import sys
import json
import urllib.request
import subprocess

def run_command(args):
    print(f"Menjalankan: {' '.join(args)}")
    res = subprocess.run(args, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Gagal: {res.stderr}")
        return False
    return True

def main():
    print("============================================================")
    # 1. Kloning Repositori media-kit (Opsi 2)
    print("--> 1. Mengkloning repositori media-kit/media-kit...")
    if not os.path.exists("media-kit"):
        success = run_command(["git", "clone", "https://github.com/media-kit/media-kit.git"])
        if success:
            print("[+] Berhasil mengkloning repositori media-kit!")
    else:
        print("[*] Folder 'media-kit' sudah ada, melewati kloning.")

    print("\n============================================================")
    # 2. Menginstal python-mpv (Opsi 1)
    print("--> 2. Menginstal python-mpv di virtual environment...")
    pip_path = os.path.join(".venv", "Scripts", "pip.exe")
    if not os.path.exists(pip_path):
        print("[-] Virtual environment (.venv) tidak ditemukan! Jalankan di root proyek.")
        return

    success = run_command([pip_path, "install", "python-mpv"])
    if success:
        print("[+] Berhasil menginstal python-mpv!")

    print("\n============================================================")
    # 3. Mengunduh libmpv-2.dll dari zhongfly/mpv-winbuild
    print("--> 3. Mencari rilis terbaru libmpv dari zhongfly/mpv-winbuild...")
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/zhongfly/mpv-winbuild/releases/latest",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        download_url = None
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            # Cari dev build 64-bit non-v3 (agar kompatibel dengan semua CPU)
            if name.startswith("mpv-dev-x86_64-") and not "-v3-" in name and name.endswith(".7z"):
                download_url = asset.get("browser_download_url")
                filename = name
                break
                
        if not download_url:
            print("[-] Gagal menemukan berkas mpv-dev-x86_64 di rilis terbaru.")
            return
            
        print(f"[+] Ditemukan berkas: {filename}")
        print(f"--> Mengunduh dari: {download_url}")
        
        # Download berkas 7z
        urllib.request.urlretrieve(download_url, filename)
        print("[+] Unduhan selesai!")
        
        # Ekstrak berkas libmpv-2.dll saja menggunakan tar bawaan Windows
        print("--> Mengekstrak libmpv-2.dll menggunakan tar...")
        run_command(["tar", "-xf", filename, "libmpv-2.dll"])
        
        # Gandakan berkas menjadi mpv-2.dll dan mpv-1.dll agar kompatibel dengan pemanggil python-mpv
        if os.path.exists("libmpv-2.dll"):
            import shutil
            shutil.copy("libmpv-2.dll", "mpv-2.dll")
            shutil.copy("libmpv-2.dll", "mpv-1.dll")
            print("[+] Pustaka libmpv-2.dll, mpv-2.dll, dan mpv-1.dll siap di root!")
            
            # Hapus berkas zip mentahan
            try: os.remove(filename)
            except: pass
        else:
            print("[-] Gagal mengekstrak libmpv-2.dll dari arsip.")
            
    except Exception as e:
        print(f"[-] Terjadi kesalahan saat mengunduh libmpv: {e}")

    print("\n============================================================")
    # 4. Membuat File Test Player MPV
    print("--> 4. Membuat file demo test_mpv_player.py...")
    test_code = """import tkinter as tk
from tkinter import messagebox
import os
import sys

# Tambahkan root folder ke PATH agar ctypes dapat memuat DLL
os.environ["PATH"] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ.get("PATH", "")

try:
    import mpv
except ImportError:
    print("Pustaka python-mpv belum terinstal!")
    sys.exit(1)

class MpvTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Demo libmpv + Tkinter (Performa MPC-HC)")
        self.root.geometry("800x550")
        self.root.configure(bg="#0d0d1a")
        
        # Header
        hdr = tk.Frame(root, bg="#16213e", pady=8)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🎬 Pengujian Mesin libmpv + Tkinter", bg="#16213e", fg="#a8dadc", 
                 font=("Segoe UI", 11, "bold")).pack()
        
        # Container Video (Frame tempat MPV menggambar videonya)
        self.video_frame = tk.Frame(root, bg="black")
        self.video_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Footer Control
        self.ctrl = tk.Frame(root, bg="#0d0d1a", pady=10)
        self.ctrl.pack(fill="x")
        
        self.btn_play = tk.Button(self.ctrl, text="Play / Pause", command=self.toggle_play,
                                  bg="#0f3460", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10)
        self.btn_play.pack(side="left", padx=15)
        
        tk.Label(self.ctrl, text="Gunakan Drag Seekbar atau tombol arah ← / → untuk tes kecepatan seek!", 
                 bg="#0d0d1a", fg="#666688", font=("Segoe UI", 8)).pack(side="right", padx=15)

        # Inisialisasi MPV Player
        # wmode='direct3d' untuk Windows agar akselerasi hardware berjalan mulus langsung di window handle
        try:
            self.player = mpv.MPV(
                wid=str(self.video_frame.winfo_id()),
                vo="gpu", # Render di GPU
                hwdec="auto", # Akselerasi hardware otomatis
                keep_open="yes",
                ytdl="no"
            )
        except Exception as e:
            messagebox.showerror("Error libmpv", f"Gagal menginisialisasi libmpv! Pastikan dll ada di root.\\nError: {e}")
            self.root.destroy()
            return
            
        # Bind Resize Jendela agar MPV menyesuaikan ukuran frame
        self.video_frame.bind("<Configure>", lambda e: self.player.command("video-aspect-override", "-1"))
        
        # Muat video secara otomatis jika ada argumen
        if len(sys.argv) > 1:
            video_path = sys.argv[1]
            if os.path.exists(video_path):
                self.player.play(video_path)
                
    def toggle_play(self):
        self.player.pause = not self.player.pause

if __name__ == "__main__":
    # Verifikasi keberadaan DLL
    dlls = ["libmpv-2.dll", "mpv-2.dll", "mpv-1.dll"]
    if not any(os.path.exists(d) for d in dlls):
        print("[-] File DLL libmpv tidak ditemukan di root folder. Uji coba dibatalkan.")
        sys.exit(1)
        
    root = tk.Tk()
    app = MpvTestApp(root)
    
    # Tunggu sebentar agar window id valid sebelum mulai memutar
    def start_playback():
        # Cari file mkv di folder saat ini jika ada untuk otomatis dimuat
        import glob
        mkv_files = glob.glob("*.mkv") + glob.glob("*.mp4")
        if mkv_files:
            print(f"[+] Otomatis memuat file: {mkv_files[0]}")
            app.player.play(mkv_files[0])
            
    root.after(100, start_playback)
    root.mainloop()
"""
    with open("test_mpv_player.py", "w", encoding="utf-8") as f:
        f.write(test_code)
    print("[+] Berhasil membuat skrip uji coba 'test_mpv_player.py'!")
    print("\n============================================================")
    print("[+] SETUP SELESAI DENGAN SUKSES!")
    print("--> Jalankan perintah berikut untuk menguji pemutar MPV:")
    print("    .\\.venv\\Scripts\\python.exe test_mpv_player.py")
    print("============================================================")

if __name__ == "__main__":
    main()
