"""
vidstamp/ui/browser.py - Komponen UI Browser Panel Kiri
"""
import tkinter as tk
from tkinter import filedialog
import os
import customtkinter as ctk
from vidstamp.config import VIDEO_EXTS

class LeftBrowserPanel(ctk.CTkFrame):
    def __init__(self, parent, on_video_select_callback, def_dir_callback, *args, **kwargs):
        super().__init__(parent, fg_color="#0f0f1e", corner_radius=0, *args, **kwargs)
        
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
        fh = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=0, height=35)
        fh.pack(fill="x")
        
        ctk.CTkLabel(fh, text="Folder Browser", text_color="#a8dadc",
                     font=("Segoe UI", 11, "bold")).pack(side="left", padx=10, pady=5)
                  
        ctk.CTkButton(fh, text="Browse", command=self._browse, fg_color="#e94560",
                      hover_color="#ff6b8b", width=60, height=24, corner_radius=6,
                      font=("Segoe UI", 9, "bold")).pack(side="right", padx=10, pady=5)

        # Breadcrumb / path navigation
        ph = ctk.CTkFrame(self, fg_color="#0b0b18", corner_radius=0, height=28)
        ph.pack(fill="x")
        
        ctk.CTkButton(ph, text="Naik", command=self._up, fg_color="#1a1a3e",
                      hover_color="#2b2b63", text_color="#7ec8e3", width=40, height=20, corner_radius=4,
                      font=("Segoe UI", 8)).pack(side="left", padx=6, pady=4)
                   
        self.lbl_path = ctk.CTkLabel(ph, text="-", text_color="#666688",
                                     font=("Segoe UI", 9), anchor="w", wraplength=140)
        self.lbl_path.pack(side="left", fill="x", expand=True, padx=4)

        # Filter / Search Box
        sf = ctk.CTkFrame(self, fg_color="#0f0f1e", corner_radius=0)
        sf.pack(fill="x", padx=6, pady=4)
        
        ctk.CTkLabel(sf, text="Filter:", text_color="#555577",
                     font=("Segoe UI", 9)).pack(side="left", padx=4)
                 
        self.fvar = tk.StringVar()
        self.fvar.trace_add("write", self._on_filter_change)
        
        self.ent_filter = ctk.CTkEntry(sf, textvariable=self.fvar, fg_color="#1a1a3e",
                                       text_color="#e0e0ff", border_width=0, corner_radius=6,
                                       height=24, font=("Consolas", 10))
        self.ent_filter.pack(side="left", fill="x", expand=True, padx=4)

        # Subfolders List
        ctk.CTkLabel(self, text="Subfolder:", text_color="#555577",
                     font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(6, 0))
                 
        subf = ctk.CTkFrame(self, fg_color="#0f0f1e", corner_radius=0)
        subf.pack(fill="x", padx=6, pady=2)
        
        self.sub_lb = tk.Listbox(subf, bg="#0b0b18", fg="#7ec8e3",
                                  font=("Segoe UI", 9), height=5,
                                  selectbackground="#1a4a6e", activestyle="none",
                                  relief="flat", highlightthickness=0, bd=0)
        ssb = ctk.CTkScrollbar(subf, orientation="vertical", command=self.sub_lb.yview, width=10)
        self.sub_lb.config(yscrollcommand=ssb.set)
        self.sub_lb.pack(side="left", fill="x", expand=True)
        ssb.pack(side="right", fill="y")
        self.sub_lb.bind("<Double-Button-1>", self._sub_dclick)

        # Video Files List
        ctk.CTkLabel(self, text="Video:", text_color="#555577",
                     font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(6, 0))
                 
        vidf = ctk.CTkFrame(self, fg_color="#0f0f1e", corner_radius=0)
        vidf.pack(fill="both", expand=True, padx=6, pady=(2, 4))
        
        self.vid_lb = tk.Listbox(vidf, bg="#0d0d1a", fg="#e0e0ff",
                                  font=("Consolas", 9), selectbackground="#e94560",
                                  activestyle="none", relief="flat", highlightthickness=0, bd=0)
        vsb = ctk.CTkScrollbar(vidf, orientation="vertical", command=self.vid_lb.yview, width=10)
        self.vid_lb.config(yscrollcommand=vsb.set)
        self.vid_lb.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        self.vid_lb.bind("<Double-Button-1>", self._vid_dclick)
        self.vid_lb.bind("<Return>", self._vid_dclick)
        
        self.lbl_vc = ctk.CTkLabel(self, text="", text_color="#555577",
                                   font=("Segoe UI", 9))
        self.lbl_vc.pack(anchor="w", padx=10, pady=2)


    def navigate_to(self, folder):
        """Masuk ke folder baru dan perbarui daftar subfolder & video."""
        if not folder or not os.path.isdir(folder):
            return
        if self.cur_folder and self.cur_folder != folder:
            self.history.append(self.cur_folder)
        self.cur_folder = folder
        self.lbl_path.configure(text=folder)
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
        self.lbl_vc.configure(text=f"{len(self._shown_vids)} video")

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
