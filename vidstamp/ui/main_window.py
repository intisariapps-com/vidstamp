"""
vidstamp/ui/main_window.py - Koordinator Window Utama dan Event Loops
"""
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sys
import os
import time

# Impor dari paket vidstamp
from vidstamp.config import ROOT_DIRS
from vidstamp.utils.time_formatter import format_time, format_remaining
from vidstamp.core.subtitle import extract_mkv_subtitles, parse_srt_file, find_external_subtitle
from vidstamp.core.player import VideoPlayerEngine
from vidstamp.ui.browser import LeftBrowserPanel
from vidstamp.ui.player_view import RightPlayerPanel
from vidstamp.utils.file_manager import load_skip_config

class VideoAppController:
    def __init__(self, root, start_path=None):
        self.root = root
        self.root.title("VidStamp v1.3.0 - Video Timestamp & Scene Marker")
        
        self.engine = VideoPlayerEngine()
        self.temp_srt_path = os.path.join(os.path.expanduser("~"), "temp_video_sub.srt")
        
        # State Penanda Skip OP/ED
        self.skipped_op = False
        self.skipped_ed = False
        
        # State Folder & Daftar Video
        self.current_folder = None
        self.video_list = []
        self.video_names = []
        
        # Panel Utama (RightPlayerPanel memenuhi jendela)
        self.right_panel = RightPlayerPanel(
            self.root, self.engine,
            on_open_folder_callback=self.open_folder_action,
            on_open_file_callback=self.open_file_action,
            on_select_video_callback=self.select_video_action,
            on_open_batch_merger_callback=self.open_batch_merger,
            on_open_extractor_callback=self.open_extractor_tool,
            on_open_notes_folder_callback=self.open_notes_folder_action
        )
        self.right_panel.pack(fill="both", expand=True)
        
        # Setup Menu Bar OS Native agar responsif di Windows
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Peralatan", menu=self.tools_menu)
        self.tools_menu.add_command(label="Batch Merger Wizard... (Ctrl+M)", command=self.open_batch_merger)
        self.tools_menu.add_command(label="Ekstraktor Subtitle & Audio...", command=self.open_extractor_tool)
        self.tools_menu.add_command(label="Buka Folder Catatan adegan", command=self.open_notes_folder_action)

        self._bind_global_shortcuts()
        
        init_path = start_path or self.get_default_dir()
        if init_path and os.path.isdir(init_path):
            self.update_video_list_from_folder(init_path)
            if self.video_list:
                self.load_video(self.video_list[0])
        elif init_path and os.path.isfile(init_path):
            self.update_video_list_from_folder(os.path.dirname(init_path))
            self.load_video(init_path)
            
        self.playback_loop()
        self._start_auto_save_loop()

    def get_default_dir(self):
        for d in ROOT_DIRS:
            if os.path.isdir(d):
                return d
        return os.path.expanduser("~")

    def load_video(self, video_path):
        # Simpan posisi video lama sebelum memuat yang baru
        if self.engine.cap and self.engine.video_path:
            cur_sec = self.engine.cur_idx / self.engine.fps
            from vidstamp.utils.file_manager import save_playback_state
            save_playback_state(self.engine.video_path, cur_sec)

        self.root.config(cursor="watch")
        self.root.update()
        
        self.right_panel.subtitle_list = []
        
        success = self.engine.load(video_path)
        self.root.config(cursor="")
        
        if not success:
            messagebox.showerror("Error", f"Gagal membuka berkas video:\n{video_path}")
            return
            
        # Prioritas 1: Cek subtitle eksternal (.srt) di folder yang sama
        external_sub = find_external_subtitle(video_path)
        if external_sub:
            subtitles = parse_srt_file(external_sub)
            self.right_panel.subtitle_list = subtitles
            self.right_panel.lbl_file.config(text=f"{os.path.basename(video_path)} ({len(subtitles)} subtitle eksternal dimuat)")
        # Prioritas 2: Fallback ke ekstraksi subtitle internal jika format mkv
        elif video_path.lower().endswith('.mkv'):
            self.right_panel.lbl_file.config(text=f"{os.path.basename(video_path)} (Ekstrak subtitle...)")
            self.root.update()
            
            extracted = extract_mkv_subtitles(video_path, self.temp_srt_path)
            if extracted:
                subtitles = parse_srt_file(self.temp_srt_path)
                self.right_panel.subtitle_list = subtitles
                self.right_panel.lbl_file.config(text=f"{os.path.basename(video_path)} ({len(subtitles)} subtitle internal dimuat)")
            else:
                self.right_panel.lbl_file.config(text=f"{os.path.basename(video_path)} (Tanpa subtitle internal)")
        else:
            self.right_panel.lbl_file.config(text=os.path.basename(video_path))
            
        # Sinkronkan pilihan dropdown video
        if hasattr(self.right_panel, "video_combo") and self.video_names:
            filename = os.path.basename(video_path)
            if filename in self.video_names:
                self.right_panel.video_combo.set(filename)
        
        total_sec = self.engine.total_frames / self.engine.fps
        self.right_panel.lbl_tot.config(text=format_remaining(0, total_sec))
        self.right_panel.lbl_cur.config(text=format_time(0))
        self.right_panel.seek_bar.config(to=max(1, self.engine.total_frames - 1))
        
        # Muat database adegan lama
        self.right_panel.load_saved_scenes()
        
        # Load posisi pemutaran terakhir (Resume Playback)
        from vidstamp.utils.file_manager import load_playback_state
        state = load_playback_state(video_path)
        last_pos = state.get("last_position_sec")
        if last_pos is not None:
            # Jeda 350ms untuk mencegah race condition/segfault di FFmpeg/ffpyplayer pada video bermasalah dengan header rusak
            target_frame = int(last_pos * self.engine.fps)
            def deferred_resume():
                if self.engine.cap and self.engine.video_path == video_path:
                    self.engine.seek_to(target_frame)
                    self.right_panel.seek_var.set(self.engine.cur_idx)
                    self.right_panel.render_current_frame()
            self.root.after(350, deferred_resume)
        else:
            self.right_panel.seek_var.set(0)
            
        self.right_panel.mark_start = None
        self.right_panel.mark_end = None
        self.right_panel.lbl_mk.config(text="")
        
        # Load Konfigurasi Skip OP/ED jika ada
        skip_data = load_skip_config(video_path)
        if not skip_data and video_path.lower().endswith(".mkv"):
            from vidstamp.core.exporter import get_mkv_chapters
            from vidstamp.utils.file_manager import save_skip_config
            detected_chapters = get_mkv_chapters(video_path)
            if detected_chapters:
                skip_data = detected_chapters
                # Simpan juga ke skip_config.json secara otomatis biar permanen
                save_skip_config(video_path, {
                    "op_start": skip_data.get("op_start"),
                    "op_end": skip_data.get("op_end"),
                    "ed_start": skip_data.get("ed_start"),
                    "ed_end": skip_data.get("ed_end"),
                    "auto_skip_enabled": True
                })
                
        self.right_panel.op_start = skip_data.get("op_start")
        self.right_panel.op_end = skip_data.get("op_end")
        self.right_panel.ed_start = skip_data.get("ed_start")
        self.right_panel.ed_end = skip_data.get("ed_end")
        self.right_panel.auto_skip.set(skip_data.get("auto_skip_enabled", True))
        
        self.skipped_op = False
        self.skipped_ed = False
        
        self.root.title(f"VidStamp - {os.path.basename(video_path)}")
        self.right_panel.render_current_frame()

    def _bind_global_shortcuts(self):
        self.root.bind("<space>",       lambda e: self.right_panel.toggle_play())
        self.root.bind("<Left>",        lambda e: self.right_panel._delta(-1))
        self.root.bind("<Right>",       lambda e: self.right_panel._delta(1))
        self.root.bind("<Shift-Left>",  lambda e: self.right_panel._delta(-10))
        self.root.bind("<Shift-Right>", lambda e: self.right_panel._delta(10))
        self.root.bind("<F11>",         self.right_panel.toggle_fullscreen)
        self.root.bind("<Escape>",      self._exit_fullscreen_only)
        self.root.bind("<Control-r>",   self._record_shortcut_handler)
        self.root.bind("<Control-R>",   self._record_shortcut_handler)
        self.root.bind("<Control-o>",   self._opening_shortcut_handler)
        self.root.bind("<Control-O>",   self._opening_shortcut_handler)
        self.root.bind("<Control-c>",   self._closing_shortcut_handler)
        self.root.bind("<Control-C>",   self._closing_shortcut_handler)
        self.root.bind("<Control-space>", lambda e: self.right_panel.cancel_recording_action())
        self.root.bind("<Control-m>",   lambda e: self.open_batch_merger())
        self.root.bind("<Control-M>",   lambda e: self.open_batch_merger())
        self.root.bind("<Tab>",         lambda e: self.right_panel.toggle_fullscreen_controls())
        self.root.bind("q",             lambda e: self.quit_app())
        self.root.bind("Q",             lambda e: self.quit_app())

    def _exit_fullscreen_only(self, event=None):
        if self.right_panel.is_fullscreen:
            self.right_panel.toggle_fullscreen()

    def _is_typing_focus(self):
        widget = self.root.focus_get()
        if widget is None:
            return False
        try:
            classname = widget.winfo_class()
            if classname in ("Entry", "Text", "TEntry", "TText"):
                return True
        except Exception:
            pass
        return False

    def _record_shortcut_handler(self, event=None):
        if self._is_typing_focus():
            return
        if not self.engine.cap:
            return
        if self.right_panel.mark_start is None:
            self.right_panel.mark_start_action()
        else:
            self.right_panel.mark_end_action()
            self.right_panel.save_scene_action()
        return "break"

    def _opening_shortcut_handler(self, event=None):
        if self._is_typing_focus():
            return
        if not self.engine.cap:
            return
        self.right_panel.record_opening_action()
        return "break"

    def _closing_shortcut_handler(self, event=None):
        if self._is_typing_focus():
            return
        if not self.engine.cap:
            return
        self.right_panel.record_closing_action()
        return "break"

    def playback_loop(self):
        if self.engine.playing and self.engine.cap:
            t0 = time.perf_counter()
            
            # Logika Auto-Skip OP/ED
            sec = self.engine.cur_idx / self.engine.fps
            
            # Reset flag jika user seek mundur sebelum start
            if self.right_panel.op_start is not None and sec < self.right_panel.op_start:
                self.skipped_op = False
            if self.right_panel.ed_start is not None and sec < self.right_panel.ed_start:
                self.skipped_ed = False
                
            if self.right_panel.auto_skip.get():
                # Skip OP
                if (self.right_panel.op_start is not None and self.right_panel.op_end is not None and
                    self.right_panel.op_start <= sec < self.right_panel.op_end and not self.skipped_op):
                    self.engine.seek_to(int(self.right_panel.op_end * self.engine.fps))
                    self.skipped_op = True
                    self.right_panel.skip_overlay_text = ">>> MELOMPATI OPENING <<<"
                    self.right_panel.skip_overlay_timer = 45 # ~1.5 detik notifikasi
                # Skip ED
                elif (self.right_panel.ed_start is not None and self.right_panel.ed_end is not None and
                      self.right_panel.ed_start <= sec < self.right_panel.ed_end and not self.skipped_ed):
                    self.engine.seek_to(int(self.right_panel.ed_end * self.engine.fps))
                    self.skipped_ed = True
                    self.right_panel.skip_overlay_text = ">>> MELOMPATI ENDING <<<"
                    self.right_panel.skip_overlay_timer = 45
            
            ret, frame = self.engine.get_next_frame()
            if ret:
                self.right_panel.draw_frame(frame)
                cur_sec = self.engine.cur_idx / self.engine.fps
                total_sec = self.engine.total_frames / self.engine.fps
                if not self.right_panel._seeking:
                    self.right_panel.seek_var.set(self.engine.cur_idx)
                self.right_panel.lbl_cur.config(text=format_time(cur_sec))
                self.right_panel.lbl_tot.config(text=format_remaining(cur_sec, total_sec))
            else:
                self.engine.set_playing(False)
                self.right_panel.btn_play.config(text="Play")
                
            elapsed = (time.perf_counter() - t0) * 1000
            frame_delay = 1000.0 / (self.engine.fps * self.engine.speed)
            delay = max(1, int(frame_delay - elapsed))
            self.root.after(delay, self.playback_loop)
        else:
            self.root.after(50, self.playback_loop)

    def open_folder_action(self):
        folder = filedialog.askdirectory(initialdir=self.current_folder or self.get_default_dir(),
                                         title="Pilih Folder Video")
        if folder:
            self.update_video_list_from_folder(folder)
            if self.video_list:
                self.load_video(self.video_list[0])
            else:
                messagebox.showinfo("Informasi", "Tidak ditemukan berkas video di folder terpilih.")

    def open_file_action(self):
        from vidstamp.config import VIDEO_EXTS
        file_types = [
            ("Video Files", " ".join(f"*{ext}" for ext in VIDEO_EXTS)),
            ("All Files", "*.*")
        ]
        file_path = filedialog.askopenfilename(initialdir=self.current_folder or self.get_default_dir(),
                                               title="Buka Berkas Video",
                                               filetypes=file_types)
        if file_path:
            folder = os.path.dirname(file_path)
            self.update_video_list_from_folder(folder)
            self.load_video(file_path)

    def select_video_action(self, video_name):
        if self.current_folder and video_name:
            target_path = os.path.join(self.current_folder, video_name)
            if os.path.exists(target_path):
                self.load_video(target_path)

    def update_video_list_from_folder(self, folder_path):
        self.current_folder = folder_path
        self.video_list = []
        self.video_names = []
        
        from vidstamp.config import VIDEO_EXTS
        if os.path.isdir(folder_path):
            files = sorted(os.listdir(folder_path))
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in VIDEO_EXTS:
                    full_path = os.path.join(folder_path, f)
                    self.video_list.append(full_path)
                    self.video_names.append(f)
                    
        if hasattr(self.right_panel, "video_combo"):
            if self.video_names:
                self.right_panel.video_combo.config(values=self.video_names)
            else:
                self.right_panel.video_combo.config(values=["Tidak ada video"])

    def open_notes_folder_action(self):
        if self.engine.video_path:
            folder = os.path.dirname(self.engine.video_path)
            if os.path.exists(folder):
                os.startfile(folder)
        else:
            folder = self.current_folder or self.get_default_dir()
            if os.path.exists(folder):
                os.startfile(folder)

    def open_batch_merger(self, event=None):
        current_dir = None
        if self.engine.video_path:
            current_dir = os.path.dirname(self.engine.video_path)
        else:
            current_dir = self.current_folder or self.get_default_dir()
            
        if not current_dir or not os.path.isdir(current_dir):
            messagebox.showerror("Pemberitahuan", "Silakan buka folder video terlebih dahulu.")
            return
            
        from vidstamp.ui.batch_merger import BatchMergerWizard
        BatchMergerWizard(self.root, current_dir)

    def open_extractor_tool(self, event=None):
        current_dir = None
        if self.engine.video_path:
            current_dir = os.path.dirname(self.engine.video_path)
        else:
            current_dir = self.current_folder or self.get_default_dir()
            
        from vidstamp.ui.extractor_tool import AudioSubExtractorWizard
        AudioSubExtractorWizard(self.root, current_dir)

    def quit_app(self):
        # Simpan posisi pemutaran detik terakhir saat aplikasi ditutup
        if self.engine.cap and self.engine.video_path:
            cur_sec = self.engine.cur_idx / self.engine.fps
            from vidstamp.utils.file_manager import save_playback_state
            save_playback_state(self.engine.video_path, cur_sec)

        self.engine.release()
        if os.path.exists(self.temp_srt_path):
            try:
                os.remove(self.temp_srt_path)
            except:
                pass
        self.root.destroy()

    def _start_auto_save_loop(self):
        """Menyimpan posisi pemutaran terakhir secara otomatis setiap 5 detik."""
        if self.engine.cap and self.engine.playing and self.engine.video_path:
            cur_sec = self.engine.cur_idx / self.engine.fps
            from vidstamp.utils.file_manager import save_playback_state
            save_playback_state(self.engine.video_path, cur_sec)
        
        self.root.after(5000, self._start_auto_save_loop)

