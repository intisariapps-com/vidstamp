"""
vidstamp/ui/browser.py - Komponen UI Browser Panel Kiri
"""
import tkinter as tk
from tkinter import filedialog
import os
from vidstamp.config import VIDEO_EXTS

class LeftBrowserPanel(tk.Frame):
    def __init__(self, parent, on_video_select_callback, def_dir_callback, *args, **kwargs):
        super().__init__(parent, bg="#0f0f1e", *args, **kwargs)
        
        self.on_video_select = on_video_select_callback
        self.get_default_dir = def_dir_callback
        self.cur_folder = ""
        self.history = []
        
        self._all_vids = []
        self._shown_vids = []
        self._subfolders = []
        
        self._build_ui()
        
    def _build_ui(self):
        # Header folder
        fh = tk.Frame(self, bg="#16213e", pady=5)
        fh.pack(fill="x")
        
        tk.Label(fh, text="Folder Browser", bg="#16213e", fg="#a8dadc",
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=8)
                 
        tk.Button(fh, text="Browse", command=self._browse, bg="#e94560",
                  fg="white", relief="flat", font=("Segoe UI", 8, "bold"),
                  padx=6, pady=2).pack(side="right", padx=6)

        # Breadcrumb / path navigation
        ph = tk.Frame(self, bg="#0b0b18", pady=2)
        ph.pack(fill="x")
        
        tk.Button(ph, text="Naik", command=self._up, bg="#1a1a3e",
                  fg="#7ec8e3", relief="flat", font=("Segoe UI", 7),
                  padx=6, pady=2).pack(side="left", padx=4)
                  
        self.lbl_path = tk.Label(ph, text="-", bg="#0b0b18", fg="#666688",
                                  font=("Segoe UI", 7), anchor="w", wraplength=190)
        self.lbl_path.pack(side="left", fill="x", expand=True, padx=2)

        # Filter / Search Box
        sf = tk.Frame(self, bg="#0f0f1e", pady=2)
        sf.pack(fill="x", padx=4)
        
        tk.Label(sf, text="Filter:", bg="#0f0f1e", fg="#555577",
                 font=("Segoe UI", 7)).pack(side="left")
                 
        self.fvar = tk.StringVar()
        self.fvar.trace_add("write", self._on_filter_change)
        
        tk.Entry(sf, textvariable=self.fvar, bg="#1a1a3e", fg="#e0e0ff",
                 insertbackground="white", relief="flat",
                 font=("Consolas", 8)).pack(side="left", fill="x", expand=True, padx=4)

        # Subfolders List
        tk.Label(self, text="Subfolder:", bg="#0f0f1e", fg="#555577",
                 font=("Segoe UI", 7)).pack(anchor="w", padx=8, pady=(6, 0))
                 
        subf = tk.Frame(self, bg="#0f0f1e")
        subf.pack(fill="x", padx=4)
        
        self.sub_lb = tk.Listbox(subf, bg="#0b0b18", fg="#7ec8e3",
                                  font=("Segoe UI", 8), height=5,
                                  selectbackground="#1a4a6e", activestyle="none",
                                  relief="flat", highlightthickness=0)
        ssb = tk.Scrollbar(subf, orient="vertical", command=self.sub_lb.yview)
        self.sub_lb.config(yscrollcommand=ssb.set)
        self.sub_lb.pack(side="left", fill="x", expand=True)
        ssb.pack(side="right", fill="y")
        self.sub_lb.bind("<Double-Button-1>", self._sub_dclick)

        # Video Files List
        tk.Label(self, text="Video:", bg="#0f0f1e", fg="#555577",
                 font=("Segoe UI", 7)).pack(anchor="w", padx=8, pady=(6, 0))
                 
        vidf = tk.Frame(self, bg="#0f0f1e")
        vidf.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        
        self.vid_lb = tk.Listbox(vidf, bg="#0d0d1a", fg="#e0e0ff",
                                  font=("Consolas", 7), selectbackground="#e94560",
                                  activestyle="none", relief="flat", highlightthickness=0)
        vsb = tk.Scrollbar(vidf, orient="vertical", command=self.vid_lb.yview)
        self.vid_lb.config(yscrollcommand=vsb.set)
        self.vid_lb.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        self.vid_lb.bind("<Double-Button-1>", self._vid_dclick)
        self.vid_lb.bind("<Return>", self._vid_dclick)
        
        self.lbl_vc = tk.Label(self, text="", bg="#0f0f1e", fg="#555577",
                                font=("Segoe UI", 7))
        self.lbl_vc.pack(anchor="w", padx=8)

    def navigate_to(self, folder):
        """Masuk ke folder baru dan perbarui daftar subfolder & video."""
        if not folder or not os.path.isdir(folder):
            return
        if self.cur_folder and self.cur_folder != folder:
            self.history.append(self.cur_folder)
        self.cur_folder = folder
        self.lbl_path.config(text=folder)
        self.fvar.set("") # reset filter
        self.refresh()

    def _browse(self):
        init = self.cur_folder or self.get_default_dir()
        d = filedialog.askdirectory(title="Pilih Folder Video", initialdir=init)
        if d:
            self.navigate_to(d)

    def _up(self):
        if self.history:
            prev = self.history.pop()
            self.cur_folder = "" # mencegah double push history
            self.navigate_to(prev)
        elif self.cur_folder:
            p = os.path.dirname(self.cur_folder)
            if p != self.cur_folder:
                self.cur_folder = ""
                self.navigate_to(p)

    def refresh(self):
        f = self.cur_folder
        if not f:
            return
            
        # Scan subfolder
        self.sub_lb.delete(0, "end")
        try:
            self._subfolders = sorted([
                os.path.join(f, n) for n in os.listdir(f)
                if os.path.isdir(os.path.join(f, n))
            ], key=str.lower)
        except Exception:
            self._subfolders = []
            
        for s in self._subfolders:
            self.sub_lb.insert("end", "[+] " + os.path.basename(s))

        # Scan video
        try:
            self._all_vids = sorted([
                os.path.join(f, n) for n in os.listdir(f)
                if os.path.isfile(os.path.join(f, n)) and os.path.splitext(n)[1].lower() in VIDEO_EXTS
            ], key=str.lower)
        except Exception:
            self._all_vids = []
            
        self._populate_videos(self._all_vids)

    def _populate_videos(self, vids):
        self.vid_lb.delete(0, "end")
        q = self.fvar.get().lower()
        
        self._shown_vids = [
            v for v in vids 
            if q in os.path.basename(v).lower()
        ] if q else list(vids)
        
        for v in self._shown_vids:
            self.vid_lb.insert("end", os.path.basename(v))
        self.lbl_vc.config(text=f"{len(self._shown_vids)} video")

    def _on_filter_change(self, *args):
        self._populate_videos(self._all_vids)

    def _sub_dclick(self, event=None):
        s = self.sub_lb.curselection()
        if s:
            self.navigate_to(self._subfolders[s[0]])

    def _vid_dclick(self, event=None):
        s = self.vid_lb.curselection()
        if s:
            self.on_video_select(self._shown_vids[s[0]])

    def highlight_video(self, path):
        """Memilih file video di listbox sesuai path"""
        name = os.path.basename(path)
        for i, v in enumerate(self._shown_vids):
            if os.path.basename(v) == name:
                self.vid_lb.selection_clear(0, "end")
                self.vid_lb.selection_set(i)
                self.vid_lb.see(i)
                break
