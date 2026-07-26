"""
vidstamp/ui/main_window.py - Koordinator Window Utama dan Event Loops
"""
import tkinter as tk
from tkinter import messagebox, ttk
import sys
import os
import time

# Impor dari paket vidstamp
from vidstamp.config import ROOT_DIRS
from vidstamp.utils.time_formatter import format_time
from vidstamp.core.subtitle import extract_mkv_subtitles, parse_srt_file, find_external_subtitle
from vidstamp.core.player import VideoPlayerEngine
from vidstamp.ui.browser import LeftBrowserPanel
from vidstamp.ui.player_view import RightPlayerPanel
from vidstamp.utils.file_manager import load_skip_config

class VideoAppController:
    def __init__(self, root, start_path=None):
        self.root = root
        self.root.title("VidStamp - Video Timestamp & Scene Marker")
        
        self.engine = VideoPlayerEngine()
        self.temp_srt_path = os.path.join(os.path.expanduser("~"), "temp_video_sub.srt")
        
        # Container layout paned window
        self.paned_window = tk.PanedWindow(self.root, orient="horizontal", bg="#0d0d1a",
                                           sashwidth=5, sashrelief="flat")
        self.paned_window.pack(fill="both", expand=True)
        
        self.browser_visible = True
        
        # State Penanda Skip OP/ED
        self.skipped_op = False
        self.skipped_ed = False
        
        # Panel Kiri
        self.left_panel = LeftBrowserPanel(self.paned_window, 
                                           on_video_select_callback=self.load_video,
                                           def_dir_callback=self.get_default_dir)
        self.paned_window.add(self.left_panel, minsize=180)
        
        # Panel Kanan
        self.right_panel = RightPlayerPanel(self.paned_window, self.engine,
                                             on_toggle_browser_callback=self.toggle_browser)
        self.paned_window.add(self.right_panel, minsize=600)
        
        self._bind_global_shortcuts()
        
        init_path = start_path or self.get_default_dir()
        if init_path and os.path.isdir(init_path):
            self.left_panel.navigate_to(init_path)
        elif init_path and os.path.isfile(init_path):
            self.left_panel.navigate_to(os.path.dirname(init_path))
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
            
        self.left_panel.highlight_video(video_path)
        
        self.right_panel.lbl_tot.config(text=format_time(self.engine.total_frames / self.engine.fps))
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
        self.right_panel.op_start = skip_data.get("op_start")
        self.right_panel.op_end = skip_data.get("op_end")
        self.right_panel.ed_start = skip_data.get("ed_start")
        self.right_panel.ed_end = skip_data.get("ed_end")
        self.right_panel.auto_skip.set(skip_data.get("auto_skip_enabled", True))
        
        self.skipped_op = False
        self.skipped_ed = False
        
        self.root.title(f"VidStamp - {os.path.basename(video_path)}")
        self.right_panel.render_current_frame()

    def toggle_browser(self, event=None):
        self.browser_visible = not self.browser_visible
        if self.browser_visible:
            self.paned_window.add(self.left_panel, before=self.right_panel, minsize=180)
            self.left_panel.pack(fill="both", expand=True)
        else:
            self.paned_window.forget(self.left_panel)
            
        self.root.update_idletasks()
        self.right_panel.render_current_frame()

    def _bind_global_shortcuts(self):
        self.root.bind("<space>",       lambda e: self.right_panel.toggle_play())
        self.root.bind("<Left>",        lambda e: self.right_panel._delta(-1))
        self.root.bind("<Right>",       lambda e: self.right_panel._delta(1))
        self.root.bind("<Shift-Left>",  lambda e: self.right_panel._delta(-10))
        self.root.bind("<Shift-Right>", lambda e: self.right_panel._delta(10))
        self.root.bind("<Tab>",         self.toggle_browser)
        self.root.bind("<F11>",         self.right_panel.toggle_fullscreen)
        self.root.bind("<Escape>",      self._exit_fullscreen_only)
        self.root.bind("<Control-t>",   self._record_shortcut_handler)
        self.root.bind("<Control-T>",   self._record_shortcut_handler)
        self.root.bind("<Control-space>", lambda e: self.right_panel.cancel_recording_action())
        self.root.bind("q",             lambda e: self.quit_app())
        self.root.bind("Q",             lambda e: self.quit_app())

    def _exit_fullscreen_only(self, event=None):
        if self.right_panel.is_fullscreen:
            self.right_panel.toggle_fullscreen()

    def _record_shortcut_handler(self, event=None):
        if not self.engine.cap:
            return
        if self.right_panel.mark_start is None:
            self.right_panel.mark_start_action()
        else:
            self.right_panel.mark_end_action()
            self.right_panel.save_scene_action()

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
                if not self.right_panel._seeking:
                    self.right_panel.seek_var.set(self.engine.cur_idx)
                self.right_panel.lbl_cur.config(text=format_time(self.engine.cur_idx / self.engine.fps, 
                                                                 self.right_panel.show_ms.get()))
            else:
                self.engine.set_playing(False)
                self.right_panel.btn_play.config(text="Play")
                
            elapsed = (time.perf_counter() - t0) * 1000
            frame_delay = 1000.0 / (self.engine.fps * self.engine.speed)
            delay = max(1, int(frame_delay - elapsed))
            self.root.after(delay, self.playback_loop)
        else:
            self.root.after(50, self.playback_loop)

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
