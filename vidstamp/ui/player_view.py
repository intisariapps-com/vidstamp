"""
vidstamp/ui/player_view.py - Komponen UI Player Panel Kanan
"""
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
from PIL import Image, ImageTk
import os
import cv2
import customtkinter as ctk
from vidstamp.config import FONT, COLOR_TS, COLOR_MARK, COLOR_END, COLOR_BG
from vidstamp.utils.time_formatter import format_time, format_remaining
from vidstamp.utils.text_cleaner import get_first_4_words
from vidstamp.utils.file_manager import ensure_note_folder, save_skip_config
from vidstamp.core.subtitle import get_subtitles_in_range

class RightPlayerPanel(ctk.CTkFrame):
    def __init__(self, parent, engine, on_toggle_browser_callback, on_settings_save_callback=None, *args, **kwargs):
        super().__init__(parent, fg_color="#0d0d1a", corner_radius=0, *args, **kwargs)
        
        self.engine = engine
        self.on_toggle_browser = on_toggle_browser_callback
        self.on_settings_save = on_settings_save_callback
        
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
        from vidstamp.utils.file_manager import load_global_config
        cfg_data = load_global_config()

        # Gunakan CTkTabview untuk transisi tab yang sangat premium
        self.tabview = ctk.CTkTabview(self, fg_color="#0d0d1a", segmented_button_selected_color="#e94560",
                                      segmented_button_selected_hover_color="#ff6b8b",
                                      segmented_button_unselected_color="#16213e",
                                      segmented_button_unselected_hover_color="#1a1a3e")
        self.tabview.pack(fill="both", expand=True)
        
        self.tab_player = self.tabview.add("  🎥 Pemutar Video  ")
        self.tab_settings = self.tabview.add("  ⚙️ Pengaturan  ")
        
        # Simpan reference notebook/tabview untuk kemudahan toggle fullscreen
        self.notebook = self.tabview
        
        # Overlay options (dimuat dari config global)
        self.show_ts = tk.BooleanVar(value=cfg_data.get("show_ts", True))
        self.show_ms = tk.BooleanVar(value=cfg_data.get("show_ms", True))

        # --- TAB PEMUTAR VIDEO ---
        self._build_player_tab_ui()
        
        # --- TAB PENGATURAN ---
        self._build_settings_tab_ui()

    def _build_player_tab_ui(self):
        # ─ Top Bar Control ─
        self.top_bar = ctk.CTkFrame(self.tab_player, fg_color="#16213e", corner_radius=0, height=32)
        self.top_bar.pack(fill="x", pady=(0, 2))
        
        self.btn_toggle_side = ctk.CTkButton(self.top_bar, text="📁 Toggle Browser", 
                                             command=self.on_toggle_browser, fg_color="#1a1a3e",
                                             hover_color="#2b2b63", text_color="#7ec8e3",
                                             width=110, height=24, corner_radius=6,
                                             font=("Segoe UI", 9, "bold"))
        self.btn_toggle_side.pack(side="left", padx=8, pady=4)
        
        self.lbl_file = ctk.CTkLabel(self.top_bar, text="Double-klik video di panel kiri",
                                     text_color="#a8dadc", font=("Segoe UI", 10))
        self.lbl_file.pack(side="left", padx=10, pady=4)
        
        # Tombol set OP/ED dan Checkbox Auto-Skip
        self.chk_auto_skip = ctk.CTkCheckBox(self.top_bar, text="Auto-Skip OP/ED", variable=self.auto_skip,
                                             fg_color="#e94560", hover_color="#ff6b8b",
                                             text_color="#ffd700", font=("Segoe UI", 9, "bold"),
                                             checkbox_width=16, checkbox_height=16)
        self.chk_auto_skip.pack(side="right", padx=10, pady=4)
                        
        self.btn_skip_setup = ctk.CTkButton(self.top_bar, text="⚙️ Set Skip OP/ED", command=self.setup_skip_oped_dialog,
                                            fg_color="#e94560", hover_color="#ff6b8b", text_color="white",
                                            width=100, height=24, corner_radius=6,
                                            font=("Segoe UI", 9, "bold"))
        self.btn_skip_setup.pack(side="right", padx=4, pady=4)

        # ─ Canvas Video ─
        self.canvas_container = ctk.CTkFrame(self.tab_player, fg_color="#000000", corner_radius=0)
        self.canvas_container.pack(fill="both", expand=True, padx=4, pady=2)
        
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
        self.seek_bar = ctk.CTkSlider(self.control_bar_frame, from_=0, to=100, variable=self.seek_var,
                                      command=self._sk_move, height=12, fg_color="#1a1a3e",
                                      progress_color="#e94560", button_color="#e94560",
                                      button_hover_color="#ff6b8b")
        self.seek_bar.pack(fill="x", padx=4, pady=(2, 4))
        
        # Gunakan binding untuk mendeteksi penekanan manual
        self.seek_bar.bind("<ButtonPress-1>", self._sk_press)
        self.seek_bar.bind("<ButtonRelease-1>", self._sk_release)
        
        self.lbl_tot = tk.Label(self.seek_frame, text="-00:00:00", bg="#0d0d1a", fg="#a8dadc",
                                 font=("Consolas", 10), width=10)
        self.lbl_tot.pack(side="left", padx=4)

        # Baris tombol & info terpadu (horizontal)
        ctrl_buttons_row = ctk.CTkFrame(self.control_bar_frame, fg_color="transparent")
        ctrl_buttons_row.pack(fill="x", pady=2)

        # Durasi Waktu Berjalan
        self.lbl_time = ctk.CTkLabel(ctrl_buttons_row, text="00:00.000 / 00:00.000",
                                     text_color="#e0e0ff", font=("Consolas", 11, "bold"))
        self.lbl_time.pack(side="left", padx=6)
        
        # Separator vertikal
        ctk.CTkFrame(ctrl_buttons_row, fg_color="#e94560", width=2, height=18).pack(side="left", padx=8, fill="y")

        # Tombol Navigasi (Unicode minimalis)
        btn_style = dict(fg_color="#0f3460", hover_color="#e94560", text_color="white",
                         font=("Segoe UI", 10, "bold"), width=32, height=24, corner_radius=4)
        
        ctk.CTkButton(ctrl_buttons_row, text="⏪", command=lambda: self._delta(-10), **btn_style).pack(side="left", padx=2)
        ctk.CTkButton(ctrl_buttons_row, text="◀", command=lambda: self._delta(-1), **btn_style).pack(side="left", padx=2)
        
        self.btn_play = ctk.CTkButton(ctrl_buttons_row, text="▶", command=self.toggle_play, **btn_style)
        self.btn_play.pack(side="left", padx=2)
        
        ctk.CTkButton(ctrl_buttons_row, text="▶", command=lambda: self._delta(1), **btn_style).pack(side="left", padx=2)
        ctk.CTkButton(ctrl_buttons_row, text="⏩", command=lambda: self._delta(10), **btn_style).pack(side="left", padx=2)

        # Separator vertikal
        ctk.CTkFrame(ctrl_buttons_row, fg_color="#e94560", width=2, height=18).pack(side="left", padx=8, fill="y")

        # Tombol Penanda Marker
        m_style = dict(fg_color="#1a4a6e", hover_color="#e94560", text_color="white",
                       font=("Segoe UI", 9, "bold"), height=24, corner_radius=4)
                       
        ctk.CTkButton(ctrl_buttons_row, text="[M] Start", command=self.mark_start_action, width=65, **m_style).pack(side="left", padx=2)
        ctk.CTkButton(ctrl_buttons_row, text="[N] End", command=self.mark_end_action, width=60, **m_style).pack(side="left", padx=2)
        ctk.CTkButton(ctrl_buttons_row, text="Simpan", command=self.save_scene_action, fg_color="#1e5f3a",
                      hover_color="#52b788", text_color="white", font=("Segoe UI", 9, "bold"),
                      width=60, height=24, corner_radius=4).pack(side="left", padx=4)

        # Separator vertikal
        ctk.CTkFrame(ctrl_buttons_row, fg_color="#e94560", width=2, height=18).pack(side="left", padx=8, fill="y")

        # Entry Lompat Detik
        ctk.CTkLabel(ctrl_buttons_row, text="Ke:", text_color="#a0a0c0", font=("Segoe UI", 9)).pack(side="left", padx=2)
        self.jvar = tk.StringVar()
        self.ent_jump = ctk.CTkEntry(ctrl_buttons_row, textvariable=self.jvar, width=55, height=24,
                                     fg_color="#1a1a3e", text_color="white", border_width=0, corner_radius=4,
                                     font=("Consolas", 10))
        self.ent_jump.pack(side="left", padx=2)
        self.ent_jump.bind("<Return>", self._jump)
        
        ctk.CTkButton(ctrl_buttons_row, text="GO", command=self._jump, fg_color="#e94560", hover_color="#ff6b8b",
                      text_color="white", font=("Segoe UI", 9, "bold"), width=32, height=24, corner_radius=4).pack(side="left", padx=2)

        # Dropdown Speed
        self.spvar = tk.StringVar(value="1.0x")
        self.sp_combo = ctk.CTkOptionMenu(ctrl_buttons_row, variable=self.spvar, width=65, height=24,
                                          values=["0.25x", "0.5x", "0.75x", "1.0x", "1.5x", "2.0x", "3.0x"],
                                          command=self._spchg, fg_color="#0f3460", button_color="#0f3460",
                                          button_hover_color="#e94560", font=("Segoe UI", 9))
        self.sp_combo.pack(side="right", padx=6)
        ctk.CTkLabel(ctrl_buttons_row, text="Speed:", text_color="#a0a0c0", font=("Segoe UI", 9)).pack(side="right", padx=4)

        # Info Status Bar tipis di bawah control bar
        self.inf_bar = ctk.CTkFrame(self.tab_player, fg_color="#0d0d1a", corner_radius=0, height=20)
        self.inf_bar.pack(fill="x", padx=6)
        
        ctk.CTkLabel(self.inf_bar, text="Klik Kanan Layar Video untuk Menu Cepat | Q = Keluar",
                     text_color="#444466", font=("Segoe UI", 8)).pack(side="left", padx=2)
                 
        self.lbl_mk = ctk.CTkLabel(self.inf_bar, text="", text_color="#ffd700",
                                   font=("Consolas", 9, "bold"))
        self.lbl_mk.pack(side="right", padx=6)

        # Catatan Adegan
        self.sc_label_frame = ctk.CTkFrame(self.tab_player, fg_color="#0b0b18", border_width=1, border_color="#16213e", corner_radius=6)
        self.sc_label_frame.pack(fill="x", padx=6, pady=(2, 4))
        
        # Label Title Catatan
        ctk.CTkLabel(self.sc_label_frame, text=" Adegan Tercatat ", text_color="#a8dadc",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=2)
        
        self.sc_lb = tk.Listbox(self.sc_label_frame, bg="#0b0b18", fg="#e0e0ff", font=("Consolas", 9),
                                height=4, selectbackground="#e94560",
                                activestyle="none", relief="flat", highlightthickness=0, bd=0)
        self.sc_lb.pack(side="left", fill="x", expand=True, padx=6, pady=(0, 6))
        self.sc_lb.bind("<Double-Button-1>", self._jump_sc)
        self.sc_lb.bind("<<ListboxSelect>>", self._on_sc_select)
        
        scbf = ctk.CTkFrame(self.sc_label_frame, fg_color="transparent")
        scbf.pack(side="right", padx=8, pady=(0, 6))
        
        for txt, cmd, col in [("Lompat", self._jump_sc, "#0f3460"),
                             ("Hapus", self._del_sc, "#5c1a1a"),
                             ("Export", self._exp_sc, "#1e5f3a")]:
            ctk.CTkButton(scbf, text=txt, command=cmd, fg_color=col, hover_color="#ff6b8b",
                          text_color="white", font=("Segoe UI", 8),
                          width=60, height=20, corner_radius=4).pack(fill="x", pady=1)

    def _build_settings_tab_ui(self):
        from vidstamp.utils.file_manager import load_global_config
        cfg_data = load_global_config()

        # Gunakan CTkScrollableFrame yang sangat modern dan clean secara native
        scroll_frame = ctk.CTkScrollableFrame(self.tab_settings, fg_color="#0d0d1a", label_text="")
        scroll_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # ─ 1. Tampilan & Pemutar ─
        lf_view = ctk.CTkFrame(scroll_frame, fg_color="#111124", border_width=1, border_color="#16213e")
        lf_view.pack(fill="x", pady=6, padx=4)
        
        ctk.CTkLabel(lf_view, text=" Tampilan & Pemutar ", text_color="#a8dadc",
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=6)

        ctk.CTkCheckBox(lf_view, text="Tampilkan Timestamp di atas Video", variable=self.show_ts,
                        fg_color="#e94560", hover_color="#ff6b8b",
                        text_color="#e0e0ff", font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=4)
                        
        ctk.CTkCheckBox(lf_view, text="Tampilkan Presisi Milidetik (ms)", variable=self.show_ms,
                        fg_color="#e94560", hover_color="#ff6b8b",
                        text_color="#e0e0ff", font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=4)

        # Default Speed
        fr_speed = ctk.CTkFrame(lf_view, fg_color="transparent")
        fr_speed.pack(fill="x", padx=15, pady=6)
        ctk.CTkLabel(fr_speed, text="Kecepatan Default Pemutar:", text_color="#a0a0c0",
                     font=("Segoe UI", 10)).pack(side="left")
        self.cfg_speed = ctk.CTkComboBox(fr_speed, width=90, height=24, state="readonly",
                                         values=["0.25x", "0.5x", "0.75x", "1.0x", "1.5x", "2.0x", "3.0x"])
        self.cfg_speed.pack(side="left", padx=10)
        self.cfg_speed.set(cfg_data.get("default_speed", "1.0x"))

        # Auto-Save Interval
        fr_save = ctk.CTkFrame(lf_view, fg_color="transparent")
        fr_save.pack(fill="x", padx=15, pady=6)
        ctk.CTkLabel(fr_save, text="Jeda Simpan Otomatis (detik):", text_color="#a0a0c0",
                     font=("Segoe UI", 10)).pack(side="left")
        self.cfg_save_int = tk.StringVar(value=str(cfg_data.get("auto_save_interval", 5)))
        self.ent_save_int = ctk.CTkEntry(fr_save, textvariable=self.cfg_save_int, width=50, height=24,
                                         fg_color="#1a1a3e", text_color="white", border_width=0, corner_radius=4,
                                         font=("Consolas", 10))
        self.ent_save_int.pack(side="left", padx=10)

        # ─ 2. Direktori Pencarian Awal ─
        lf_dirs = ctk.CTkFrame(scroll_frame, fg_color="#111124", border_width=1, border_color="#16213e")
        lf_dirs.pack(fill="x", pady=6, padx=4)
        
        ctk.CTkLabel(lf_dirs, text=" Direktori Awal Pemindaian (Scan Dirs) ", text_color="#a8dadc",
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=6)

        # Listbox direktori
        self.dir_list_frame = ctk.CTkFrame(lf_dirs, fg_color="transparent")
        self.dir_list_frame.pack(fill="x", padx=10, pady=2)
        
        self.dir_lb = tk.Listbox(self.dir_list_frame, bg="#0b0b18", fg="#7ec8e3", font=("Segoe UI", 9),
                                 height=4, selectbackground="#e94560", relief="flat", highlightthickness=0, bd=0)
        self.dir_lb.pack(side="left", fill="x", expand=True)
        
        dir_sb = ctk.CTkScrollbar(self.dir_list_frame, orientation="vertical", command=self.dir_lb.yview, width=10)
        self.dir_lb.config(yscrollcommand=dir_sb.set)
        dir_sb.pack(side="right", fill="y")
        
        for d in cfg_data.get("root_dirs", []):
            self.dir_lb.insert("end", d)

        # Tombol + / - dirs
        fr_dir_btns = ctk.CTkFrame(lf_dirs, fg_color="transparent")
        fr_dir_btns.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkButton(fr_dir_btns, text="➕ Tambah Folder", command=self._add_cfg_dir, fg_color="#1e5f3a",
                      hover_color="#52b788", text_color="white", font=("Segoe UI", 9, "bold"),
                      width=110, height=24, corner_radius=6).pack(side="left", padx=2)
        ctk.CTkButton(fr_dir_btns, text="➖ Hapus Terpilih", command=self._del_cfg_dir, fg_color="#5c1a1a",
                      hover_color="#e94560", text_color="white", font=("Segoe UI", 9, "bold"),
                      width=110, height=24, corner_radius=6).pack(side="left", padx=2)

        # ─ 3. Ekstensi Video ─
        lf_exts = ctk.CTkFrame(scroll_frame, fg_color="#111124", border_width=1, border_color="#16213e")
        lf_exts.pack(fill="x", pady=6, padx=4)
        
        ctk.CTkLabel(lf_exts, text=" Ekstensi Berkas Video ", text_color="#a8dadc",
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=6)
        
        ctk.CTkLabel(lf_exts, text="Daftar Ekstensi (pisahkan dengan koma):", text_color="#a0a0c0",
                     font=("Segoe UI", 9)).pack(anchor="w", padx=15, pady=2)
                 
        exts_str = ", ".join(cfg_data.get("video_exts", []))
        self.cfg_exts = tk.StringVar(value=exts_str)
        self.ent_exts = ctk.CTkEntry(lf_exts, textvariable=self.cfg_exts, fg_color="#1a1a3e",
                                     text_color="white", border_width=0, corner_radius=6,
                                     height=26, font=("Consolas", 10))
        self.ent_exts.pack(fill="x", padx=15, pady=(2, 10))

        # ─ 4. Asosiasi File Default Player (Windows Only) ─
        if os.name == 'nt':
            lf_assoc = ctk.CTkFrame(scroll_frame, fg_color="#111124", border_width=1, border_color="#16213e")
            lf_assoc.pack(fill="x", pady=6, padx=4)
            
            ctk.CTkLabel(lf_assoc, text=" Default Media Player (Windows) ", text_color="#a8dadc",
                         font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=6)
                         
            ctk.CTkLabel(lf_assoc, text="Daftarkan VidStamp agar bisa dipilih sebagai aplikasi\npemutar video default di sistem Windows Anda.",
                         text_color="#a0a0c0", font=("Segoe UI", 9), justify="left").pack(anchor="w", padx=15, pady=2)
                         
            ctk.CTkButton(lf_assoc, text="🔗 Jadikan Default Player", command=self.set_default_player_action,
                          fg_color="#e94560", hover_color="#ff6b8b", text_color="white",
                          font=("Segoe UI", 10, "bold"), height=30, corner_radius=6).pack(fill="x", padx=15, pady=(8, 12))

        # Tombol Simpan Besar di bagian paling bawah
        ctk.CTkButton(scroll_frame, text="💾 Simpan Pengaturan", command=self.save_settings_action, fg_color="#e94560",
                      hover_color="#ff6b8b", text_color="white", font=("Segoe UI", 11, "bold"),
                      height=36, corner_radius=6).pack(fill="x", pady=15, padx=4)

    def set_default_player_action(self):
        from vidstamp.utils.file_manager import register_as_default_player
        success, msg = register_as_default_player()
        if success:
            messagebox.showinfo("Sukses", msg)
        else:
            messagebox.showerror("Error", msg)

    def show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0, bg="#16213e", fg="#e0e0ff",
                       activebackground="#e94560", activeforeground="white", bd=0)
        menu.add_command(label="▶  Play / Pause (Space)", command=self.toggle_play)
        menu.add_separator()
        menu.add_command(label="📍 Tandai Start [M]", command=self.mark_start_action)
        menu.add_command(label="📍 Tandai End [N]", command=self.mark_end_action)
        menu.add_command(label="💾 Simpan Adegan (Ctrl+T)", command=self.save_scene_action)
        menu.add_command(label="❌ Batal Rekam (Ctrl+Space)", command=self._cancel_rec)
        menu.add_separator()
        menu.add_command(label="⚙️ Set Skip OP/ED", command=self.setup_skip_oped_dialog)
        menu.add_command(label="📺 Layar Penuh (Double-Click)", command=self.toggle_fullscreen)
        menu.post(event.x_root, event.y_root)
        
    def _cancel_rec(self):
        self.mark_start = None
        self.mark_end = None
        self.lbl_mk.configure(text="")

    def _add_cfg_dir(self):
        d = filedialog.askdirectory(title="Pilih Folder Video Utama")
        if d:
            existing = self.dir_lb.get(0, "end")
            if d not in existing:
                self.dir_lb.insert("end", d)
                
    def _del_cfg_dir(self):
        sel = self.dir_lb.curselection()
        if sel:
            self.dir_lb.delete(sel[0])

    def save_settings_action(self):
        from vidstamp.utils.file_manager import save_global_config
        
        dirs = list(self.dir_lb.get(0, "end"))
        
        exts_raw = self.cfg_exts.get().split(",")
        exts = []
        for e in exts_raw:
            cleaned = e.strip().lower()
            if cleaned:
                if not cleaned.startswith("."):
                    cleaned = "." + cleaned
                exts.append(cleaned)
                
        try:
            interval = int(self.cfg_save_int.get())
            if interval <= 0:
                interval = 5
        except:
            interval = 5
            
        new_config = {
            "root_dirs": dirs,
            "video_exts": exts,
            "show_ts": self.show_ts.get(),
            "show_ms": self.show_ms.get(),
            "default_speed": self.cfg_speed.get(),
            "auto_save_interval": interval
        }
        
        success = save_global_config(new_config)
        if success:
            messagebox.showinfo("Sukses", "Pengaturan global berhasil disimpan!")
            if self.on_settings_save:
                self.on_settings_save()
        else:
            messagebox.showerror("Error", "Gagal menyimpan berkas konfigurasi.")


        # Detail Preview Adegan Terpilih
        self.detail_frame = tk.LabelFrame(self, text=" Detail Adegan & Subtitel Terpilih ", bg="#0d0d1a", fg="#a8dadc",
                                          font=("Segoe UI", 8, "bold"), pady=2)
        
        self.txt_detail = tk.Text(self.detail_frame, bg="#0b0b18", fg="#8888aa", font=("Consolas", 8),
                                  height=3, relief="flat", wrap="word", highlightthickness=0)
        self.txt_detail.pack(fill="x", padx=5, pady=2)
        self.txt_detail.insert("1.0", "Pilih adegan di atas untuk melihat detail subtitel...")
        self.txt_detail.config(state="disabled")

    # ── Playback control wrappers ──
    def toggle_play(self):
        if not self.engine.cap:
            return
        if self.engine.playing:
            self.engine.set_playing(False)
            self.btn_play.configure(text="▶")
        else:
            self.engine.set_playing(True)
            self.btn_play.configure(text="⏸")

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

    def toggle_fullscreen(self, event=None):
        root = self.winfo_toplevel()
        self.is_fullscreen = not self.is_fullscreen
        
        if self.is_fullscreen:
            self.top_bar.pack_forget()
            self.seek_frame.pack_forget()
            self.ctrl_panel.pack_forget()
            self.inf_bar.pack_forget()
            self.sc_label_frame.pack_forget()
            self.detail_frame.pack_forget() # Sembunyikan detail frame visual!
            root.attributes("-fullscreen", True)
        else:
            # Pindahkan kanvas video kembali ke tab pemutar
            self.canvas_container.pack_forget()
            
            # Susun ulang tata letak pemutar di tab_player secara presisi
            self.top_bar.pack(fill="x", pady=(0, 2))
            self.canvas_container.pack(in_=self.tab_player, fill="both", expand=True, padx=4, pady=2)
            self.control_bar_frame.pack(fill="x", padx=6, pady=2)
            self.inf_bar.pack(fill="x", padx=6)
            self.sc_label_frame.pack(fill="x", padx=6, pady=(2, 4))
            
            # Hancurkan jendela fullscreen
            if hasattr(self, "fs_window") and self.fs_window:
                self.fs_window.destroy()
                self.fs_window = None
                
            root.focus_set()
            
            # Tampilkan kembali detail frame hanya jika ada adegan terpilih
            if self.sc_lb.curselection():
                self.detail_frame.pack(fill="x", padx=6, pady=(0, 4), after=self.sc_label_frame)
            
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
            self.btn_play.configure(text="▶")
            
        dialog = tk.Toplevel(self)
        dialog.title("⚙️ Atur Waktu Skip OP/ED")
        dialog.geometry("420x260")
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
                
                self.lbl_mk.configure(text="⚙️ Skip OP/ED Disimpan!")
                dialog.destroy()
                
                # Kembalikan video play
                if was_playing:
                    self.engine.set_playing(True)
                    self.btn_play.configure(text="⏸")
            except ValueError:
                messagebox.showerror("Error", "Masukkan format angka detik saja (misal: 90 atau 1320.5)!")

        # Row 6: Tombol Aksi
        btn_frame = tk.Frame(f, bg="#0f0f1e")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="Batal", command=dialog.destroy, bg="#333", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=12).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Simpan Settings", command=save, bg="#1e5f3a", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=12).pack(side="left", padx=5)
        tk.Button(btn_frame, text="✂️ Ekspor Video Bersih", command=lambda: self.setup_export_clean_dialog(dialog, v_op_start, v_op_end, v_ed_start, v_ed_end), bg="#e94560", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=10).pack(side="left", padx=5)

    def setup_export_clean_dialog(self, parent_dialog, v_op_start, v_op_end, v_ed_start, v_ed_end):
        if not self.engine.video_path:
            return
            
        # Parse inputs dari parent dialog
        try:
            op_s = float(v_op_start.get().strip()) if v_op_start.get().strip() else None
            op_e = float(v_op_end.get().strip()) if v_op_end.get().strip() else None
            ed_s = float(v_ed_start.get().strip()) if v_ed_start.get().strip() else None
            ed_e = float(v_ed_end.get().strip()) if v_ed_end.get().strip() else None
        except ValueError:
            messagebox.showerror("Error", "Masukkan format angka detik saja di pengaturan skip!")
            return
            
        dialog = tk.Toplevel(self)
        dialog.title("✂️ Konfigurasi Ekspor Bersih")
        dialog.geometry("380x310")
        dialog.configure(bg="#0f0f1e")
        dialog.resizable(False, False)
        dialog.transient(parent_dialog)
        dialog.grab_set()
        
        lbl_style = dict(bg="#0f0f1e", fg="#a8dadc", font=("Segoe UI", 9, "bold"))
        
        # Opsi 1: Mode Subtitel (Hardsub vs Softsub)
        tk.Label(dialog, text="Mode Subtitel:", **lbl_style).pack(anchor="w", padx=20, pady=(12, 3))
        v_sub_mode = tk.StringVar(value="softsub")
        tk.Radiobutton(dialog, text="Softsub (Potong subtitel terpisah .srt)", variable=v_sub_mode, value="softsub",
                       bg="#0f0f1e", fg="white", selectcolor="#1a1a3e", activebackground="#0f0f1e",
                       activeforeground="white", font=("Segoe UI", 9)).pack(anchor="w", padx=35)
        tk.Radiobutton(dialog, text="Hardsub (Tempel teks ke dalam video)", variable=v_sub_mode, value="hardsub",
                       bg="#0f0f1e", fg="white", selectcolor="#1a1a3e", activebackground="#0f0f1e",
                       activeforeground="white", font=("Segoe UI", 9)).pack(anchor="w", padx=35)
                       
        # Opsi 2: Cakupan (Satu file vs Bulk folder)
        tk.Label(dialog, text="Cakupan Ekspor:", **lbl_style).pack(anchor="w", padx=20, pady=(10, 3))
        v_scope = tk.BooleanVar(value=False) # False = Single, True = Bulk
        tk.Radiobutton(dialog, text="Hanya episode aktif saat ini", variable=v_scope, value=False,
                       bg="#0f0f1e", fg="white", selectcolor="#1a1a3e", activebackground="#0f0f1e",
                       activeforeground="white", font=("Segoe UI", 9)).pack(anchor="w", padx=35)
        tk.Radiobutton(dialog, text="Semua video di folder aktif saat ini (Bulk)", variable=v_scope, value=True,
                       bg="#0f0f1e", fg="white", selectcolor="#1a1a3e", activebackground="#0f0f1e",
                       activeforeground="white", font=("Segoe UI", 9)).pack(anchor="w", padx=35)
                       
        v_merge_bulk = tk.BooleanVar(value=True)
        chk_merge = tk.Checkbutton(dialog, text="Gabungkan hasil bulk menjadi 1 file utama (MP4 & SRT)", variable=v_merge_bulk,
                        bg="#0f0f1e", fg="#ffd700", selectcolor="#1a1a3e", activebackground="#0f0f1e",
                        activeforeground="#ffd700", font=("Segoe UI", 8, "bold"))
        chk_merge.pack(anchor="w", padx=35, pady=(5, 0))
                       
        def start_export():
            video_path = self.engine.video_path
            mode = v_sub_mode.get()
            is_bulk = v_scope.get()
            is_merge = v_merge_bulk.get()
            
            # Default output paths
            base_name, ext = os.path.splitext(video_path)
            output_video = f"{base_name}_clean{ext}"
            output_srt = f"{base_name}_clean.srt"
            
            # Tutup dialog opsi dan dialog skip parent
            dialog.destroy()
            parent_dialog.destroy()
            
            # Buka progress window
            self.show_export_progress_window(
                video_path, op_s, op_e, ed_s, ed_e,
                output_video, output_srt, mode, is_bulk, is_merge
            )
            
        # Tombol aksi
        btn_frame_opts = tk.Frame(dialog, bg="#0f0f1e")
        btn_frame_opts.pack(fill="x", pady=12)
        
        tk.Button(btn_frame_opts, text="Batal", command=dialog.destroy, bg="#333", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=15).pack(side="left", padx=25)
        tk.Button(btn_frame_opts, text="Mulai Ekspor", command=start_export, bg="#1e5f3a", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=15).pack(side="right", padx=25)

    def show_export_progress_window(self, video_path, op_start, op_end, ed_start, ed_end, output_video, output_srt, mode, is_bulk, is_merge=False):
        import threading
        
        progress_dialog = tk.Toplevel(self)
        progress_dialog.title("✂️ Memproses Ekspor Video Bersih")
        progress_dialog.geometry("400x190")
        progress_dialog.configure(bg="#0f0f1e")
        progress_dialog.resizable(False, False)
        progress_dialog.transient(self.winfo_toplevel())
        progress_dialog.grab_set()
        
        lbl_status = tk.Label(progress_dialog, text="Menyiapkan ekspor...", bg="#0f0f1e", fg="#a8dadc", font=("Segoe UI", 10, "bold"))
        lbl_status.pack(pady=(20, 5))
        
        lbl_file = tk.Label(progress_dialog, text=os.path.basename(video_path), bg="#0f0f1e", fg="white", font=("Segoe UI", 9))
        lbl_file.pack(pady=5)
        
        progress_var = tk.DoubleVar(value=0)
        progress_bar = ttk.Progressbar(progress_dialog, variable=progress_var, maximum=100, length=320)
        progress_bar.pack(pady=10)
        
        cancel_event = threading.Event()
        
        def cancel_action():
            if messagebox.askyesno("Batal", "Apakah Anda yakin ingin membatalkan proses ekspor?"):
                cancel_event.set()
                progress_dialog.destroy()
                
        btn_cancel = tk.Button(progress_dialog, text="Batal", command=cancel_action, bg="#5c1a1a", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=15)
        btn_cancel.pack(pady=5)
        
        def run_export_thread():
            from vidstamp.core.exporter import export_clean_video_and_srt, export_bulk_and_merge
            
            def progress_callback(pct):
                self.after(0, lambda: progress_var.set(pct))
                self.after(0, lambda: lbl_status.config(text=f"Rendering: {pct:.1f}%"))
                
            if not is_bulk:
                success, msg = export_clean_video_and_srt(
                    video_path, op_start, op_end, ed_start, ed_end,
                    output_video, output_srt, mode=mode,
                    progress_callback=progress_callback, cancel_event=cancel_event
                )
                
                if not cancel_event.is_set():
                    if success:
                        self.after(0, lambda: messagebox.showinfo("Sukses", f"Ekspor berhasil selesai!\nVideo: {os.path.basename(output_video)}\nSubtitel: {os.path.basename(output_srt)}"))
                    else:
                        self.after(0, lambda: messagebox.showerror("Gagal Ekspor", f"Terjadi kesalahan saat mengekspor:\n{msg}"))
                    self.after(0, progress_dialog.destroy)
            else:
                # Pemrosesan Massal (Bulk Folder)
                parent_dir = os.path.dirname(video_path)
                
                def bulk_progress_callback(file_idx, total, pct, status_text):
                    overall_pct = (file_idx / total) * 100 + (pct / total)
                    self.after(0, lambda: progress_var.set(overall_pct))
                    self.after(0, lambda: lbl_status.config(text=f"Eps {file_idx+1}/{total} - {pct:.1f}%"))
                    self.after(0, lambda: lbl_file.config(text=status_text))
                    
                success, msg = export_bulk_and_merge(
                    parent_dir, mode=mode, merge_to_one=is_merge,
                    progress_callback=bulk_progress_callback, cancel_event=cancel_event
                )
                
                if not cancel_event.is_set():
                    if success:
                        self.after(0, lambda: messagebox.showinfo("Sukses", f"Ekspor Massal Selesai!\n{msg}"))
                    else:
                        self.after(0, lambda: messagebox.showerror("Gagal Ekspor Massal", f"Terjadi kesalahan:\n{msg}"))
                    self.after(0, progress_dialog.destroy)
                    
        threading.Thread(target=run_export_thread, daemon=True).start()

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
            self.lbl_mk.configure(text=f"{s}  {e}")


    def cancel_recording_action(self):
        """Membatalkan perekaman adegan yang sedang berjalan."""
        if self.mark_start is not None or self.mark_end is not None:
            self.mark_start = None
            self.mark_end = None
            self.lbl_mk.configure(text="Perekaman dibatalkan")
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
        self.lbl_mk.configure(text=f"Tersimpan: {note_name}")
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
            
            # Reset panel detail setelah hapus
            self.txt_detail.config(state="normal")
            self.txt_detail.delete("1.0", "end")
            self.txt_detail.insert("1.0", "Pilih adegan di atas untuk melihat detail subtitel...")
            self.txt_detail.config(state="disabled")
            self.detail_frame.pack_forget() # Sembunyikan detail frame!
            
            # Simpan database JSON dan ekspor teks otomatis setelah penghapusan
            from vidstamp.utils.file_manager import save_scenes_data
            save_scenes_data(self.engine.video_path, self.scenes)
            self._auto_export_scenes()

    def _on_sc_select(self, event=None):
        selection = self.sc_lb.curselection()
        if not selection:
            self.detail_frame.pack_forget() # Sembunyikan jika deselect
            return
            
        idx = selection[0]
        if idx < len(self.scenes):
            _, _, label, subs = self.scenes[idx]
            self.txt_detail.config(state="normal")
            self.txt_detail.delete("1.0", "end")
            if subs:
                self.txt_detail.insert("1.0", f"Adegan: {label}\n{subs}")
            else:
                self.txt_detail.insert("1.0", f"Adegan: {label}\n(Tidak ada subtitel/dialog terekam)")
            self.txt_detail.config(state="disabled")
            
            # Tampilkan detail frame secara dinamis hanya jika tidak fullscreen
            if not self.is_fullscreen:
                self.detail_frame.pack(fill="x", padx=6, pady=(0, 4), after=self.sc_label_frame)

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
        
        # Reset detail text dan sembunyikan frame detail
        self.txt_detail.config(state="normal")
        self.txt_detail.delete("1.0", "end")
        self.txt_detail.insert("1.0", "Pilih adegan di atas untuk melihat detail subtitel...")
        self.txt_detail.config(state="disabled")
        self.detail_frame.pack_forget()
        
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
    def _wrap_text(self, text, font, font_scale, thickness, max_width):
        """Membungkus kata-kata dalam teks agar total lebar visual piksel tidak melebihi max_width."""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word]) if current_line else word
            (tw, _), _ = cv2.getTextSize(test_line, font, font_scale, thickness)
            
            if tw <= max_width or not current_line:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines

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
            
        # ─ Render Subtitle Live Preview ke Frame ─
        if self.subtitle_list:
            import re
            active_subs = [s for s in self.subtitle_list if s['start'] <= sec < s['end']]
            if active_subs:
                sub_text = active_subs[0]['text']
                sub_text = re.sub(r'<[^>]*>', '', sub_text)
                sub_text = re.sub(r'\{[^}]*\}', '', sub_text).strip()
                
                # Font scale proporsional terhadap tinggi frame (lebar area 1:1 di tengah)
                font_scale = max(0.35, min(0.7, h / 1300.0))
                thickness = max(1, int(2.0 * font_scale))
                shadow_thickness = thickness + 2
                
                # Batas lebar maksimum teks 85% dari lebar efektif area 1:1 di tengah (tinggi h)
                max_text_width = int(h * 0.85)
                
                raw_lines = sub_text.split('\n')
                wrapped_lines = []
                for rl in raw_lines:
                    wrapped_lines.extend(self._wrap_text(rl, FONT, font_scale, thickness, max_text_width))
                
                line_height = int(28 * font_scale)
                base_y = h - 35 - (len(wrapped_lines) - 1) * line_height
                
                for line_idx, line in enumerate(wrapped_lines):
                    (tw, th), _ = cv2.getTextSize(line, FONT, font_scale, thickness)
                    tx = (w - tw) // 2
                    ty = base_y + line_idx * line_height
                    
                    # Shadow hitam outline
                    cv2.putText(frame, line, (tx, ty), FONT, font_scale, COLOR_BG, shadow_thickness, cv2.LINE_AA)
                    # Text utama putih
                    cv2.putText(frame, line, (tx, ty), FONT, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

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
