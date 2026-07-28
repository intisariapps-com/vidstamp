"""
vidstamp/ui/player_view.py - Komponen UI Panel Kontrol Pendamping MPC-HC berbasis PySide6
"""
import os
import re
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QComboBox, QLineEdit, 
                             QMessageBox, QFileDialog, QApplication, QSizePolicy, QCheckBox)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QKeyEvent

from vidstamp.core.mpc_client import MPCClient
from vidstamp.core.subtitle import parse_srt_file
from vidstamp.utils.time_formatter import format_time, format_remaining

class PlayerView(QWidget):
    def __init__(self, parent=None, on_video_loaded_callback=None):
        super().__init__(parent)
        self.client = MPCClient()
        self.on_video_loaded = on_video_loaded_callback
        
        self.video_path = ""
        self.fps = 23.976 # fallback default
        self.total_duration_sec = 0.0
        self.cur_sec = 0.0
        self.subtitle_list = []
        self.scenes = []
        
        self.mark_start = None
        self.mark_end = None
        self._seeking = False
        
        self._build_ui()
        self._apply_stylesheet()
        
        # Timer Sinkronisasi Status MPC-HC (setiap 200ms)
        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(200)
        self.sync_timer.timeout.connect(self.sync_with_mpc)
        self.sync_timer.start()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # 1. Status Koneksi & Informasi File Aktif
        self.info_frame = QWidget(self)
        self.info_frame.setObjectName("InfoFrame")
        info_layout = QVBoxLayout(self.info_frame)
        info_layout.setContentsMargins(10, 8, 10, 8)
        
        self.lbl_connection = QLabel("🔌 Status: Mencari koneksi ke MPC-HC...", self.info_frame)
        self.lbl_connection.setObjectName("ConnectionLabel")
        
        self.lbl_title = QLabel("📽️ File: (Tidak ada video terdeteksi di MPC-HC)", self.info_frame)
        self.lbl_title.setObjectName("VideoTitle")
        self.lbl_title.setWordWrap(True)
        
        info_layout.addWidget(self.lbl_connection)
        info_layout.addWidget(self.lbl_title)
        self.main_layout.addWidget(self.info_frame)
        
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
        
        # 3. Control Panel (Navigasi & Marker)
        self.ctrl_panel = QWidget(self)
        ctrl_layout = QHBoxLayout(self.ctrl_panel)
        ctrl_layout.setContentsMargins(5, 0, 5, 0)
        ctrl_layout.setSpacing(8)
        
        btn_rew10 = QPushButton("-10s", self.ctrl_panel)
        btn_rew10.clicked.connect(lambda: self.client.jump_backward(10))
        btn_rew1 = QPushButton("-5s", self.ctrl_panel)
        btn_rew1.clicked.connect(lambda: self.client.jump_backward(5))
        
        self.btn_play = QPushButton("Play / Pause", self.ctrl_panel)
        self.btn_play.setObjectName("PlayButton")
        self.btn_play.clicked.connect(self.client.toggle_play)
        
        btn_ff1 = QPushButton("+5s", self.ctrl_panel)
        btn_ff1.clicked.connect(lambda: self.client.jump_forward(5))
        btn_ff10 = QPushButton("+10s", self.ctrl_panel)
        btn_ff10.clicked.connect(lambda: self.client.jump_forward(10))
        
        # Marker Buttons
        self.btn_start = QPushButton("[M] Start", self.ctrl_panel)
        self.btn_start.setObjectName("StartMarker")
        self.btn_start.clicked.connect(self._mark_start_fn)
        
        self.btn_end = QPushButton("[N] End", self.ctrl_panel)
        self.btn_end.setObjectName("EndMarker")
        self.btn_end.clicked.connect(self._mark_end_fn)
        
        for btn in [btn_rew10, btn_rew1, btn_ff1, btn_ff10]:
            btn.setObjectName("NavButton")
            btn.setCursor(Qt.PointingHandCursor)
            
        ctrl_layout.addWidget(btn_rew10)
        ctrl_layout.addWidget(btn_rew1)
        ctrl_layout.addWidget(self.btn_play)
        ctrl_layout.addWidget(btn_ff1)
        ctrl_layout.addWidget(btn_ff10)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_end)
        self.main_layout.addWidget(self.ctrl_panel)
        
        # 4. Info Bar Status
        self.inf_bar = QLabel("Space = Play/Pause di MPC-HC | M = Mark Start | N = Mark End | Ctrl+L = Daftar Adegan", self)
        self.inf_bar.setObjectName("InfoBar")
        self.inf_bar.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.inf_bar)

    def _apply_stylesheet(self):
        qss = """
        #InfoFrame {
            background-color: #16213e;
            border: 1px solid #1f4068;
            border-radius: 6px;
        }
        #ConnectionLabel {
            color: #ffde59;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
        }
        #VideoTitle {
            color: #e0e0ff;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
            font-weight: bold;
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
            padding: 5px 10px;
        }
        #NavButton:hover {
            background-color: #1a1a3e;
        }
        #StartMarker {
            background-color: #1a4a6e;
            color: white;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: bold;
            padding: 5px 14px;
            border-radius: 4px;
        }
        #EndMarker {
            background-color: #5c1a1a;
            color: white;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: bold;
            padding: 5px 14px;
            border-radius: 4px;
        }
        #InfoBar {
            color: #555577;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
        }
        """
        self.setStyleSheet(qss)

    def sync_with_mpc(self):
        """Membaca status pemutaran secara real-time dari MPC-HC via client HTTP."""
        status = self.client.get_variables()
        if not status["active"]:
            self.lbl_connection.setText("❌ Status: Terputus dari MPC-HC (Aktifkan Web Interface port 13579!)")
            self.lbl_connection.setStyleSheet("color: #ff5e7e;")
            return
            
        self.lbl_connection.setText("🟢 Status: Terhubung ke MPC-HC")
        self.lbl_connection.setStyleSheet("color: #2a7f50;")
        
        # Deteksi perubahan file video yang sedang diputar di MPC-HC
        active_filepath = status["filepath"]
        if active_filepath and active_filepath != self.video_path:
            self.load_video(active_filepath)
            
        self.cur_sec = status["position_sec"]
        self.total_duration_sec = status["duration_sec"]
        
        # Update Slider & Label Waktu jika user tidak sedang menggeser slider
        if not self._seeking:
            if self.total_duration_sec > 0:
                self.slider.setRange(0, int(self.total_duration_sec))
                self.slider.setValue(int(self.cur_sec))
            self.lbl_time_cur.setText(format_time(self.cur_sec))
            self.lbl_time_total.setText(format_time(self.total_duration_sec))
            
        # Update text tombol Play/Pause berdasarkan status state MPC-HC
        if status["state"] == 2:
            self.btn_play.setText("Pause")
            self.btn_play.setStyleSheet("background-color: #e94560;")
        else:
            self.btn_play.setText("Play")
            self.btn_play.setStyleSheet("background-color: #1e5f3a;")

    def load_video(self, path):
        if not path or not os.path.exists(path):
            return
            
        self.video_path = path
        self.lbl_title.setText(f"📽️ File: {os.path.basename(path)}")
        
        # Deteksi FPS dasar (soft fallback)
        self.fps = 23.976
        
        # Load Subtitle lokal secara background untuk analisis catatan adegan
        self.subtitle_list = []
        ext_srt = os.path.splitext(path)[0] + ".srt"
        if not os.path.exists(ext_srt):
            ext_srt = os.path.splitext(path)[0] + "_clean.srt"
            
        if os.path.exists(ext_srt):
            self.subtitle_list = parse_srt_file(ext_srt)
            self.lbl_status_bar_update("Memuat subtitle eksternal SRT secara background.")
        else:
            self.lbl_status_bar_update("Video dimuat tanpa subtitel background.")
            
        self.load_saved_scenes()
        
        if self.on_video_loaded:
            self.on_video_loaded(path)

    def load_saved_scenes(self):
        self.scenes = []
        if not self.video_path:
            return
            
        from vidstamp.utils.file_manager import load_scenes_data
        saved = load_scenes_data(self.video_path)
        for item in saved:
            s = item.get("start", 0.0)
            e = item.get("end", 0.0)
            label = item.get("label", "")
            subs = item.get("subtitles", "")
            self.scenes.append((s, e, label, subs))

    def _mark_start_fn(self):
        if not self.video_path:
            return
        self.mark_start = self.cur_sec
        self.btn_start.setText(f"S: {format_time(self.mark_start)}")
        self.lbl_status_bar_update("Batas START terkatat. Klik [N] End untuk mengunci adegan.")

    def _mark_end_fn(self):
        if not self.video_path or self.mark_start is None:
            return
        self.mark_end = self.cur_sec
        self.btn_end.setText(f"E: {format_time(self.mark_end)}")
        
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
            save_scenes_data(self.video_path, self.scenes)
            self._auto_export_scenes()
            
            self.load_saved_scenes()
            self.lbl_status_bar_update(f"Adegan '{label}' berhasil disimpan.")
            
            self.mark_start = None
            self.mark_end = None
            self.btn_start.setText("[M] Start")
            self.btn_end.setText("[N] End")

    def _auto_export_scenes(self):
        if not self.video_path:
            return
        try:
            from vidstamp.utils.file_manager import ensure_note_folder
            note_dir = ensure_note_folder(self.video_path)
            video_name = os.path.basename(self.video_path)
            video_base, _ = os.path.splitext(video_name)
            default_file = os.path.join(note_dir, f"{video_base}_catatan_adegan.txt")
            
            with open(default_file, "w", encoding="utf-8") as f:
                f.write(f"=== CATATAN ADEGAN VIDEO ===\n")
                f.write(f"Video Asli: {os.path.abspath(self.video_path)}\n")
                f.write(f"Total Adegan Tercatat: {len(self.scenes)}\n\n")
                
                for idx, (s, e, label, subs) in enumerate(self.scenes):
                    dur = e - s
                    f.write(f"{idx+1}. [{format_time(s)} -> {format_time(e)}] ({dur:.2f}s) - {label}\n")
                    if subs:
                        f.write(f"--- Dialog Tercatat ---\n{subs}\n")
                    f.write("="*40 + "\n")
        except Exception as err:
            print(f"Gagal melakukan ekspor otomatis catatan: {err}")

    def open_scenes_dialog(self):
        if not self.video_path:
            QMessageBox.critical(self, "Pemberitahuan", "Silakan buka video di MPC-HC terlebih dahulu.")
            return
        dialog = SceneListDialog(self)
        dialog.exec()

    def lbl_status_bar_update(self, text):
        self.inf_bar.setText(text)

    def _on_slider_pressed(self):
        self._seeking = True

    def _on_slider_released(self):
        self._seeking = False
        # Kirim perintah seek ke MPC-HC setelah slider dilepas
        self.client.seek_to_seconds(self.slider.value())

    def _on_slider_moved(self, val):
        self.lbl_time_cur.setText(format_time(val))

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
            self.player.client.seek_to_seconds(s_start)
            self.player._update_time_slider()
            
    def _del_sc(self):
        selected = self.sc_lb.currentRow()
        if selected >= 0 and selected < len(self.player.scenes):
            reply = QMessageBox.question(self, "Konfirmasi", 
                                         "Hapus catatan adegan terpilih?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.player.scenes.pop(selected)
                
                from vidstamp.utils.file_manager import save_scenes_data
                save_scenes_data(self.player.video_path, self.player.scenes)
                self.player._auto_export_scenes()
                
                self.load_scenes()
                self.player.lbl_status_bar_update("Adegan dihapus.")
                
    def _exp_sc(self):
        selected = self.sc_lb.currentRow()
        if selected >= 0 and selected < len(self.player.scenes):
            s_start, s_end, label, _ = self.player.scenes[selected]
            fn, _ = QFileDialog.getSaveFileName(self, "Export Potongan Adegan Video", 
                                                os.path.dirname(self.player.video_path), 
                                                "Video MP4 (*.mp4)")
            if fn:
                self.player.lbl_status_bar_update("Mengekspor potongan adegan via FFmpeg... Mohon tunggu.")
                import threading
                from vidstamp.core.exporter import cut_video_single
                def run_cut():
                    success, msg = cut_video_single(self.player.video_path, s_start, s_end, fn)
                    if success:
                        self.player.lbl_status_bar_update("Ekspor adegan sukses!")
                    else:
                        self.player.lbl_status_bar_update(f"Ekspor adegan gagal: {msg}")
                threading.Thread(target=run_cut, daemon=True).start()
