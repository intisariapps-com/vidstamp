"""
vidstamp/ui/extractor_tool.py - Jendela Perkakas Ekstraktor Subtitle & Audio (MP3/SRT)
"""
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import os
import threading
from vidstamp.core.subtitle import extract_mkv_subtitles, extract_audio_from_video

class AudioSubExtractorWizard(tk.Toplevel):
    def __init__(self, parent, initial_dir=None, *args, **kwargs):
        super().__init__(parent, bg="#0d0d1a", *args, **kwargs)
        self.title("Ekstraktor Subtitle & Audio")
        self.geometry("600x420")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        self.parent = parent
        self.initial_dir = initial_dir or os.path.expanduser("~")
        self.processing = False
        
        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.configure("Emerald.Horizontal.TProgressbar", 
                        troughcolor="#0d0d1a", 
                        background="#1e5f3a", 
                        thickness=15)

    def _build_ui(self):
        # 1. Header
        header_frame = tk.Frame(self, bg="#16213e", pady=10)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="⚙️ Ekstraktor Subtitle & Audio", 
                 bg="#16213e", fg="#a8dadc", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15)
        tk.Label(header_frame, text="Ekstrak subtitle internal MKV atau ambil audio video untuk persiapan transkripsi.", 
                 bg="#16213e", fg="#8888aa", font=("Segoe UI", 8)).pack(anchor="w", padx=15)

        # Body container
        body = tk.Frame(self, bg="#0d0d1a", padx=15, pady=15)
        body.pack(fill="both", expand=True)

        # Input Video File
        tk.Label(body, text="Pilih Berkas Video input (MKV / MP4):", bg="#0d0d1a", fg="#a8dadc",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 2))
                 
        in_frame = tk.Frame(body, bg="#0d0d1a")
        in_frame.pack(fill="x", pady=(0, 10))
        
        self.v_input_path = tk.StringVar()
        self.v_input_path.trace_add("write", self._on_input_changed)
        self.ent_input = tk.Entry(in_frame, textvariable=self.v_input_path, bg="#16213e", fg="white",
                                  insertbackground="white", relief="flat", font=("Consolas", 9))
        self.ent_input.pack(side="left", fill="x", expand=True, ipady=3)
        
        tk.Button(in_frame, text="Pilih Berkas", command=self._browse_input, bg="#1a1a3e", fg="#7ec8e3",
                  relief="flat", font=("Segoe UI", 8, "bold"), padx=10).pack(side="left", padx=(5, 0))

        # Mode Ekstraksi (Radiobutton)
        tk.Label(body, text="Pilih Jenis Ekstraksi:", bg="#0d0d1a", fg="#a8dadc",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5, 2))
                 
        self.v_extract_mode = tk.StringVar(value="sub")
        self.v_extract_mode.trace_add("write", self._on_mode_changed)
        
        self.rb_sub = tk.Radiobutton(body, text="Ekstrak Subtitle Internal ke .srt (Hanya berkas MKV)", 
                                     variable=self.v_extract_mode, value="sub",
                                     bg="#0d0d1a", fg="white", selectcolor="#16213e", activebackground="#0d0d1a",
                                     activeforeground="white", font=("Segoe UI", 9))
        self.rb_sub.pack(anchor="w", padx=10, pady=2)
        
        self.rb_audio = tk.Radiobutton(body, text="Ekstrak Audio Track ke .mp3 (Mendukung MKV & MP4)", 
                                       variable=self.v_extract_mode, value="audio",
                                       bg="#0d0d1a", fg="white", selectcolor="#16213e", activebackground="#0d0d1a",
                                       activeforeground="white", font=("Segoe UI", 9))
        self.rb_audio.pack(anchor="w", padx=10, pady=2)

        # Output Target File
        tk.Label(body, text="Pilih Berkas Output hasil:", bg="#0d0d1a", fg="#a8dadc",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(10, 2))
                 
        out_frame = tk.Frame(body, bg="#0d0d1a")
        out_frame.pack(fill="x", pady=(0, 10))
        
        self.v_output_path = tk.StringVar()
        self.ent_output = tk.Entry(out_frame, textvariable=self.v_output_path, bg="#16213e", fg="white",
                                   insertbackground="white", relief="flat", font=("Consolas", 9))
        self.ent_output.pack(side="left", fill="x", expand=True, ipady=3)
        
        tk.Button(out_frame, text="Browse...", command=self._browse_output, bg="#1a1a3e", fg="#7ec8e3",
                  relief="flat", font=("Segoe UI", 8, "bold"), padx=10).pack(side="left", padx=(5, 0))

        # Progress Indicator
        self.lbl_status = tk.Label(body, text="Silakan pilih input berkas video.", bg="#0d0d1a", fg="#8888aa",
                                   font=("Segoe UI", 8))
        self.lbl_status.pack(anchor="w", pady=(5, 2))
        
        self.progress_bar = ttk.Progressbar(body, style="Emerald.Horizontal.TProgressbar", mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=(0, 10))

        # Bottom Actions
        btn_frame = tk.Frame(body, bg="#0d0d1a")
        btn_frame.pack(fill="x", side="bottom")
        
        self.btn_cancel = tk.Button(btn_frame, text="Batal", command=self.destroy, bg="#333", fg="white",
                                    relief="flat", font=("Segoe UI", 9, "bold"), padx=15, pady=4)
        self.btn_cancel.pack(side="left")
        
        self.btn_start = tk.Button(btn_frame, text="Mulai Ekstraksi", command=self._start_extraction, bg="#1e5f3a", fg="white",
                                   relief="flat", font=("Segoe UI", 9, "bold"), padx=18, pady=4)
        self.btn_start.pack(side="right")

    def _browse_input(self):
        fn = filedialog.askopenfilename(title="Pilih Berkas Video", 
                                        initialdir=self.initial_dir,
                                        filetypes=[("Video (MKV/MP4)", "*.mkv *.mp4"), ("Semua Berkas", "*.*")])
        if fn:
            self.v_input_path.set(fn)

    def _browse_output(self):
        mode = self.v_extract_mode.get()
        if mode == "sub":
            types = [("Subtitle SRT", "*.srt")]
        else:
            types = [("Audio MP3", "*.mp3")]
            
        fn = filedialog.asksaveasfilename(title="Simpan File Hasil", 
                                          initialdir=os.path.dirname(self.v_input_path.get()) or self.initial_dir,
                                          initialfile=os.path.basename(self.v_output_path.get()),
                                          filetypes=types)
        if fn:
            self.v_output_path.set(fn)

    def _on_input_changed(self, *args):
        in_path = self.v_input_path.get()
        if not in_path or not os.path.exists(in_path):
            return
            
        base, ext = os.path.splitext(in_path)
        mode = self.v_extract_mode.get()
        
        # Atur disable/enable mode radio berdasarkan ekstensi file
        if ext.lower() == ".mp4":
            self.rb_sub.config(state="disabled")
            self.v_extract_mode.set("audio")
            self.v_output_path.set(base + ".mp3")
        else:
            self.rb_sub.config(state="normal")
            if mode == "sub":
                self.v_output_path.set(base + ".srt")
            else:
                self.v_output_path.set(base + ".mp3")
                
        self.lbl_status.config(text="Siap untuk diekstrak.")

    def _on_mode_changed(self, *args):
        in_path = self.v_input_path.get()
        if not in_path:
            return
        base, _ = os.path.splitext(in_path)
        mode = self.v_extract_mode.get()
        if mode == "sub":
            self.v_output_path.set(base + ".srt")
        else:
            self.v_output_path.set(base + ".mp3")

    def _start_extraction(self):
        if self.processing:
            return
            
        in_path = self.v_input_path.get()
        out_path = self.v_output_path.get()
        mode = self.v_extract_mode.get()
        
        if not in_path or not os.path.exists(in_path):
            messagebox.showerror("Error", "Berkas video input tidak valid!")
            return
        if not out_path:
            messagebox.showerror("Error", "Tentukan lokasi berkas output!")
            return
            
        self.processing = True
        self.btn_start.config(state="disabled")
        self.btn_cancel.config(state="disabled")
        self.progress_bar.start(10)
        self.lbl_status.config(text="Sedang mengekstrak berkas via FFmpeg... Mohon tunggu.")
        
        def run_thread():
            try:
                if mode == "sub":
                    success = extract_mkv_subtitles(in_path, out_path)
                    msg = "Sukses mengekstrak subtitle internal!" if success else "Gagal mengekstrak subtitle. Pastikan video MKV memiliki trek teks."
                else:
                    success, err_msg = extract_audio_from_video(in_path, out_path)
                    msg = "Sukses mengekstrak audio track!" if success else f"Gagal mengekstrak audio:\n{err_msg}"
                
                self.after(0, lambda: self._extraction_complete(success, msg))
            except Exception as e:
                self.after(0, lambda: self._extraction_complete(False, f"Terjadi kesalahan internal:\n{e}"))
                
        threading.Thread(target=run_thread, daemon=True).start()

    def _extraction_complete(self, success, message):
        self.processing = False
        self.progress_bar.stop()
        self.btn_start.config(state="normal")
        self.btn_cancel.config(state="normal")
        self.lbl_status.config(text="Proses selesai.")
        
        if success:
            messagebox.showinfo("Sukses", message)
            self.destroy()
        else:
            messagebox.showerror("Gagal", message)
