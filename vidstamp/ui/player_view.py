"""
vidstamp/ui/player_view.py - Komponen UI Player Panel Kanan
"""
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
from PIL import Image, ImageTk
import os
import cv2
from vidstamp.config import FONT, COLOR_TS, COLOR_MARK, COLOR_END, COLOR_BG
from vidstamp.utils.time_formatter import format_time, format_remaining
from vidstamp.utils.text_cleaner import get_first_4_words
from vidstamp.utils.file_manager import ensure_note_folder, save_skip_config
from vidstamp.core.subtitle import get_subtitles_in_range

class RightPlayerPanel(tk.Frame):
    def __init__(self, parent, engine, on_toggle_browser_callback, *args, **kwargs):
        super().__init__(parent, bg="#0d0d1a", *args, **kwargs)
        
        self.engine = engine
        self.on_toggle_browser = on_toggle_browser_callback
        
        self._seeking = False
        self.mark_start = None
        self.mark_end = None
        self.scenes = [] # list of tuple (start_sec, end_sec, label_name, subtitle_text)
        self.subtitle_list = [] # List subtitle yang sedang diparse
        
        # State Fullscreen
        self.is_fullscreen = False
        
        # State Skip OP/ED
        self.auto_skip = tk.BooleanVar(value=True)
        self.op_start = None
        self.op_end = None
        self.ed_start = None
        self.ed_end = None
        
        # Overlay Notifikasi Skip
        self.skip_overlay_text = ""
        self.skip_overlay_timer = 0
        
        self._build_ui()
        
    def _build_ui(self):
        # ─ Top Bar Control ─
        self.top_bar = tk.Frame(self, bg="#16213e", pady=3)
        self.top_bar.pack(fill="x")
        
        self.btn_toggle_side = tk.Button(self.top_bar, text="📁 Toggle Browser (Tab)", 
                                         command=self.on_toggle_browser, bg="#1a1a3e",
                                         fg="#7ec8e3", relief="flat", font=("Segoe UI", 8, "bold"),
                                         padx=6, pady=2)
        self.btn_toggle_side.pack(side="left", padx=6)
        
        self.lbl_file = tk.Label(self.top_bar, text="Double-klik video di panel kiri",
                                  bg="#16213e", fg="#a8dadc", font=("Segoe UI", 9))
        self.lbl_file.pack(side="left", padx=10)
        
        # Overlay options
        self.show_ts = tk.BooleanVar(value=True)
        self.show_ms = tk.BooleanVar(value=True)
        
        # Tombol set OP/ED dan Checkbox Auto-Skip
        tk.Checkbutton(self.top_bar, text="ms", variable=self.show_ms,
                        bg="#16213e", fg="#a8dadc", selectcolor="#0f3460",
                        activebackground="#16213e", font=("Segoe UI", 8)).pack(side="right", padx=(2, 6))
        tk.Checkbutton(self.top_bar, text="Timestamp", variable=self.show_ts,
                        bg="#16213e", fg="#a8dadc", selectcolor="#0f3460",
                        activebackground="#16213e", font=("Segoe UI", 8)).pack(side="right", padx=2)
                        
        tk.Frame(self.top_bar, bg="#e94560", width=1, height=18).pack(side="right", padx=8, fill="y")
        
        tk.Checkbutton(self.top_bar, text="Auto-Skip OP/ED", variable=self.auto_skip,
                        bg="#16213e", fg="#ffd700", selectcolor="#0f3460",
                        activebackground="#16213e", font=("Segoe UI", 8, "bold")).pack(side="right", padx=2)
                        
        tk.Button(self.top_bar, text="⚙️ Set Skip OP/ED", command=self.setup_skip_oped_dialog,
                  bg="#e94560", fg="white", relief="flat", font=("Segoe UI", 8, "bold"),
                  padx=6, pady=1).pack(side="right", padx=4)

        # ─ Canvas Video ─
        self.canvas_container = tk.Frame(self, bg="#000000")
        self.canvas_container.pack(fill="both", expand=True, padx=4, pady=4)
        
        self.canvas = tk.Canvas(self.canvas_container, bg="#000000", width=760, height=428,
                                 highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(380, 214, text="<-- Double-klik video dari panel kiri",
                                 fill="#333355", font=("Segoe UI", 13), tags="ph")
        
        # Binding Klik, Double Klik, & Resize Jendela
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Double-Button-1>", self.toggle_fullscreen)
        self.canvas.bind("<Configure>", lambda e: self.render_current_frame())

        # ─ Seek Bar Frame ─
        self.seek_frame = tk.Frame(self, bg="#0d0d1a", pady=2)
        self.seek_frame.pack(fill="x", padx=6)
        
        self.lbl_cur = tk.Label(self.seek_frame, text="00:00:00", bg="#0d0d1a", fg="#e94560",
                                 font=("Consolas", 10, "bold"), width=9)
        self.lbl_cur.pack(side="left", padx=4)
        
        self.seek_var = tk.DoubleVar(value=0)
        self.seek_bar = ttk.Scale(self.seek_frame, from_=0, to=100, variable=self.seek_var,
                                   orient="horizontal", command=self._sk_move)
        self.seek_bar.pack(side="left", fill="x", expand=True, padx=4)
        
        self.seek_bar.bind("<ButtonPress-1>", self._sk_press)
        self.seek_bar.bind("<ButtonRelease-1>", self._sk_release)
        
        self.lbl_tot = tk.Label(self.seek_frame, text="-00:00:00", bg="#0d0d1a", fg="#a8dadc",
                                 font=("Consolas", 10), width=10)
        self.lbl_tot.pack(side="left", padx=4)

        # ─ Control Panel Frame ─
        self.ctrl_panel = tk.Frame(self, bg="#16213e", pady=5)
        self.ctrl_panel.pack(fill="x")
        
        b = dict(bg="#0f3460", fg="white", activebackground="#e94560",
                 font=("Segoe UI", 9, "bold"), relief="flat", padx=7, pady=4)
                 
        tk.Button(self.ctrl_panel, text="-10s", command=lambda: self._delta(-10), **b).pack(side="left", padx=3)
        tk.Button(self.ctrl_panel, text="-1s", command=lambda: self._delta(-1), **b).pack(side="left", padx=2)
        
        self.btn_play = tk.Button(self.ctrl_panel, text="Play", command=self.toggle_play, **b)
        self.btn_play.pack(side="left", padx=3)
        
        tk.Button(self.ctrl_panel, text="+1s", command=lambda: self._delta(1), **b).pack(side="left", padx=2)
        tk.Button(self.ctrl_panel, text="+10s", command=lambda: self._delta(10), **b).pack(side="left", padx=3)

        # Input lompat detik
        tk.Label(self.ctrl_panel, text="Ke detik:", bg="#16213e", fg="#a8dadc",
                 font=("Segoe UI", 8)).pack(side="left", padx=(12, 2))
        
        self.jvar = tk.StringVar()
        je = tk.Entry(self.ctrl_panel, textvariable=self.jvar, width=8, bg="#1a1a3e", fg="white",
                    insertbackground="white", relief="flat", font=("Consolas", 9))
        je.pack(side="left", padx=2)
        je.bind("<Return>", self._jump)
        
        tk.Button(self.ctrl_panel, text="GO", command=self._jump, bg="#e94560", fg="white",
                  relief="flat", font=("Segoe UI", 8, "bold"), padx=5, pady=4).pack(side="left", padx=2)

        # Dropdown Speed
        tk.Label(self.ctrl_panel, text="Speed:", bg="#16213e", fg="#a8dadc",
                 font=("Segoe UI", 8)).pack(side="left", padx=(12, 2))
                 
        self.spvar = tk.StringVar(value="1.0x")
        sp = ttk.Combobox(self.ctrl_panel, textvariable=self.spvar, width=5, state="readonly",
                         values=["0.25x", "0.5x", "0.75x", "1.0x", "1.5x", "2.0x", "3.0x"],
                         font=("Segoe UI", 8))
        sp.pack(side="left", padx=2)
        sp.bind("<<ComboboxSelected>>", self._spchg)

        # Mark buttons
        tk.Frame(self.ctrl_panel, bg="#e94560", width=2, height=26).pack(side="left", padx=10, fill="y")
        
        mk = dict(bg="#1a4a6e", fg="white", activebackground="#e94560",
                font=("Segoe UI", 8, "bold"), relief="flat", padx=6, pady=4)
                
        tk.Button(self.ctrl_panel, text="[M] Start", command=self.mark_start_action, **mk).pack(side="left", padx=2)
        tk.Button(self.ctrl_panel, text="[N] End", command=self.mark_end_action, **mk).pack(side="left", padx=2)
        tk.Button(self.ctrl_panel, text="Simpan", command=self.save_scene_action, bg="#1e5f3a", fg="white",
                  activebackground="#52b788", font=("Segoe UI", 8, "bold"),
                  relief="flat", padx=6, pady=4).pack(side="left", padx=4)

        # Info mark bar
        self.inf_bar = tk.Frame(self, bg="#0d0d1a", pady=1)
        self.inf_bar.pack(fill="x", padx=6)
        
        tk.Label(self.inf_bar, text="Space=Play/Pause | DoubleClick=Fullscreen | Ctrl+T=Record | Ctrl+Space=Batal Rekam | Q=Keluar",
                 bg="#0d0d1a", fg="#333355", font=("Segoe UI", 7)).pack(side="left")
                 
        self.lbl_mk = tk.Label(self.inf_bar, text="", bg="#0d0d1a", fg="#ffd700",
                              font=("Consolas", 8, "bold"))
        self.lbl_mk.pack(side="right", padx=6)

        # Catatan Adegan
        self.sc_label_frame = tk.LabelFrame(self, text=" Adegan Tercatat ", bg="#0d0d1a", fg="#a8dadc",
                           font=("Segoe UI", 8, "bold"), pady=2)
        self.sc_label_frame.pack(fill="x", padx=6, pady=(0, 4))
        
        self.sc_lb = tk.Listbox(self.sc_label_frame, bg="#0b0b18", fg="#e0e0ff", font=("Consolas", 8),
                               height=4, selectbackground="#e94560",
                               activestyle="none", relief="flat", highlightthickness=0)
        self.sc_lb.pack(side="left", fill="x", expand=True)
        self.sc_lb.bind("<Double-Button-1>", self._jump_sc)
        
        scbf = tk.Frame(self.sc_label_frame, bg="#0d0d1a")
        scbf.pack(side="right", padx=4)
        
        for txt, cmd, col in [("Lompat", self._jump_sc, "#0f3460"),
                             ("Hapus", self._del_sc, "#5c1a1a"),
                             ("Export", self._exp_sc, "#1e5f3a")]:
            tk.Button(scbf, text=txt, command=cmd, bg=col, fg="white", relief="flat",
                      font=("Segoe UI", 7), padx=6, pady=2).pack(fill="x", pady=1)

    # ── Playback control wrappers ──
    def toggle_play(self):
        if not self.engine.cap:
            return
        if self.engine.playing:
            self.engine.set_playing(False)
            self.btn_play.config(text="Play")
        else:
            self.engine.set_playing(True)
            self.btn_play.config(text="Pause")

    def _delta(self, ds):
        if not self.engine.cap:
            return
        target = self.engine.cur_idx + int(ds * self.engine.fps)
        self.engine.seek_to(target)
        self.seek_var.set(self.engine.cur_idx)
        cur_sec = self.engine.cur_idx / self.engine.fps
        total_sec = self.engine.total_frames / self.engine.fps
        self.lbl_cur.config(text=format_time(cur_sec))
        self.lbl_tot.config(text=format_remaining(cur_sec, total_sec))
        self.render_current_frame()

    def _sk_press(self, e=None):
        self._seeking = True

    def _sk_release(self, e=None):
        self._seeking = False
        if not self.engine.cap:
            return
        self.engine.seek_to(int(self.seek_var.get()))
        self.render_current_frame()

    def _sk_move(self, v):
        if not self.engine.cap:
            return
        try:
            cur_sec = int(float(v)) / self.engine.fps
            total_sec = self.engine.total_frames / self.engine.fps
            self.lbl_cur.config(text=format_time(cur_sec))
            self.lbl_tot.config(text=format_remaining(cur_sec, total_sec))
        except:
            pass

    def _jump(self, e=None):
        if not self.engine.cap:
            return
        raw = self.jvar.get().strip()
        if not raw:
            return
        try:
            if ":" in raw:
                parts = raw.split(":")
                sec = float(parts[0]) * 60 + float(parts[1])
            else:
                sec = float(raw)
            self.engine.seek_to(int(sec * self.engine.fps))
            self.seek_var.set(self.engine.cur_idx)
            self.render_current_frame()
        except:
            messagebox.showwarning("Format Salah", "Gunakan format: detik (90) atau menit:detik (1:30)")

    def _spchg(self, e=None):
        try:
            val = float(self.spvar.get().replace("x", ""))
            self.engine.set_speed(val)
        except:
            self.engine.set_speed(1.0)

    def _on_canvas_click(self, event):
        self.toggle_play()

    # ── Fullscreen ──
    def toggle_fullscreen(self, event=None):
        root = self.winfo_toplevel()
        self.is_fullscreen = not self.is_fullscreen
        
        if self.is_fullscreen:
            self.top_bar.pack_forget()
            self.seek_frame.pack_forget()
            self.ctrl_panel.pack_forget()
            self.inf_bar.pack_forget()
            self.sc_label_frame.pack_forget()
            root.attributes("-fullscreen", True)
        else:
            root.attributes("-fullscreen", False)
            self.top_bar.pack(fill="x", before=self.canvas_container)
            self.canvas_container.pack(fill="both", expand=True)
            self.seek_frame.pack(fill="x", after=self.canvas_container)
            self.ctrl_panel.pack(fill="x", after=self.seek_frame)
            self.inf_bar.pack(fill="x", after=self.ctrl_panel)
            self.sc_label_frame.pack(fill="x", padx=6, pady=(0, 4), after=self.inf_bar)
            
        self.update_idletasks()
        self.render_current_frame()

    # ── Dialog Konfigurasi Skip OP/ED ──
    def setup_skip_oped_dialog(self):
        if not self.engine.cap:
            return
            
        # Jeda video saat popup dialog muncul
        was_playing = self.engine.playing
        if was_playing:
            self.engine.set_playing(False)
            self.btn_play.config(text="Play")
            
        dialog = tk.Toplevel(self)
        dialog.title("⚙️ Atur Waktu Skip OP/ED")
        dialog.geometry("340x260")
        dialog.configure(bg="#0f0f1e")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        # Buat Frame Form
        f = tk.Frame(dialog, bg="#0f0f1e", padx=15, pady=15)
        f.pack(fill="both", expand=True)
        
        # Grid input
        lbl_style = dict(bg="#0f0f1e", fg="#a8dadc", font=("Segoe UI", 9, "bold"))
        ent_style = dict(bg="#1a1a3e", fg="white", insertbackground="white", relief="flat", font=("Consolas", 10))
        
        # Row 1: Opening Start
        tk.Label(f, text="OP Mulai (detik):", **lbl_style).grid(row=0, column=0, sticky="w", pady=4)
        v_op_start = tk.StringVar(value=str(self.op_start) if self.op_start is not None else "")
        tk.Entry(f, textvariable=v_op_start, width=12, **ent_style).grid(row=0, column=1, pady=4, padx=10)
        
        # Row 2: Opening End
        tk.Label(f, text="OP Selesai (detik):", **lbl_style).grid(row=1, column=0, sticky="w", pady=4)
        v_op_end = tk.StringVar(value=str(self.op_end) if self.op_end is not None else "")
        tk.Entry(f, textvariable=v_op_end, width=12, **ent_style).grid(row=1, column=1, pady=4, padx=10)
        
        # Row 3: Ending Start
        tk.Label(f, text="ED Mulai (detik):", **lbl_style).grid(row=2, column=0, sticky="w", pady=4)
        v_ed_start = tk.StringVar(value=str(self.ed_start) if self.ed_start is not None else "")
        tk.Entry(f, textvariable=v_ed_start, width=12, **ent_style).grid(row=2, column=1, pady=4, padx=10)
        
        # Row 4: Ending End
        tk.Label(f, text="ED Selesai (detik):", **lbl_style).grid(row=3, column=0, sticky="w", pady=4)
        v_ed_end = tk.StringVar(value=str(self.ed_end) if self.ed_end is not None else "")
        tk.Entry(f, textvariable=v_ed_end, width=12, **ent_style).grid(row=3, column=1, pady=4, padx=10)
        
        # Row 5: Save as Template Checkbox
        v_template = tk.BooleanVar(value=True)
        tk.Checkbutton(f, text="Terapkan ke satu folder (template season)", variable=v_template,
                        bg="#0f0f1e", fg="#e94560", selectcolor="#1a1a3e",
                        activebackground="#0f0f1e", font=("Segoe UI", 8, "bold")).grid(row=4, column=0, columnspan=2, pady=10, sticky="w")
                        
        def save():
            try:
                op_s = float(v_op_start.get().strip()) if v_op_start.get().strip() else None
                op_e = float(v_op_end.get().strip()) if v_op_end.get().strip() else None
                ed_s = float(v_ed_start.get().strip()) if v_ed_start.get().strip() else None
                ed_e = float(v_ed_end.get().strip()) if v_ed_end.get().strip() else None
                
                # Validasi logika durasi
                if op_s is not None and op_e is not None and op_e <= op_s:
                    messagebox.showerror("Error", "Waktu OP Selesai harus setelah OP Mulai!"); return
                if ed_s is not None and ed_e is not None and ed_e <= ed_s:
                    messagebox.showerror("Error", "Waktu ED Selesai harus setelah ED Mulai!"); return
                    
                # Simpan ke state
                self.op_start = op_s
                self.op_end = op_e
                self.ed_start = ed_s
                self.ed_end = ed_e
                
                # Simpan ke file JSON
                config = {
                    "op_start": self.op_start,
                    "op_end": self.op_end,
                    "ed_start": self.ed_start,
                    "ed_end": self.ed_end,
                    "auto_skip_enabled": self.auto_skip.get()
                }
                save_skip_config(self.engine.video_path, config, as_template=v_template.get())
                
                self.lbl_mk.config(text="⚙️ Skip OP/ED Disimpan!")
                dialog.destroy()
                
                # Kembalikan video play
                if was_playing:
                    self.engine.set_playing(True)
                    self.btn_play.config(text="Pause")
            except ValueError:
                messagebox.showerror("Error", "Masukkan format angka detik saja (misal: 90 atau 1320.5)!")

        # Row 6: Tombol Aksi
        btn_frame = tk.Frame(f, bg="#0f0f1e")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="Batal", command=dialog.destroy, bg="#333", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=15).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Simpan", command=save, bg="#1e5f3a", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=15).pack(side="left", padx=10)

    # ── Mark & Catatan ──
    def mark_start_action(self):
        if not self.engine.cap:
            return
        self.mark_start = self.engine.cur_idx / self.engine.fps
        self._upmk()

    def mark_end_action(self):
        if not self.engine.cap:
            return
        self.mark_end = self.engine.cur_idx / self.engine.fps
        self._upmk()

    def _upmk(self, current_sec=None):
        s = f"S:{format_time(self.mark_start)}" if self.mark_start is not None else "S:--"
        e = f"E:{format_time(self.mark_end)}"   if self.mark_end   is not None else "E:--"
        if self.mark_start is not None and self.mark_end is None and current_sec is not None:
            diff = current_sec - self.mark_start
            diff_m = int(diff) // 60
            diff_s = int(diff) % 60
            self.lbl_mk.config(text=f"{s}  {e}  ({diff_m:02d}:{diff_s:02d})")
        else:
            self.lbl_mk.config(text=f"{s}  {e}")

    def cancel_recording_action(self):
        """Membatalkan perekaman adegan yang sedang berjalan."""
        if self.mark_start is not None or self.mark_end is not None:
            self.mark_start = None
            self.mark_end = None
            self.lbl_mk.config(text="Perekaman dibatalkan")
            self.render_current_frame()

    def save_scene_action(self):
        if not self.engine.cap:
            return
        if self.mark_start is None or self.mark_end is None:
            messagebox.showwarning("Peringatan", "Tandai Start [M] dan End [N] terlebih dahulu!"); return
        if self.mark_end <= self.mark_start:
            messagebox.showwarning("Peringatan", "End harus setelah Start!"); return
            
        dur = self.mark_end - self.mark_start
        
        video_name = os.path.basename(self.engine.video_path)
        base_title = get_first_4_words(video_name)
        default_name = f"{base_title} Catatan {len(self.scenes) + 1}"
        
        was_playing = self.engine.playing
        if was_playing:
            self.engine.set_playing(False)
            self.btn_play.config(text="Play")
            
        # Dapatkan subtitle pratinjau
        sub_text = ""
        if self.subtitle_list:
            matched_subs = get_subtitles_in_range(self.subtitle_list, self.mark_start, self.mark_end)
            if matched_subs:
                sub_text = "\n".join([f"[{format_time(s['start'])}] {s['text']}" for s in matched_subs])

        # State untuk menangkap data dialog
        dialog_result = {"saved": False, "name": ""}

        # Toplevel Dialog Kustom
        dialog = tk.Toplevel(self)
        dialog.title("💾 Simpan Catatan Adegan")
        dialog.geometry("460x330")
        dialog.configure(bg="#0f0f1e")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Pusatkan dialog relatif terhadap main window
        try:
            parent_x = self.winfo_toplevel().winfo_x()
            parent_y = self.winfo_toplevel().winfo_y()
            parent_w = self.winfo_toplevel().winfo_width()
            parent_h = self.winfo_toplevel().winfo_height()
            dialog_x = parent_x + (parent_w - 460) // 2
            dialog_y = parent_y + (parent_h - 330) // 2
            dialog.geometry(f"460x330+{max(0, dialog_x)}+{max(0, dialog_y)}")
        except:
            pass

        # Frame Kontainer utama
        f = tk.Frame(dialog, bg="#0f0f1e", padx=15, pady=15)
        f.pack(fill="both", expand=True)

        # 1. Info Adegan (Waktu & Durasi)
        info_frame = tk.Frame(f, bg="#16213e", padx=10, pady=8)
        info_frame.pack(fill="x", pady=(0, 10))

        lbl_style = dict(bg="#16213e", fg="#a8dadc", font=("Segoe UI", 9))
        val_style = dict(bg="#16213e", fg="#ffd700", font=("Consolas", 9, "bold"))

        tk.Label(info_frame, text="Mulai:", **lbl_style).grid(row=0, column=0, sticky="w")
        tk.Label(info_frame, text=format_time(self.mark_start), **val_style).grid(row=0, column=1, sticky="w", padx=(5, 15))
        
        tk.Label(info_frame, text="Selesai:", **lbl_style).grid(row=0, column=2, sticky="w")
        tk.Label(info_frame, text=format_time(self.mark_end), **val_style).grid(row=0, column=3, sticky="w", padx=(5, 15))

        tk.Label(info_frame, text="Durasi:", **lbl_style).grid(row=0, column=4, sticky="w")
        tk.Label(info_frame, text=f"{dur:.2f}s", **val_style).grid(row=0, column=5, sticky="w", padx=5)

        # 2. Input Kolom Nama Catatan
        tk.Label(f, text="Nama Catatan Adegan:", bg="#0f0f1e", fg="#ffd700", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))
        
        v_name = tk.StringVar(value=default_name)
        ent = tk.Entry(f, textvariable=v_name, bg="#1a1a3e", fg="white", insertbackground="white",
                       relief="flat", font=("Segoe UI", 10), highlightthickness=1, highlightbackground="#333366",
                       highlightcolor="#e94560")
        ent.pack(fill="x", ipady=4, pady=(0, 10))
        
        # Fokus otomatis & seleksi teks
        ent.focus_set()
        ent.select_range(0, tk.END)

        # 3. Preview Subtitle (Jika ada)
        if sub_text:
            tk.Label(f, text="Preview Subtitle / Transkrip:", bg="#0f0f1e", fg="#a8dadc", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 2))
            preview_box = tk.Text(f, bg="#0d0d1a", fg="#8888aa", font=("Consolas", 8), height=5, relief="flat", wrap="word", highlightthickness=0)
            preview_box.pack(fill="both", expand=True, pady=(0, 15))
            preview_box.insert("1.0", sub_text)
            preview_box.config(state="disabled")
        else:
            tk.Frame(f, bg="#0f0f1e", height=60).pack(fill="x")

        # Fungsi Aksi
        def on_confirm(event=None):
            name_val = v_name.get().strip()
            if not name_val:
                messagebox.showwarning("Peringatan", "Nama catatan tidak boleh kosong!", parent=dialog)
                return
            dialog_result["saved"] = True
            dialog_result["name"] = name_val
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # Binds
        ent.bind("<Return>", on_confirm)

        # 4. Tombol Aksi di bagian bawah
        btn_frame = tk.Frame(f, bg="#0f0f1e")
        btn_frame.pack(fill="x")

        tk.Button(btn_frame, text="Batal", command=on_cancel, bg="#333", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=20, pady=4).pack(side="left")
        tk.Button(btn_frame, text="Simpan Catatan", command=on_confirm, bg="#e94560", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=20, pady=4).pack(side="right")

        # Tunggu dialog ditutup
        self.wait_window(dialog)
        
        if was_playing:
            self.engine.set_playing(True)
            self.btn_play.config(text="Pause")
            
        if not dialog_result["saved"]:
            return
            
        note_name = dialog_result["name"]
        self.scenes.append((self.mark_start, self.mark_end, note_name, sub_text))
        
        disp = f"{note_name}: {format_time(self.mark_start)} -> {format_time(self.mark_end)} ({dur:.2f}s)"
        self.sc_lb.insert("end", disp)
        
        self.mark_start = None
        self.mark_end = None
        self.lbl_mk.config(text=f"Tersimpan: {note_name}")
        self.render_current_frame()
        
        # Simpan database JSON dan ekspor teks otomatis
        from vidstamp.utils.file_manager import save_scenes_data
        save_scenes_data(self.engine.video_path, self.scenes)
        self._auto_export_scenes()

    def _jump_sc(self, event=None):
        s = self.sc_lb.curselection()
        if s and self.engine.cap:
            start_sec = self.scenes[s[0]][0]
            self.engine.seek_to(int(start_sec * self.engine.fps))
            self.seek_var.set(self.engine.cur_idx)
            self.render_current_frame()

    def _del_sc(self):
        s = self.sc_lb.curselection()
        if s:
            self.scenes.pop(s[0])
            self.sc_lb.delete(s[0])
            # Simpan database JSON dan ekspor teks otomatis setelah penghapusan
            from vidstamp.utils.file_manager import save_scenes_data
            save_scenes_data(self.engine.video_path, self.scenes)
            self._auto_export_scenes()

    def _auto_export_scenes(self):
        """Mengekspor daftar adegan secara otomatis ke file teks default di folder catatan."""
        if not self.engine.cap or not self.engine.video_path:
            return
        try:
            from vidstamp.utils.file_manager import ensure_note_folder
            note_dir = ensure_note_folder(self.engine.video_path)
            video_name = os.path.basename(self.engine.video_path)
            video_base, _ = os.path.splitext(video_name)
            default_file = os.path.join(note_dir, f"{video_base}_catatan_adegan.txt")
            
            # Ambil path absolut video dan folder catatan
            abs_video_path = os.path.abspath(self.engine.video_path)
            abs_note_dir = os.path.abspath(note_dir)
            note_folder_name = os.path.basename(abs_note_dir)
            
            with open(default_file, "w", encoding="utf-8") as f:
                f.write("=" * 65 + "\n")
                f.write("                  CATATAN ADEGAN & SUBTITLE\n")
                f.write(f"  Video File Name  : {video_name}\n")
                f.write(f"  Video Abs Path   : {abs_video_path}\n")
                f.write(f"  Note Folder Name : {note_folder_name}\n")
                f.write(f"  Note Folder Path : {abs_note_dir}\n")
                f.write("=" * 65 + "\n\n")
                
                for i, (s, e, label, subs) in enumerate(self.scenes, 1):
                    f.write(f"[{i:02d}] {label}\n")
                    f.write(f"     Mulai  : {format_time(s)} ({s:.3f}s)\n")
                    f.write(f"     Akhir  : {format_time(e)} ({e:.3f}s)\n")
                    f.write(f"     Durasi : {e-s:.3f} detik\n")
                    if subs:
                        f.write(f"     --- Subtitle / Transkrip Adegan ---\n")
                        indented_subs = "\n".join(["       " + line for line in subs.split("\n")])
                        f.write(f"{indented_subs}\n")
                    f.write("\n" + "-" * 40 + "\n\n")
        except Exception as err:
            print(f"Gagal melakukan ekspor otomatis catatan: {err}")

    def load_saved_scenes(self):
        """Memuat database adegan lama dari scenes.json ke GUI."""
        self.scenes = []
        self.sc_lb.delete(0, "end")
        if not self.engine.cap or not self.engine.video_path:
            return
            
        from vidstamp.utils.file_manager import load_scenes_data
        saved = load_scenes_data(self.engine.video_path)
        for item in saved:
            s = item.get("start", 0.0)
            e = item.get("end", 0.0)
            label = item.get("label", "")
            subs = item.get("subtitles", "")
            self.scenes.append((s, e, label, subs))
            
            dur = e - s
            disp = f"{label}: {format_time(s)} -> {format_time(e)} ({dur:.2f}s)"
            self.sc_lb.insert("end", disp)

    def _exp_sc(self):
        if not self.scenes:
            messagebox.showinfo("Info", "Belum ada adegan yang dicatat!")
            return
            
        try:
            note_dir = ensure_note_folder(self.engine.video_path)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membuat folder catatan: {e}")
            return
            
        video_name = os.path.basename(self.engine.video_path)
        video_base, _ = os.path.splitext(video_name)
        
        default_file = os.path.join(note_dir, f"{video_base}_catatan_adegan.txt")
        
        p = filedialog.asksaveasfilename(title="Simpan Catatan ke Berkas Teks",
                                         defaultextension=".txt",
                                         initialfile=os.path.basename(default_file),
                                         initialdir=note_dir,
                                         filetypes=[("Text File", "*.txt")])
        if not p:
            return
            
        try:
            # Ambil path absolut video dan folder catatan
            abs_video_path = os.path.abspath(self.engine.video_path)
            abs_note_dir = os.path.abspath(note_dir)
            note_folder_name = os.path.basename(abs_note_dir)
            
            with open(p, "w", encoding="utf-8") as f:
                f.write("=" * 65 + "\n")
                f.write("                  CATATAN ADEGAN & SUBTITLE (SEO)\n")
                f.write(f"  Video File Name  : {video_name}\n")
                f.write(f"  Video Abs Path   : {abs_video_path}\n")
                f.write(f"  Note Folder Name : {note_folder_name}\n")
                f.write(f"  Note Folder Path : {abs_note_dir}\n")
                f.write("=" * 65 + "\n\n")
                
                for i, (s, e, label, subs) in enumerate(self.scenes, 1):
                    f.write(f"[{i:02d}] {label}\n")
                    f.write(f"     Mulai  : {format_time(s)} ({s:.3f}s)\n")
                    f.write(f"     Akhir  : {format_time(e)} ({e:.3f}s)\n")
                    f.write(f"     Durasi : {e-s:.3f} detik\n")
                    if subs:
                        f.write(f"     --- Subtitle / Transkrip Adegan ---\n")
                        indented_subs = "\n".join(["       " + line for line in subs.split("\n")])
                        f.write(f"{indented_subs}\n")
                    f.write("\n" + "-" * 40 + "\n\n")
                    
            messagebox.showinfo("Sukses", f"Catatan berhasil diexport ke:\n{p}")
        except Exception as err:
            messagebox.showerror("Error", f"Gagal mengekspor file: {err}")

    # ── Rendering Helper ──
    def render_current_frame(self):
        if not self.engine.cap:
            return
        frame = self.engine.read_single_frame(self.engine.cur_idx)
        if frame is not None:
            self.draw_frame(frame)

    def draw_frame(self, frame):
        h, w = frame.shape[:2]
        sec = self.engine.cur_idx / self.engine.fps
        
        # ─ Tampilkan Overlay skip text ─
        if self.skip_overlay_text and self.skip_overlay_timer > 0:
            self.skip_overlay_timer -= 1
            # Cari posisi teks tengah
            (tw, th), _ = cv2.getTextSize(self.skip_overlay_text, FONT, 1.2, 3)
            tx = (w - tw) // 2
            ty = (h + th) // 2
            
            # Teks bayangan hitam
            cv2.putText(frame, self.skip_overlay_text, (tx, ty), FONT, 1.2, COLOR_BG, 7, cv2.LINE_AA)
            # Teks utama oranye menyala
            cv2.putText(frame, self.skip_overlay_text, (tx, ty), FONT, 1.2, (50, 150, 255), 3, cv2.LINE_AA)
        else:
            self.skip_overlay_text = ""
            
        if self.show_ts.get():
            lbl = f"  {format_time(sec, self.show_ms.get())}"
            cv2.putText(frame, lbl, (8, 44), FONT, 1.1, COLOR_BG, 6, cv2.LINE_AA)
            cv2.putText(frame, lbl, (8, 44), FONT, 1.1, COLOR_TS, 2, cv2.LINE_AA)
            
            total_sec = self.engine.total_frames / self.engine.fps
            sl = format_remaining(sec, total_sec)
            (tw, _), _ = cv2.getTextSize(sl, FONT, 1.0, 2)
            cv2.putText(frame, sl, (w - tw - 12, 44), FONT, 1.0, COLOR_BG, 5, cv2.LINE_AA)
            cv2.putText(frame, sl, (w - tw - 12, 44), FONT, 1.0, (255, 220, 80), 2, cv2.LINE_AA)
            
        if self.mark_start is not None:
            t = f"START: {format_time(self.mark_start)}"
            cv2.putText(frame, t, (8, h - 28), FONT, 0.75, COLOR_BG, 4, cv2.LINE_AA)
            cv2.putText(frame, t, (8, h - 28), FONT, 0.75, COLOR_MARK, 2, cv2.LINE_AA)
            
            if self.mark_end is None:
                self._upmk(sec)
                running_sec = sec - self.mark_start
                run_m = int(running_sec) // 60
                run_s = int(running_sec) % 60
                t_rec = f"REC: {run_m:02d}:{run_s:02d}"
                cv2.putText(frame, t_rec, (8, h - 56), FONT, 0.75, COLOR_BG, 4, cv2.LINE_AA)
                cv2.putText(frame, t_rec, (8, h - 56), FONT, 0.75, (0, 0, 255), 2, cv2.LINE_AA)
            
        if self.mark_end is not None:
            t = f"END: {format_time(self.mark_end)}"
            (tw, _), _ = cv2.getTextSize(t, FONT, 0.75, 2)
            cv2.putText(frame, t, (w - tw - 12, h - 28), FONT, 0.75, COLOR_BG, 4, cv2.LINE_AA)
            cv2.putText(frame, t, (w - tw - 12, h - 28), FONT, 0.75, COLOR_END, 2, cv2.LINE_AA)
            
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Ambil dimensi aktual Canvas tanpa memblokir thread via update_idletasks()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        
        # Fallback jika widget belum dirender sepenuhnya (nilai <= 1)
        if cw <= 1 or ch <= 1:
            cw = 760
            ch = 428
            
        sc = min(cw / w, ch / h)
        nw, nh = max(1, int(w * sc)), max(1, int(h * sc))
        
        rgb = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_NEAREST)
        img = ImageTk.PhotoImage(Image.fromarray(rgb))
        
        self.canvas.delete("all")
        self.canvas.create_image(cw // 2, ch // 2, anchor="center", image=img)
        self._img_ref = img
