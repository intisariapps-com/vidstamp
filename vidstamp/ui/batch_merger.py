"""
vidstamp/ui/batch_merger.py - Jendela Wizard Pemrosesan & Penggabungan Video Massal (Bulk)
"""
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import os
import threading
from vidstamp.config import VIDEO_EXTS
from vidstamp.utils.time_formatter import format_time
from vidstamp.utils.file_manager import load_skip_config
from vidstamp.core.exporter import get_video_duration, get_mkv_chapters, export_bulk_and_merge
from vidstamp.core.subtitle import find_external_subtitle

class BatchMergerWizard(tk.Toplevel):
    def __init__(self, parent, current_dir, *args, **kwargs):
        super().__init__(parent, bg="#0d0d1a", *args, **kwargs)
        self.title("Batch Merger & Skip Config Wizard")
        self.geometry("850x680")
        self.minsize(800, 550)
        
        self.parent_dir = current_dir
        self.cancel_event = threading.Event()
        self.processing = False
        
        self.video_files = []
        self.video_data = {} # path -> {duration, sub_status, op_s, op_e, ed_s, ed_e}
        
        self._setup_styles()
        self._build_ui()
        
        # Mulai load data file di background agar GUI tidak lag saat dibuka
        self.after(100, self._scan_folder_background)

    def _setup_styles(self):
        style = ttk.Style(self)
        
        # Paksa menggunakan tema 'clam' agar properti fieldbackground dihormati di Windows!
        if "clam" in style.theme_names():
            style.theme_use("clam")
            
        style.configure("Dark.Treeview", 
                        background="#0d0d1a", 
                        foreground="#e0e0ff",
                        fieldbackground="#0d0d1a", 
                        rowheight=22,
                        font=("Segoe UI", 9))
        style.configure("Dark.Treeview.Heading", 
                        background="#16213e", 
                        foreground="#a8dadc",
                        font=("Segoe UI", 9, "bold"))
        style.map("Dark.Treeview", 
                  background=[("selected", "#1a4a6e")],
                  foreground=[("selected", "white")])
        
        # Style Progressbar
        style.configure("Emerald.Horizontal.TProgressbar", 
                        troughcolor="#0d0d1a", 
                        background="#1e5f3a", 
                        thickness=15)

    def _build_ui(self):
        # 1. Header & Deskripsi (Terpasang di paling atas)
        header_frame = tk.Frame(self, bg="#16213e", pady=8)
        header_frame.pack(side="top", fill="x")
        
        tk.Label(header_frame, text="🎛️ Batch Merger & Skip Config Wizard", 
                 bg="#16213e", fg="#a8dadc", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15)
        self.lbl_folder = tk.Label(header_frame, text=f"Folder Aktif: {self.parent_dir}", 
                                   bg="#16213e", fg="#8888aa", font=("Segoe UI", 8))
        self.lbl_folder.pack(anchor="w", padx=15, pady=(2, 0))

        # 2. Tombol Pintasan Aksi (Terjangkar di paling bawah)
        btn_frame = tk.Frame(self, bg="#0d0d1a", pady=10)
        btn_frame.pack(side="bottom", fill="x", padx=15)
        
        self.btn_cancel = tk.Button(btn_frame, text="Batal / Keluar", command=self._on_cancel, bg="#333", fg="white",
                                    relief="flat", font=("Segoe UI", 9, "bold"), padx=15, pady=5)
        self.btn_cancel.pack(side="left")
        
        self.btn_start = tk.Button(btn_frame, text="Mulai Proses Massal", command=self._start_processing, bg="#1e5f3a", fg="white",
                                   relief="flat", font=("Segoe UI", 9, "bold"), padx=20, pady=5)
        self.btn_start.pack(side="right")

        # 3. Progres Rendering & Teks Status (Di atas tombol aksi)
        self.progress_frame = tk.Frame(self, bg="#0d0d1a", pady=5)
        self.progress_frame.pack(side="bottom", fill="x", padx=15)
        
        self.lbl_status_text = tk.Label(self.progress_frame, text="Menunggu inisialisasi berkas...", bg="#0d0d1a", fg="#8888aa",
                                        font=("Segoe UI", 9))
        self.lbl_status_text.pack(anchor="w", pady=(0, 2))
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100,
                                            style="Emerald.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x")

        # 4. Panel Opsi & Pengaturan (Di atas progress frame)
        opts_frame = tk.LabelFrame(self, text=" Opsi Pemrosesan Massal ", bg="#0d0d1a", fg="#a8dadc",
                                   font=("Segoe UI", 9, "bold"), padx=15, pady=10, relief="solid", bd=1)
        opts_frame.pack(side="bottom", fill="x", padx=15, pady=(5, 10))
        
        # Subtitle Mode (Softsub vs Hardsub)
        sub_mode_frame = tk.Frame(opts_frame, bg="#0d0d1a")
        sub_mode_frame.pack(fill="x", pady=4)
        tk.Label(sub_mode_frame, text="Mode Subtitle:", bg="#0d0d1a", fg="white", 
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 20))
                 
        self.v_sub_mode = tk.StringVar(value="softsub")
        tk.Radiobutton(sub_mode_frame, text="Softsub (Ekspor subtitel .srt terpisah)", variable=self.v_sub_mode, value="softsub",
                       bg="#0d0d1a", fg="white", selectcolor="#16213e", activebackground="#0d0d1a",
                       activeforeground="white", font=("Segoe UI", 9)).pack(side="left", padx=10)
        tk.Radiobutton(sub_mode_frame, text="Hardsub (Render teks langsung ke video)", variable=self.v_sub_mode, value="hardsub",
                       bg="#0d0d1a", fg="white", selectcolor="#16213e", activebackground="#0d0d1a",
                       activeforeground="white", font=("Segoe UI", 9)).pack(side="left", padx=10)

        # Concat Checkbox
        concat_frame = tk.Frame(opts_frame, bg="#0d0d1a")
        concat_frame.pack(fill="x", pady=4)
        tk.Label(concat_frame, text="Penggabungan:", bg="#0d0d1a", fg="white", 
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 22))
                 
        self.v_merge_video = tk.BooleanVar(value=True)
        tk.Checkbutton(concat_frame, text="Satukan semua hasil bulk menjadi 1 file utama (.mp4 & .srt)", variable=self.v_merge_video,
                       bg="#0d0d1a", fg="#ffd700", selectcolor="#16213e", activebackground="#0d0d1a",
                       activeforeground="#ffd700", font=("Segoe UI", 9, "bold")).pack(side="left", padx=10)

        # Parameter Pintar (OCR & Penamaan Output)
        params_frame = tk.Frame(opts_frame, bg="#0d0d1a")
        params_frame.pack(fill="x", pady=6)
        
        tk.Label(params_frame, text="Toleransi OCR:", bg="#0d0d1a", fg="white", 
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 20))
        
        self.v_ocr_tolerance = tk.DoubleVar(value=2.0)
        ocr_scale = tk.Scale(params_frame, from_=0.5, to=5.0, resolution=0.1, variable=self.v_ocr_tolerance,
                             orient="horizontal", bg="#0d0d1a", fg="white", highlightthickness=0,
                             activebackground="#1e5f3a", font=("Segoe UI", 8), length=150)
        ocr_scale.pack(side="left", padx=5)
        tk.Label(params_frame, text="detik", bg="#0d0d1a", fg="#8888aa", font=("Segoe UI", 8)).pack(side="left", padx=2)
        
        # Penamaan Output File Gabungan
        output_name_frame = tk.Frame(opts_frame, bg="#0d0d1a")
        output_name_frame.pack(fill="x", pady=6)
        
        tk.Label(output_name_frame, text="File Gabungan:", bg="#0d0d1a", fg="white", 
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 20))
                 
        self.v_output_path = tk.StringVar()
        folder_basename = os.path.basename(self.parent_dir.rstrip(r"\/"))
        self.v_output_path.set(os.path.join(self.parent_dir, f"{folder_basename}_clean.mp4"))
        
        ent_out = tk.Entry(output_name_frame, textvariable=self.v_output_path, bg="#16213e", fg="white",
                           insertbackground="white", relief="flat", font=("Consolas", 9))
        ent_out.pack(side="left", fill="x", expand=True, padx=5)
        
        tk.Button(output_name_frame, text="Telusuri...", command=self._browse_output_file, bg="#1a1a3e", fg="#7ec8e3",
                  relief="flat", font=("Segoe UI", 8, "bold"), padx=8).pack(side="left", padx=2)

        # 5. Tabel File Treeview (Menempati sisa ruang di bagian tengah secara elastis)
        table_frame = tk.Frame(self, bg="#0d0d1a", pady=5)
        table_frame.pack(side="top", fill="both", expand=True, padx=15)
        
        tk.Label(table_frame, text="Antrean Episode Video:", bg="#0d0d1a", fg="#a8dadc",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
                 
        columns = ("episode", "duration", "subtitle", "op_skip", "ed_skip")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", 
                                 style="Dark.Treeview", height=6)
        
        self.tree.heading("episode", text="Episode / Nama Berkas")
        self.tree.heading("duration", text="Durasi")
        self.tree.heading("subtitle", text="Subtitel")
        self.tree.heading("op_skip", text="Batas Skip Opening (OP)")
        self.tree.heading("ed_skip", text="Batas Skip Ending (ED)")
        
        self.tree.column("episode", width=250, anchor="w")
        self.tree.column("duration", width=80, anchor="center")
        self.tree.column("subtitle", width=110, anchor="center")
        self.tree.column("op_skip", width=140, anchor="center")
        self.tree.column("ed_skip", width=140, anchor="center")
        
        sb = tk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.config(yscrollcommand=sb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _browse_output_file(self):
        fn = filedialog.asksaveasfilename(title="Simpan File Gabungan", 
                                          initialdir=self.parent_dir,
                                          initialfile=os.path.basename(self.v_output_path.get()),
                                          filetypes=[("Video MP4", "*.mp4")])
        if fn:
            self.v_output_path.set(fn)

    def _scan_folder_background(self):
        self.lbl_status_text.config(text="Memindai daftar video di folder...")
        self.progress_var.set(10)
        self.update()
        
        try:
            self.video_files = sorted([
                os.path.join(self.parent_dir, f) for f in os.listdir(self.parent_dir)
                if os.path.splitext(f)[1].lower() in VIDEO_EXTS and "_clean" not in f.lower()
            ], key=str.lower)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membaca direktori:\n{e}")
            try: self.destroy()
            except tk.TclError: pass
            return
            
        if not self.video_files:
            messagebox.showinfo("Informasi", "Tidak ditemukan berkas video di folder aktif saat ini.")
            try: self.destroy()
            except tk.TclError: pass
            return
            
        def scan_details():
            total = len(self.video_files)
            for idx, file_path in enumerate(self.video_files):
                basename = os.path.basename(file_path)
                self.after(0, lambda name=basename: self.lbl_status_text.config(text=f"Menganalisis [{idx+1}/{total}] {name}..."))
                
                duration = get_video_duration(file_path)
                
                # Cek Subtitle
                sub_status = "Tidak Ada"
                ext_sub = find_external_subtitle(file_path)
                if ext_sub:
                    sub_status = "Eksternal SRT"
                elif file_path.lower().endswith(".mkv"):
                    sub_status = "Internal MKV"
                    
                # Cek Chapters OP/ED
                skip_data = load_skip_config(file_path)
                op_text, ed_text = "-", "-"
                op_start = skip_data.get("op_start")
                op_end = skip_data.get("op_end")
                ed_start = skip_data.get("ed_start")
                ed_end = skip_data.get("ed_end")
                
                if not skip_data and file_path.lower().endswith(".mkv"):
                    detected = get_mkv_chapters(file_path)
                    op_start = detected.get("op_start")
                    op_end = detected.get("op_end")
                    ed_start = detected.get("ed_start")
                    ed_end = detected.get("ed_end")
                
                if op_start is not None and op_end is not None:
                    op_text = f"{format_time(op_start)} - {format_time(op_end)}"
                if ed_start is not None and ed_end is not None:
                    ed_text = f"{format_time(ed_start)} - {format_time(ed_end)}"
                    
                self.video_data[file_path] = {
                    "duration": duration,
                    "subtitle": sub_status,
                    "op_text": op_text,
                    "ed_text": ed_text
                }
                
                # Masukkan ke Treeview di thread utama
                self.after(0, lambda path=file_path: self._insert_to_tree(path))
                
                pct = 10 + (idx + 1) / total * 80
                self.after(0, lambda p=pct: self.progress_var.set(p))
                
            self.after(0, self._scan_complete)

        threading.Thread(target=scan_details, daemon=True).start()

    def _insert_to_tree(self, path):
        data = self.video_data[path]
        filename = os.path.basename(path)
        dur_str = format_time(data["duration"])
        
        self.tree.insert("", "end", values=(
            filename,
            dur_str,
            data["subtitle"],
            data["op_text"],
            data["ed_text"]
        ))

    def _scan_complete(self):
        self.progress_var.set(100)
        self.lbl_status_text.config(text=f"Siap memproses {len(self.video_files)} episode video.")

    def _start_processing(self):
        if self.processing:
            return
            
        self.processing = True
        self.cancel_event.clear()
        self.btn_start.config(state="disabled")
        self.btn_cancel.config(text="Batalkan Proses")
        
        mode = self.v_sub_mode.get()
        merge = self.v_merge_video.get()
        out_path = self.v_output_path.get()
        ocr_tolerance = self.v_ocr_tolerance.get()
        
        # Override sementara file output dan toleransi OCR di core exporter secara lokal
        # Modifikasi global/module-level variables di exporter jika perlu, tapi kita bisa berikan
        # setting ini langsung ke fungsi-fungsi terkait.
        
        def run_merge_thread():
            # Inject parameter OCR tolerance ke dalam exporter module
            import vidstamp.core.exporter as core_exporter
            
            # Buat patch helper sementara untuk merubah gap threshold di merge_duplicate_ocr_subtitles
            original_merge_logic = core_exporter.merge_duplicate_ocr_subtitles
            
            def patched_merge(subs_list):
                if not subs_list:
                    return []
                def normalize_text(t):
                    import re
                    t = t.lower()
                    t = re.sub(r'<[^>]*>', '', t)
                    t = re.sub(r'[\s.,\/#!$%\^&\*;:{}=\-_`~()]+', '', t)
                    return t.strip()
                merged = []
                current = subs_list[0].copy()
                for next_sub in subs_list[1:]:
                    norm_curr = normalize_text(current['text'])
                    norm_next = normalize_text(next_sub['text'])
                    gap = next_sub['start'] - current['end']
                    # Gunakan toleransi OCR yang diset user
                    if norm_curr == norm_next and gap <= ocr_tolerance:
                        current['end'] = max(current['end'], next_sub['end'])
                    else:
                        merged.append(current)
                        current = next_sub.copy()
                merged.append(current)
                return merged
                
            core_exporter.merge_duplicate_ocr_subtitles = patched_merge
            
            # Target output kustom mp4 & srt
            folder_name = os.path.basename(self.parent_dir.rstrip(r"\/"))
            out_mp4_final = out_path
            out_srt_final = os.path.splitext(out_path)[0] + ".srt"
            
            # Kita override path final di exporter dengan path buatan user
            original_output_mp4_final = None
            
            def progress_callback(file_idx, total, pct, status_text):
                overall_pct = (file_idx / total) * 100 + (pct / total)
                self.after(0, lambda: self.progress_var.set(overall_pct))
                self.after(0, lambda: self.lbl_status_text.config(text=f"Eps {file_idx+1}/{total} ({pct:.1f}%) - {status_text}"))
            
            try:
                success, msg = export_bulk_and_merge(
                    self.parent_dir, mode=mode, merge_to_one=merge,
                    progress_callback=progress_callback, cancel_event=self.cancel_event
                )
                
                # Jika user memilih gabungkan, dan output path kustom berbeda dengan default [NamaFolder]_clean.mp4, pindahkan berkas.
                default_mp4 = os.path.join(self.parent_dir, f"{folder_name}_clean.mp4")
                default_srt = os.path.join(self.parent_dir, f"{folder_name}_clean.srt")
                
                if success and merge:
                    if os.path.exists(default_mp4) and os.path.abspath(default_mp4) != os.path.abspath(out_mp4_final):
                        if os.path.exists(out_mp4_final): os.remove(out_mp4_final)
                        os.rename(default_mp4, out_mp4_final)
                    if os.path.exists(default_srt) and os.path.abspath(default_srt) != os.path.abspath(out_srt_final):
                        if os.path.exists(out_srt_final): os.remove(out_srt_final)
                        os.rename(default_srt, out_srt_final)
                
                # Pulihkan fungsi asli
                core_exporter.merge_duplicate_ocr_subtitles = original_merge_logic
                
                if not self.cancel_event.is_set():
                    if success:
                        self.after(0, lambda: messagebox.showinfo("Sukses", f"Proses Batch Selesai!\n{msg}"))
                        self.after(0, self.destroy)
                    else:
                        self.after(0, lambda: messagebox.showerror("Gagal Ekspor Massal", f"Terjadi kesalahan:\n{msg}"))
                        self.after(0, self._reset_ui_state)
            except Exception as ex:
                core_exporter.merge_duplicate_ocr_subtitles = original_merge_logic
                self.after(0, lambda: messagebox.showerror("Error", f"Terjadi kesalahan internal:\n{ex}"))
                self.after(0, self._reset_ui_state)

        threading.Thread(target=run_merge_thread, daemon=True).start()

    def _reset_ui_state(self):
        self.processing = False
        self.btn_start.config(state="normal")
        self.btn_cancel.config(text="Batal / Keluar")
        self.progress_var.set(100)
        self.lbl_status_text.config(text="Proses dibatalkan atau terhenti.")

    def _on_cancel(self):
        if self.processing:
            if messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin membatalkan proses massal yang sedang berjalan?"):
                self.cancel_event.set()
                self._reset_ui_state()
        else:
            self.destroy()