def start_gui(start_path=None):
    from vidstamp.ui.launcher import LauncherWindow
    from vidstamp.config import ROOT_DIRS
    
    def get_default_dir():
        for d in ROOT_DIRS:
            if os.path.isdir(d):
                return d
        return os.path.expanduser("~")

    def launch_player():
        root = tk.Tk()
        from vidstamp.utils.logger import register_tkinter_exception_handler
        register_tkinter_exception_handler(root)
        root.geometry("1200x760")
        root.minsize(900, 580)
        
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("Horizontal.TScale", background="#0d0d1a", troughcolor="#1a1a3e",
                         sliderthickness=14, sliderrelief="flat")
                         
        app = VideoAppController(root, start_path)
        root.protocol("WM_DELETE_WINDOW", app.quit_app)
        root.mainloop()

    def launch_wizard(folder_path):
        root = tk.Tk()
        root.withdraw() # Sembunyikan window root
        
        from vidstamp.utils.logger import register_tkinter_exception_handler
        register_tkinter_exception_handler(root)
        
        from vidstamp.ui.batch_merger import BatchMergerWizard
        wizard = BatchMergerWizard(root, folder_path)
        
        def on_wizard_close():
            try: wizard.destroy()
            except: pass
            try: root.destroy()
            except: pass
            
        wizard.protocol("WM_DELETE_WINDOW", on_wizard_close)
        root.mainloop()

    # Jika start_path diberikan dan berupa file/folder valid, langsung buka player
    if start_path and os.path.exists(start_path):
        launch_player()
    else:
        # Jalankan launcher screen
        launcher = LauncherWindow(
            launch_player_fn=launch_player,
            launch_wizard_fn=launch_wizard,
            get_def_dir_fn=get_default_dir
        )
        launcher.mainloop()
