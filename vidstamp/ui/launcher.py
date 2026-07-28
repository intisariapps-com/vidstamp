"""
vidstamp/ui/launcher.py - Jendela Menu Pembuka (Startup Launcher Screen)
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import os

class LauncherWindow(tk.Tk):
    def __init__(self, launch_player_fn, launch_wizard_fn, get_def_dir_fn, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("VidStamp Launcher")
        self.geometry("520x350")
        self.resizable(False, False)
        self.configure(bg="#0d0d1a")
        
        self.launch_player = launch_player_fn
        self.launch_wizard = launch_wizard_fn
        self.get_default_dir = get_def_dir_fn
        
        # Center window di monitor
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.geometry(f"+{int(x)}+{int(y)}")
        
        self._build_ui()

    def _build_ui(self):
        # Header / Title
        header = tk.Frame(self, bg="#16213e", pady=20)
        header.pack(fill="x")
        
        tk.Label(header, text="⚡ WELCOME TO VIDSTAMP ⚡", 
                 bg="#16213e", fg="#a8dadc", font=("Segoe UI", 14, "bold")).pack()
        tk.Label(header, text="Video Timestamp, Skip OP/ED & Batch Merger Manager", 
                 bg="#16213e", fg="#8888aa", font=("Segoe UI", 8, "italic")).pack(pady=(2, 0))

        # Body Frame
        body = tk.Frame(self, bg="#0d0d1a", pady=25)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Silakan pilih mode operasi yang ingin dibuka:", 
                 bg="#0d0d1a", fg="white", font=("Segoe UI", 10)).pack(pady=(0, 15))

        # Button Style Dict
        b_player = dict(bg="#1a1a3e", fg="#7ec8e3", activebackground="#e94560", activeforeground="white",
                        font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8, width=42)
                        
        b_wizard = dict(bg="#1e5f3a", fg="white", activebackground="#2a7f50", activeforeground="white",
                        font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8, width=42)

        # Button 1: Media Player
        tk.Button(body, text="📺 Buka Pemutar Media & Marker (VidStamp)", 
                  command=self._click_player, **b_player).pack(pady=8)

        # Button 2: Batch Merger
        tk.Button(body, text="🎛️ Buka Batch Merger & Skip Config Wizard", 
                  command=self._click_wizard, **b_wizard).pack(pady=8)

        # Bottom Frame (Keluar)
        bottom = tk.Frame(body, bg="#0d0d1a")
        bottom.pack(fill="x", side="bottom", padx=25)
        
        tk.Button(bottom, text="Keluar", command=self.quit, bg="#333", fg="white",
                  relief="flat", font=("Segoe UI", 8, "bold"), padx=12, pady=3).pack(side="left")
                  
        tk.Label(bottom, text="v1.3.0", bg="#0d0d1a", fg="#444466",
                 font=("Segoe UI", 8)).pack(side="right", pady=4)

    def _click_player(self):
        self.destroy()
        # Memicu launch player
        self.launch_player()

    def _click_wizard(self):
        # Minta user memilih folder target pengerjaan merge terlebih dahulu
        init_dir = self.get_default_dir()
        d = filedialog.askdirectory(title="Pilih Folder Video Anime", initialdir=init_dir)
        if d:
            self.destroy()
            self.launch_wizard(d)
        else:
            # Jika user cancel dialog folder picker, launcher tetap terbuka
            pass
