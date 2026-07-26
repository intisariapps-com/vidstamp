import tkinter as tk
from tkinter import messagebox, ttk
import sys
import os
import time
import threading
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

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
        
        self._loading = False

        
        # Panel Kiri
        self.left_panel = LeftBrowserPanel(self.paned_window, 
                                           on_video_select_callback=self.load_video,
                                           def_dir_callback=self.get_default_dir)
        self.paned_window.add(self.left_panel, minsize=180)
        
        # Panel Kanan
        self.right_panel = RightPlayerPanel(self.paned_window, self.engine,
                                             on_toggle_browser_callback=self.toggle_browser,
                                             on_settings_save_callback=self.on_settings_saved)
        self.paned_window.add(self.right_panel, minsize=600)

        # Daftarkan canvas untuk menerima drop file video (Drag & Drop)
        self.right_panel.canvas.drop_target_register(DND_FILES)
        self.right_panel.canvas.dnd_bind('<<Drop>>', self._on_file_drop)
        
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

    def _on_file_drop(self, event):
        file_path = event.data.strip()
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        
        if os.path.isfile(file_path):
            from vidstamp.utils.file_manager import load_global_config
            cfg_data = load_global_config()
            video_exts = cfg_data.get("video_exts", [".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv"])
            _, ext = os.path.splitext(file_path.lower())
            if ext in video_exts:
                self.load_video(file_path)
            else:
                messagebox.showwarning("File Tidak Didukung", f"Ekstensi file {ext} tidak terdaftar di pengaturan video.")

    def load_video(self, video_path):
        if getattr(self, "_loading", False):
            return
        self._loading = True
        
        try:
            self._load_video_internal(video_path)
        except Exception as e:
            self._loading = False
            import traceback
            try:
                with open("crash.log", "a", encoding="utf-8") as f:
                    f.write("=== LOAD_VIDEO EXCEPTION ===\n")
                    traceback.print_exc(file=f)
            except:
                pass
            messagebox.showerror("Error", f"Terjadi kesalahan saat memuat video:\n{e}")

    def _load_video_internal(self, video_path):
        # Simpan posisi video lama sebelum memuat yang baru
        if self.engine.cap and self.engine.video_path:
            cur_sec = self.engine.cur_idx / self.engine.fps
            from vidstamp.utils.file_manager import save_playback_state
            save_playback_state(self.engine.video_path, cur_sec)

        self.root.configure(cursor="watch")
        self.root.update()
        
        self.right_panel.subtitle_list = []
        
        success = self.engine.load(video_path)
        self.root.configure(cursor="")
        
        if not success:
            messagebox.showerror("Error", f"Gagal membuka berkas video:\n{video_path}")
            self._loading = False
            return
            
        self.left_panel.highlight_video(video_path)
        
        tot_sec = self.engine.total_frames / self.engine.fps
        self.right_panel.lbl_time.configure(text=f"00:00.000 / {format_time(tot_sec, self.right_panel.show_ms.get())}")
        self.right_panel.seek_bar.configure(to=max(1, self.engine.total_frames - 1))
        
        # Muat database adegan lama
        self.right_panel.load_saved_scenes()
        
        # Load posisi pemutaran terakhir (Resume Playback)
        from vidstamp.utils.file_manager import load_playback_state
        state = load_playback_state(video_path)
        last_pos = state.get("last_position_sec")
        if last_pos is not None:
            import cv2
            # Posisikan OpenCV frame secara instan agar user langsung melihat gambarnya
            target_frame = int(last_pos * self.engine.fps)
            target_frame = max(0, min(target_frame, self.engine.total_frames - 1))
            self.engine.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            self.engine.cur_idx = int(self.engine.cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            self.right_panel.seek_var.set(self.engine.cur_idx)
            
            # Tunda pemanggilan seek audio player selama 500ms agar thread ffpyplayer siap
            def delayed_audio_seek():
                if self.engine.video_path == video_path and self.engine.audio_player:
                    try:
                        self.engine.audio_player.seek(last_pos, relative=False)
                    except:
                        pass
            self.root.after(500, delayed_audio_seek)
        else:
            self.right_panel.seek_var.set(0)

            
        self.right_panel.mark_start = None
        self.right_panel.mark_end = None
        self.right_panel.lbl_mk.configure(text="")
        
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

        # Prioritas 1: Cek subtitle eksternal (.srt) di folder yang sama
        external_sub = find_external_subtitle(video_path)
        if external_sub:
            subtitles = parse_srt_file(external_sub)
            self.right_panel.subtitle_list = subtitles
            self.right_panel.lbl_file.configure(text=f"{os.path.basename(video_path)} ({len(subtitles)} subtitle eksternal dimuat)")
            self._loading = False
        # Prioritas 2: Fallback ke ekstraksi subtitle internal jika format mkv
        elif video_path.lower().endswith('.mkv'):
            self.right_panel.lbl_file.configure(text=f"{os.path.basename(video_path)} (Mengekstrak subtitle...)")
            
            def bg_extract():
                try:
                    extracted = extract_mkv_subtitles(video_path, self.temp_srt_path)
                except Exception:
                    extracted = False
                
                self.root.after(0, lambda: self._on_mkv_extract_complete(video_path, extracted))
                
            threading.Thread(target=bg_extract, daemon=True).start()
        else:
            self.right_panel.lbl_file.configure(text=os.path.basename(video_path))
            self._loading = False

    def _on_mkv_extract_complete(self, video_path, extracted):
        if self.engine.video_path == video_path:
            if extracted:
                subtitles = parse_srt_file(self.temp_srt_path)
                self.right_panel.subtitle_list = subtitles
                self.right_panel.lbl_file.configure(text=f"{os.path.basename(video_path)} ({len(subtitles)} subtitle internal dimuat)")
            else:
                self.right_panel.lbl_file.configure(text=f"{os.path.basename(video_path)} (Tanpa subtitle internal)")
        self._loading = False


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
                cur_sec = self.engine.cur_idx / self.engine.fps
                tot_sec = self.engine.total_frames / self.engine.fps
                self.right_panel.lbl_time.configure(text=f"{format_time(cur_sec, self.right_panel.show_ms.get())} / {format_time(tot_sec, self.right_panel.show_ms.get())}")
            else:
                self.engine.set_playing(False)
                self.right_panel.btn_play.configure(text="▶")
                
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
        """Menyimpan posisi pemutaran terakhir secara otomatis sesuai pengaturan global."""
        if self.engine.cap and self.engine.playing and self.engine.video_path:
            cur_sec = self.engine.cur_idx / self.engine.fps
            from vidstamp.utils.file_manager import save_playback_state
            save_playback_state(self.engine.video_path, cur_sec)
        
        from vidstamp.utils.file_manager import load_global_config
        cfg_data = load_global_config()
        interval_ms = max(1, cfg_data.get("auto_save_interval", 5)) * 1000
        
        self.root.after(interval_ms, self._start_auto_save_loop)

    def on_settings_saved(self):
        """Triggered ketika pengguna mengklik simpan pengaturan global."""
        from vidstamp.utils.file_manager import load_global_config
        import vidstamp.config as cfg
        new_config = load_global_config()
        
        # Perbarui variabel konfigurasi global di memori
        cfg.ROOT_DIRS = new_config.get("root_dirs", cfg.ROOT_DIRS)
        cfg.VIDEO_EXTS = set(new_config.get("video_exts", cfg.VIDEO_EXTS))
        
        # Segarkan navigasi folder browser di panel kiri
        init_path = self.get_default_dir()
        if init_path and os.path.isdir(init_path):
            self.left_panel.navigate_to(init_path)
            
        # Segarkan canvas video saat ini agar timestamp/milidetik langsung terupdate
        if self.engine.cap:
            self.right_panel.render_current_frame()


class CTkDnD(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

def start_gui(start_path=None):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = CTkDnD()
    root.geometry("1200x760")
    root.minsize(900, 580)
    
    def report_callback_exception(exc, val, tb):
        import traceback
        try:
            with open("crash.log", "a", encoding="utf-8") as f:
                f.write("=== TKINTER CALLBACK EXCEPTION ===\n")
                traceback.print_exception(exc, val, tb, file=f)
        except:
            pass
        sys.__stderr__.write("Tkinter Callback Exception:\n")
        traceback.print_exception(exc, val, tb, file=sys.__stderr__)

    root.report_callback_exception = report_callback_exception
    
    # Inisialisasi controller utama
    app = VideoAppController(root, start_path)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()

