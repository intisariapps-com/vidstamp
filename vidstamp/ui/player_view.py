"""
vidstamp/ui/player_view.py - Komponen UI Media Player Utama berbasis PySide6
"""
import os
import re
import cv2
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QComboBox, QLineEdit, 
                             QListWidget, QTextEdit, QFileDialog, QMessageBox, 
                             QGroupBox, QApplication, QSizePolicy, QCheckBox)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QImage, QPixmap, QKeyEvent

from vidstamp.core.player import VideoPlayerEngine
from vidstamp.core.subtitle import parse_srt_file
from vidstamp.utils.time_formatter import format_time, format_remaining

FONT = cv2.FONT_HERSHEY_DUPLEX
COLOR_BG = (0, 0, 0)
COLOR_TS = (0, 255, 255)
COLOR_MARK = (0, 255, 0)
COLOR_END = (0, 0, 255)

class PlayerView(QWidget):
    def __init__(self, parent=None, on_video_loaded_callback=None):
        super().__init__(parent)
        self.engine = VideoPlayerEngine()
        self.on_video_loaded = on_video_loaded_callback
        
        self.subtitle_list = []
        self.scenes = []
        self.mark_start = None
        self.mark_end = None
        
        # State
        self.is_fullscreen = False
        self.skip_overlay_text = ""
        self.skip_overlay_timer = 0
        self.show_ts_enabled = True
        self.show_ms_enabled = True
        self.temp_srt_path = ""
        
        # State Penanda Skip OP/ED
        self.op_start = None
        self.op_end = None
        self.ed_start = None
        self.ed_end = None
        self.skipped_op = False
        self.skipped_ed = False
        
        self._build_ui()
        self._apply_stylesheet()
        self._setup_shortcuts()
        
        # Timer Loop Playback
        self.timer = QTimer(self)
        self.timer.setInterval(15) # ~60fps refresh limit
        self.timer.timeout.connect(self.update_loop)
        
        # Timer Auto Save Playback State (setiap 5 detik)
        self.save_timer = QTimer(self)
        self.save_timer.setInterval(5000)
        self.save_timer.timeout.connect(self._auto_save_playback_state)
        self.save_timer.start()

    def _build_ui(self):
        # Layout utama berorientasi vertikal murni
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(6)
        
        # 1. Canvas Panel (Display Frame OpenCV)
        self.canvas_container = QWidget(self)
        self.canvas_container.setObjectName("CanvasContainer")
        self.canvas_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        canvas_layout = QVBoxLayout(self.canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_canvas = QLabel(self.canvas_container)
        self.lbl_canvas.setObjectName("CanvasLabel")
        self.lbl_canvas.setAlignment(Qt.AlignCenter)
        self.lbl_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_canvas.setMinimumSize(400, 225) # Aspek 16:9 dasar
        # Double Click event filter untuk fullscreen
        self.lbl_canvas.mouseDoubleClickEvent = self.toggle_fullscreen
        self.lbl_canvas.mousePressEvent = self._on_canvas_clicked
        
        canvas_layout.addWidget(self.lbl_canvas)
        self.main_layout.addWidget(self.canvas_container)
        
        # 2. Seek Bar & Time Display
        self.seek_frame = QWidget(self)
        seek_layout = QHBoxLayout(self.seek_frame)
        seek_layout.setContentsMargins(5, 0, 5, 0)
        
        self.lbl_time_cur = QLabel("00:00:00.000", self.seek_frame)
        self.lbl_time_cur.setObjectName("TimeLabel")
        
        self.slider = QSlider(Qt.Horizontal, self.seek_frame)
        self.slider.setObjectName("SeekBar")
        self.slider.setRange(0, 1000)
        self.slider.setValue(0)
        self.slider.sliderMoved.connect(self._on_slider_moved)
        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderReleased.connect(self._on_slider_released)
        
        self.lbl_time_total = QLabel("00:00:00.000", self.seek_frame)
        self.lbl_time_total.setObjectName("TimeLabel")
        
        seek_layout.addWidget(self.lbl_time_cur)
        seek_layout.addWidget(self.slider)
        seek_layout.addWidget(self.lbl_time_total)
        self.main_layout.addWidget(self.seek_frame)
        
        # 3. Control Panel (Playback Navigasi & Markers)
        self.ctrl_panel = QWidget(self)
        ctrl_layout = QHBoxLayout(self.ctrl_panel)
        ctrl_layout.setContentsMargins(5, 0, 5, 0)
        ctrl_layout.setSpacing(6)
        
        btn_rew10 = QPushButton("-10s", self.ctrl_panel)
        btn_rew10.clicked.connect(lambda: self.seek_offset(-10))
        btn_rew1 = QPushButton("-1s", self.ctrl_panel)
        btn_rew1.clicked.connect(lambda: self.seek_offset(-1))
        
        self.btn_play = QPushButton("Play", self.ctrl_panel)
        self.btn_play.setObjectName("PlayButton")
        self.btn_play.clicked.connect(self.toggle_play)
        
        btn_ff1 = QPushButton("+1s", self.ctrl_panel)
        btn_ff1.clicked.connect(lambda: self.seek_offset(1))
        btn_ff10 = QPushButton("+10s", self.ctrl_panel)
        btn_ff10.clicked.connect(lambda: self.seek_offset(10))
        
        # Jump To Input
        lbl_go = QLabel("Ke detik:", self.ctrl_panel)
        lbl_go.setObjectName("ControlText")
        self.txt_go = QLineEdit(self.ctrl_panel)
        self.txt_go.setObjectName("GoInput")
        self.txt_go.setFixedWidth(50)
        self.txt_go.returnPressed.connect(self._jump_to_seconds)
        
        btn_go = QPushButton("GO", self.ctrl_panel)
        btn_go.setObjectName("GoButton")
        btn_go.clicked.connect(self._jump_to_seconds)
        
        # Speed
        lbl_speed = QLabel("Speed:", self.ctrl_panel)
        lbl_speed.setObjectName("ControlText")
        self.combo_speed = QComboBox(self.ctrl_panel)
        self.combo_speed.addItems(["0.25x", "0.5x", "1.0x", "1.5x", "2.0x", "3.0x"])
        self.combo_speed.setCurrentText("1.0x")
        self.combo_speed.currentTextChanged.connect(self._on_speed_changed)
        
        # Checkbox Auto Skip OP/ED
        self.cb_auto_skip = QCheckBox("Auto Skip OP/ED", self.ctrl_panel)
        self.cb_auto_skip.setObjectName("OptionCheckbox")
        self.cb_auto_skip.setChecked(True)
        
        # Marker Buttons
        self.btn_start = QPushButton("[M] Start", self.ctrl_panel)
        self.btn_start.setObjectName("StartMarker")
        self.btn_start.clicked.connect(self._mark_start_fn)
        
        self.btn_end = QPushButton("[N] End", self.ctrl_panel)
        self.btn_end.setObjectName("EndMarker")
        self.btn_end.clicked.connect(self._mark_end_fn)
        
        # Concat styles to control panel
        for btn in [btn_rew10, btn_rew1, btn_ff1, btn_ff10, btn_go]:
            btn.setObjectName("NavButton")
            btn.setCursor(Qt.PointingHandCursor)
            
        ctrl_layout.addWidget(btn_rew10)
        ctrl_layout.addWidget(btn_rew1)
        ctrl_layout.addWidget(self.btn_play)
        ctrl_layout.addWidget(btn_ff1)
        ctrl_layout.addWidget(btn_ff10)
        ctrl_layout.addWidget(lbl_go)
        ctrl_layout.addWidget(self.txt_go)
        ctrl_layout.addWidget(btn_go)
        ctrl_layout.addWidget(lbl_speed)
        ctrl_layout.addWidget(self.combo_speed)
        ctrl_layout.addWidget(self.cb_auto_skip)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_end)
        self.main_layout.addWidget(self.ctrl_panel)
        
        # 4. Info Bar Pintasan
        self.inf_bar = QLabel("Space = Play/Pause | DoubleClick = Fullscreen | Ctrl+T = Record | Ctrl+Space = Batal | Q = Keluar", self)
        self.inf_bar.setObjectName("InfoBar")
        self.inf_bar.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.inf_bar)

    def _apply_stylesheet(self):
        qss = """
        #TopBar {
            background-color: #16213e;
            border-bottom: 2px solid #1f4068;
            border-radius: 4px;
        }
        #VideoTitle {
            color: #a8dadc;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
            font-weight: bold;
        }
        #OpenButton {
            background-color: #e94560;
            color: white;
            border: none;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 10px;
        }
        #OpenButton:hover {
            background-color: #ff5e7e;
        }
        #CanvasContainer {
            background-color: #000000;
            border: 2px solid #1f4068;
            border-radius: 6px;
        }
        #TimeLabel {
            color: #8888aa;
            font-family: 'Consolas', monospace;
            font-size: 11px;
        }
        #SeekBar::groove:horizontal {
            border: 1px solid #1f4068;
            height: 10px;
            background: #1a1a3e;
            border-radius: 4px;
        }
        #SeekBar::handle:horizontal {
            background: #e94560;
            width: 14px;
            border-radius: 7px;
            margin: -2px 0;
        }
        #PlayButton {
            background-color: #1e5f3a;
            color: white;
            border: none;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: bold;
            padding: 5px 18px;
        }
        #PlayButton:hover {
            background-color: #2a7f50;
        }
        #NavButton {
            background-color: #16213e;
            color: #7ec8e3;
            border: 1px solid #1f4068;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
            padding: 4px 8px;
        }
        #NavButton:hover {
            background-color: #1a1a3e;
        }
        #ControlText {
            color: #8888aa;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }
        #GoInput {
            background-color: #16213e;
            color: white;
            border: 1px solid #1f4068;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            padding: 2px;
        }
        #GoButton {
            background-color: #e94560;
            color: white;
            border: none;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
            font-weight: bold;
            padding: 4px 8px;
        }
        #StartMarker {
            background-color: #1a4a6e;
            color: white;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: bold;
            padding: 5px 12px;
            border-radius: 4px;
        }
        #EndMarker {
            background-color: #5c1a1a;
            color: white;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: bold;
            padding: 5px 12px;
            border-radius: 4px;
        }
        #InfoBar {
            color: #555577;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 9px;
        }
        #SceneFrame {
            color: #a8dadc;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
            border: 1px solid #1f4068;
            border-radius: 6px;
        }
        #SceneList {
            background-color: #0d0d1a;
            color: #e0e0ff;
            border: none;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }
        #SceneList::item:hover {
            background-color: #16213e;
        }
        #SceneList::item:selected {
            background-color: #e94560;
            color: white;
        }
        #SceneActionButton {
            background-color: #16213e;
            color: white;
            border: none;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
            padding: 4px 10px;
            min-width: 60px;
        }
        #SceneActionButton:hover {
            background-color: #1a1a3e;
        }
        #DeleteSceneButton {
            background-color: #5c1a1a;
        }
        #DeleteSceneButton:hover {
            background-color: #7c2222;
        }
        #ExportSceneButton {
            background-color: #1e5f3a;
        }
        #ExportSceneButton:hover {
            background-color: #2a7f50;
        }
        #DetailFrame {
            color: #a8dadc;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
            border: 1px solid #1f4068;
            border-radius: 6px;
        }
        #DetailText {
            background-color: #0b0b18;
            color: #8888aa;
            border: none;
            font-family: 'Consolas', monospace;
            font-size: 11px;
        }
        """
        self.setStyleSheet(qss)

    def _setup_shortcuts(self):
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()
        
        if key == Qt.Key_Space:
            self.toggle_play()
        elif key == Qt.Key_M:
            self._mark_start_fn()
        elif key == Qt.Key_N:
            self._mark_end_fn()
        elif key == Qt.Key_Q:
            QApplication.quit()
        elif modifiers & Qt.ControlModifier and key == Qt.Key_T:
            self._toggle_record_shortcut()
        elif modifiers & Qt.ControlModifier and key == Qt.Key_Space:
            self._cancel_record_shortcut()
        else:
            super().keyPressEvent(event)

    def _toggle_record_shortcut(self):
        if self.mark_start is None:
            self._mark_start_fn()
        else:
            self._mark_end_fn()

    def _cancel_record_shortcut(self):
        self.mark_start = None
        self.mark_end = None
        self.skip_overlay_text = ""
        self.lbl_status_bar_update("Perekaman dibatalkan.")

    def lbl_status_bar_update(self, text):
        self.inf_bar.setText(text)

    # ── Playback Logic ──
    def load_video(self, path):
        if not path or not os.path.exists(path):
            return
            
        self.timer.stop()
        self.engine.release()
        
        success = self.engine.load(path)
        if success:
            self.lbl_title.setText(os.path.basename(path))
            self.lbl_time_total.setText(format_time(self.engine.total_frames / self.engine.fps))
            self.slider.setRange(0, self.engine.total_frames - 1)
            self.slider.setValue(0)
            
            # Load Subtitle
            self.subtitle_list = []
            self.temp_srt_path = os.path.join(os.path.dirname(path), "temp_player_sub.srt")
            
            from vidstamp.core.subtitle import extract_mkv_subtitles, find_external_subtitle, filter_karaoke_spam
            ext_srt = find_external_subtitle(path)
            if ext_srt:
                self.subtitle_list = filter_karaoke_spam(parse_srt_file(ext_srt))
                self.lbl_status_bar_update("Memuat subtitle eksternal SRT.")
            elif path.lower().endswith(".mkv"):
                extracted = extract_mkv_subtitles(path, self.temp_srt_path)
                if extracted and os.path.exists(self.temp_srt_path):
                    self.subtitle_list = filter_karaoke_spam(parse_srt_file(self.temp_srt_path))
                    self.lbl_status_bar_update("Memuat subtitle internal MKV.")
                    try: os.remove(self.temp_srt_path)
                    except: pass
                else:
                    self.lbl_status_bar_update("Trek subtitle internal tidak ditemukan.")
            else:
                self.lbl_status_bar_update("Video dimuat tanpa subtitel.")
                
            self.load_saved_scenes()
            
            # Load Konfigurasi Skip OP/ED
            from vidstamp.utils.file_manager import load_skip_config, save_skip_config
            skip_data = load_skip_config(path)
            if not skip_data and path.lower().endswith(".mkv"):
                from vidstamp.core.exporter import get_mkv_chapters
                detected_chapters = get_mkv_chapters(path)
                if detected_chapters:
                    skip_data = detected_chapters
                    save_skip_config(path, {
                        "op_start": skip_data.get("op_start"),
                        "op_end": skip_data.get("op_end"),
                        "ed_start": skip_data.get("ed_start"),
                        "ed_end": skip_data.get("ed_end"),
                        "auto_skip_enabled": True
                    })
                    
            self.op_start = skip_data.get("op_start")
            self.op_end = skip_data.get("op_end")
            self.ed_start = skip_data.get("ed_start")
            self.ed_end = skip_data.get("ed_end")
            self.cb_auto_skip.setChecked(skip_data.get("auto_skip_enabled", True))
            
            self.skipped_op = False
            self.skipped_ed = False
            
            self.render_current_frame()
            
            # Load posisi pemutaran terakhir (Resume Playback)
            from vidstamp.utils.file_manager import load_playback_state
            state = load_playback_state(path)
            last_pos = state.get("last_position_sec")
            if last_pos is not None:
                target_frame = int(last_pos * self.engine.fps)
                def deferred_resume():
                    if self.engine.cap and self.engine.video_path == path:
                        self.engine.seek_to(target_frame)
                        self.slider.setValue(self.engine.cur_idx)
                        self.render_current_frame()
                QTimer.singleShot(350, deferred_resume)
            else:
                self.slider.setValue(0)
            
            if self.on_video_loaded:
                self.on_video_loaded(path)
        else:
            QMessageBox.critical(self, "Error", "Gagal memuat berkas video!")

    def toggle_play(self):
        if not self.engine.cap:
            return
        state = not self.engine.playing
        self.engine.set_playing(state)
        if state:
            self.btn_play.setText("Pause")
            self.btn_play.setStyleSheet("background-color: #e94560;")
            self.timer.start()
        else:
            self.btn_play.setText("Play")
            self.btn_play.setStyleSheet("background-color: #1e5f3a;")
            self.timer.stop()

    def update_loop(self):
        if not self.engine.playing:
            return
            
        sec = self.engine.cur_idx / self.engine.fps
        
        if self.op_start is not None and sec < self.op_start:
            self.skipped_op = False
        if self.ed_start is not None and sec < self.ed_start:
            self.skipped_ed = False
            
        if self.cb_auto_skip.isChecked():
            if (self.op_start is not None and self.op_end is not None and
                self.op_start <= sec < self.op_end and not self.skipped_op):
                self.engine.seek_to(int(self.op_end * self.engine.fps))
                self.skipped_op = True
                self.skip_overlay_text = ">>> MELOMPATI OPENING <<<"
                self.skip_overlay_timer = 45
            elif (self.ed_start is not None and self.ed_end is not None and
                  self.ed_start <= sec < self.ed_end and not self.skipped_ed):
                self.engine.seek_to(int(self.ed_end * self.engine.fps))
                self.skipped_ed = True
                self.skip_overlay_text = ">>> MELOMPATI ENDING <<<"
                self.skip_overlay_timer = 45

        if self.skip_overlay_timer > 0:
            self.skip_overlay_timer -= 1
            if self.skip_overlay_timer == 0:
                self.skip_overlay_text = ""
            
        ret, frame = self.engine.get_next_frame()
        if ret and frame is not None:
            self._draw_frame_on_canvas(frame)
            self._update_time_slider()
        else:
            self.toggle_play()
            self.engine.seek_to(0)
            self._update_time_slider()
            self.render_current_frame()

    def _update_time_slider(self):
        idx = self.engine.cur_idx
        self.slider.setValue(idx)
        self.lbl_time_cur.setText(format_time(idx / self.engine.fps))

    def _auto_save_playback_state(self):
        if self.engine.cap and self.engine.playing and self.engine.video_path:
            cur_sec = self.engine.cur_idx / self.engine.fps
            from vidstamp.utils.file_manager import save_playback_state
            save_playback_state(self.engine.video_path, cur_sec)

    def render_current_frame(self):
        if not self.engine.cap:
            return
        frame = self.engine.read_single_frame(self.engine.cur_idx)
        if frame is not None:
            self._draw_frame_on_canvas(frame)

    def _draw_frame_on_canvas(self, frame):
        h, w, _ = frame.shape
        sec = self.engine.cur_idx / self.engine.fps
        
        if self.skip_overlay_text:
            (tw, th), _ = cv2.getTextSize(self.skip_overlay_text, FONT, 1.2, 7)
            tx = (w - tw) // 2
            ty = h // 3
            cv2.putText(frame, self.skip_overlay_text, (tx, ty), FONT, 1.2, COLOR_BG, 7, cv2.LINE_AA)
            cv2.putText(frame, self.skip_overlay_text, (tx, ty), FONT, 1.2, (50, 150, 255), 3, cv2.LINE_AA)
            
        if self.show_ts_enabled:
            lbl = f"  {format_time(sec, self.show_ms_enabled)}"
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
                t_rec = f"REC: {format_time(sec - self.mark_start)}"
                cv2.putText(frame, t_rec, (8, h - 56), FONT, 0.75, COLOR_BG, 4, cv2.LINE_AA)
                cv2.putText(frame, t_rec, (8, h - 56), FONT, 0.75, (0, 0, 255), 2, cv2.LINE_AA)
                
        if self.mark_end is not None:
            t = f"END: {format_time(self.mark_end)}"
            (tw, _), _ = cv2.getTextSize(t, FONT, 0.75, 2)
            cv2.putText(frame, t, (w - tw - 12, h - 28), FONT, 0.75, COLOR_BG, 4, cv2.LINE_AA)
            cv2.putText(frame, t, (w - tw - 12, h - 28), FONT, 0.75, COLOR_END, 2, cv2.LINE_AA)
            
        if self.subtitle_list:
            active_subs = [s for s in self.subtitle_list if s['start'] <= sec < s['end']]
            if active_subs:
                sub_text = active_subs[0]['text']
                sub_text = re.sub(r'<[^>]*>', '', sub_text)
                sub_text = re.sub(r'\{[^}]*\}', '', sub_text).strip()
                
                font_scale = max(0.35, min(0.7, h / 1300.0))
                thickness = max(1, int(2.0 * font_scale))
                shadow_thickness = thickness + 2
                
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
                    
                    cv2.putText(frame, line, (tx, ty), FONT, font_scale, COLOR_BG, shadow_thickness, cv2.LINE_AA)
                    cv2.putText(frame, line, (tx, ty), FONT, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
                    
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ch_h, ch_w, ch = rgb_image.shape
        bytes_per_line = ch * ch_w
        qimg = QImage(rgb_image.data, ch_w, ch_h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        self.lbl_canvas.setPixmap(pixmap.scaled(
            self.lbl_canvas.size(), Qt.KeepAspectRatio, Qt.FastTransformation
        ))

    def _wrap_text(self, text, font, scale, thickness, max_w):
        words = text.split(' ')
        lines = []
        curr = ""
        for w in words:
            test_line = f"{curr} {w}".strip()
            (tw, _), _ = cv2.getTextSize(test_line, font, scale, thickness)
            if tw <= max_w:
                curr = test_line
            else:
                if curr:
                    lines.append(curr)
                curr = w
        if curr:
            lines.append(curr)
        return lines

    def seek_offset(self, seconds):
        if not self.engine.cap:
            return
        target = self.engine.cur_idx + int(seconds * self.engine.fps)
        self.engine.seek_to(target)
        self._update_time_slider()
        if not self.engine.playing:
            self.render_current_frame()

    def _on_slider_pressed(self):
        self._was_playing = self.engine.playing
        if self._was_playing:
            self.timer.stop()

    def _on_slider_released(self):
        if self._was_playing:
            self.timer.start()

    def _on_slider_moved(self, val):
        if not self.engine.cap:
            return
        self.engine.seek_to(val)
        self.lbl_time_cur.setText(format_time(val / self.engine.fps))
        if not self.engine.playing:
            self.render_current_frame()

    def _on_canvas_clicked(self, event):
        self.toggle_play()

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        parent_window = self.window()
        if self.is_fullscreen:
            self.top_bar.hide()
            self.seek_frame.hide()
            self.ctrl_panel.hide()
            self.inf_bar.hide()
            self.sidebar_container.hide()
            parent_window.showFullScreen()
        else:
            self.top_bar.show()
            self.seek_frame.show()
            self.ctrl_panel.show()
            self.inf_bar.show()
            self.sidebar_container.show()
            parent_window.showNormal()
        self.render_current_frame()

    def _on_speed_changed(self, text):
        val = float(text.replace("x", ""))
        self.engine.set_speed(val)
        self.timer.setInterval(int(15 / val))

    def _jump_to_seconds(self):
        if not self.engine.cap:
            return
        t = self.txt_go.text().strip()
        try:
            if ":" in t:
                parts = t.split(":")
                secs = 0.0
                for p in parts:
                    secs = secs * 60 + float(p)
            else:
                secs = float(t)
            self.engine.seek_to(int(secs * self.engine.fps))
            self._update_time_slider()
            self.render_current_frame()
        except ValueError:
            pass

    def _mark_start_fn(self):
        if not self.engine.cap:
            return
        self.mark_start = self.engine.cur_idx / self.engine.fps
        self.btn_start.setText(f"S: {format_time(self.mark_start)}")
        self.lbl_status_bar_update("Batas START tercatat. Jalankan video dan klik [N] End untuk mengunci adegan.")
        self.render_current_frame()

    def _mark_end_fn(self):
        if not self.engine.cap or self.mark_start is None:
            return
        self.mark_end = self.engine.cur_idx / self.engine.fps
        self.btn_end.setText(f"E: {format_time(self.mark_end)}")
        self.render_current_frame()
        
        from PySide6.QtWidgets import QInputDialog
        label, ok = QInputDialog.getItem(self, "Jenis Adegan", "Pilih label adegan skip:", ["Skip_Opening", "Skip_Ending"], 0, False)
        if ok and label:
            subs_in_range = []
            for s in self.subtitle_list:
                if s['start'] >= self.mark_start and s['end'] <= self.mark_end:
                    clean_txt = re.sub(r'<[^>]*>', '', s['text'])
                    clean_txt = re.sub(r'\{[^}]*\}', '', clean_txt).strip()
                    if clean_txt:
                        subs_in_range.append(f"[{format_time(s['start'])}] {clean_txt}")
                        
            sub_summary = "\n".join(subs_in_range)
            self.scenes.append((self.mark_start, self.mark_end, label, sub_summary))
            
            from vidstamp.utils.file_manager import save_scenes_data
            save_scenes_data(self.engine.video_path, self.scenes)
            self._auto_export_scenes()
            
            self.load_saved_scenes()
            self.lbl_status_bar_update(f"Adegan '{label}' berhasil disimpan.")
            
            self.mark_start = None
            self.mark_end = None
            self.btn_start.setText("[M] Start")
            self.btn_end.setText("[N] End")
            self.render_current_frame()

    def load_saved_scenes(self):
        self.scenes = []
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

    def open_scenes_dialog(self):
        if not self.engine.cap or not self.engine.video_path:
            QMessageBox.critical(self, "Pemberitahuan", "Silakan muat file video terlebih dahulu.")
            return
        dialog = SceneListDialog(self)
        dialog.exec()

    def _auto_export_scenes(self):
        if not self.engine.cap or not self.engine.video_path:
            return
        try:
            from vidstamp.utils.file_manager import ensure_note_folder
            note_dir = ensure_note_folder(self.engine.video_path)
            video_name = os.path.basename(self.engine.video_path)
            video_base, _ = os.path.splitext(video_name)
            default_file = os.path.join(note_dir, f"{video_base}_catatan_adegan.txt")
            
            with open(default_file, "w", encoding="utf-8") as f:
                f.write(f"=== CATATAN ADEGAN VIDEO ===\n")
                f.write(f"Video Asli: {os.path.abspath(self.engine.video_path)}\n")
                f.write(f"Total Adegan Tercatat: {len(self.scenes)}\n\n")
                
                for idx, (s, e, label, subs) in enumerate(self.scenes):
                    dur = e - s
                    f.write(f"{idx+1}. [{format_time(s)} -> {format_time(e)}] ({dur:.2f}s) - {label}\n")
                    if subs:
                        f.write(f"--- Dialog Tercatat ---\n{subs}\n")
                    f.write("="*40 + "\n")
        except Exception as err:
            print(f"Gagal melakukan ekspor otomatis catatan: {err}")

from PySide6.QtWidgets import QDialog, QListWidget, QTextEdit, QGroupBox

class SceneListDialog(QDialog):
    def __init__(self, parent_player):
        super().__init__(parent_player)
        self.player = parent_player
        self.setWindowTitle("Daftar Catatan Adegan - VidStamp")
        self.resize(500, 420)
        self.setMinimumSize(400, 320)
        self.setObjectName("SceneListDialog")
        
        self._build_ui()
        self._apply_stylesheet()
        self.load_scenes()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        self.sc_label_frame = QGroupBox(" Adegan Tercatat ", self)
        self.sc_label_frame.setObjectName("SceneFrame")
        sc_layout = QVBoxLayout(self.sc_label_frame)
        sc_layout.setContentsMargins(8, 8, 8, 8)
        sc_layout.setSpacing(6)
        
        self.sc_lb = QListWidget(self.sc_label_frame)
        self.sc_lb.setObjectName("SceneList")
        self.sc_lb.itemSelectionChanged.connect(self._on_sc_select)
        self.sc_lb.itemDoubleClicked.connect(self._jump_sc)
        
        sc_btn_layout = QHBoxLayout()
        sc_btn_layout.setSpacing(6)
        
        self.btn_sc_jump = QPushButton("Lompat", self.sc_label_frame)
        self.btn_sc_jump.clicked.connect(self._jump_sc)
        
        self.btn_sc_del = QPushButton("Hapus", self.sc_label_frame)
        self.btn_sc_del.setObjectName("DeleteSceneButton")
        self.btn_sc_del.clicked.connect(self._del_sc)
        
        self.btn_sc_exp = QPushButton("Export Video", self.sc_label_frame)
        self.btn_sc_exp.setObjectName("ExportSceneButton")
        self.btn_sc_exp.clicked.connect(self._exp_sc)
        
        for btn in [self.btn_sc_jump, self.btn_sc_del, self.btn_sc_exp]:
            btn.setObjectName("SceneActionButton")
            btn.setCursor(Qt.PointingHandCursor)
            sc_btn_layout.addWidget(btn)
            
        sc_layout.addWidget(self.sc_lb)
        sc_layout.addLayout(sc_btn_layout)
        layout.addWidget(self.sc_label_frame)
        
        self.detail_frame = QGroupBox(" Detail Adegan & Subtitel ", self)
        self.detail_frame.setObjectName("DetailFrame")
        self.detail_frame.setFixedHeight(120)
        det_layout = QVBoxLayout(self.detail_frame)
        det_layout.setContentsMargins(6, 6, 6, 6)
        
        self.txt_detail = QTextEdit(self.detail_frame)
        self.txt_detail.setObjectName("DetailText")
        self.txt_detail.setReadOnly(True)
        self.txt_detail.setPlainText("Pilih adegan di atas untuk melihat detail...")
        
        det_layout.addWidget(self.txt_detail)
        layout.addWidget(self.detail_frame)
        
    def _apply_stylesheet(self):
        qss = """
        #SceneListDialog {
            background-color: #0d0d1a;
        }
        #SceneFrame, #DetailFrame {
            color: #a8dadc;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
            border: 1px solid #1f4068;
            border-radius: 6px;
        }
        #SceneList {
            background-color: #050510;
            color: #e0e0ff;
            border: 1px solid #1f4068;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }
        #SceneList::item:hover {
            background-color: #16213e;
        }
        #SceneList::item:selected {
            background-color: #e94560;
            color: white;
        }
        #SceneActionButton {
            background-color: #16213e;
            color: white;
            border: none;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
            padding: 5px 12px;
            font-weight: bold;
        }
        #SceneActionButton:hover {
            background-color: #243b6b;
        }
        #DeleteSceneButton {
            background-color: #5c1a1a;
        }
        #DeleteSceneButton:hover {
            background-color: #7c2222;
        }
        #ExportSceneButton {
            background-color: #1e5f3a;
        }
        #ExportSceneButton:hover {
            background-color: #2a7f50;
        }
        #DetailText {
            background-color: #050510;
            color: #8888aa;
            border: 1px solid #1f4068;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-size: 11px;
        }
        """
        self.setStyleSheet(qss)
        
    def load_scenes(self):
        self.sc_lb.clear()
        self.txt_detail.setPlainText("Pilih adegan di atas untuk melihat detail...")
        
        for idx, (s, e, label, subs) in enumerate(self.player.scenes):
            dur = e - s
            disp = f"{label}: {format_time(s)} -> {format_time(e)} ({dur:.2f}s)"
            self.sc_lb.addItem(disp)
            
    def _on_sc_select(self):
        selected = self.sc_lb.currentRow()
        if selected < 0 or selected >= len(self.player.scenes):
            return
            
        s_start, s_end, label, subs = self.player.scenes[selected]
        self.txt_detail.clear()
        if subs:
            self.txt_detail.setPlainText(f"Adegan: {label}\n{subs}")
        else:
            self.txt_detail.setPlainText(f"Adegan: {label}\n(Tidak ada subtitel/dialog terekam)")
            
    def _jump_sc(self):
        selected = self.sc_lb.currentRow()
        if selected >= 0 and selected < len(self.player.scenes):
            s_start, _, _, _ = self.player.scenes[selected]
            self.player.engine.seek_to(int(s_start * self.player.engine.fps))
            self.player._update_time_slider()
            self.player.render_current_frame()
            
    def _del_sc(self):
        selected = self.sc_lb.currentRow()
        if selected >= 0 and selected < len(self.player.scenes):
            reply = QMessageBox.question(self, "Konfirmasi", 
                                         "Hapus catatan adegan terpilih?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.player.scenes.pop(selected)
                
                from vidstamp.utils.file_manager import save_scenes_data
                save_scenes_data(self.player.engine.video_path, self.player.scenes)
                self.player._auto_export_scenes()
                
                self.load_scenes()
                self.player.lbl_status_bar_update("Adegan dihapus.")
                
    def _exp_sc(self):
        selected = self.sc_lb.currentRow()
        if selected >= 0 and selected < len(self.player.scenes):
            s_start, s_end, label, _ = self.player.scenes[selected]
            fn, _ = QFileDialog.getSaveFileName(self, "Export Potongan Adegan Video", 
                                                os.path.dirname(self.player.engine.video_path), 
                                                "Video MP4 (*.mp4)")
            if fn:
                self.player.lbl_status_bar_update("Mengekspor potongan adegan via FFmpeg... Mohon tunggu.")
                import threading
                from vidstamp.core.exporter import cut_video_single
                def run_cut():
                    success, msg = cut_video_single(self.player.engine.video_path, s_start, s_end, fn)
                    if success:
                        self.player.lbl_status_bar_update("Ekspor adegan sukses!")
                    else:
                        self.player.lbl_status_bar_update(f"Ekspor adegan gagal: {msg}")
                threading.Thread(target=run_cut, daemon=True).start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.render_current_frame()
