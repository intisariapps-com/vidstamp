"""
vidstamp/ui/extractor_tool.py - Jendela Perkakas Ekstraktor Subtitle & Audio (MP3/SRT) menggunakan PySide6
"""
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QRadioButton, QButtonGroup, 
                             QProgressBar, QFileDialog, QMessageBox, QApplication, QWidget)
from PySide6.QtCore import Qt, QThread, Signal
from vidstamp.core.subtitle import extract_mkv_subtitles, extract_audio_from_video

class ExtractorWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, mode, in_path, out_path):
        super().__init__()
        self.mode = mode
        self.in_path = in_path
        self.out_path = out_path

    def run(self):
        try:
            if self.mode == "sub":
                success = extract_mkv_subtitles(self.in_path, self.out_path)
                msg = "Sukses mengekstrak subtitle internal!" if success else "Gagal mengekstrak subtitle. Pastikan video MKV memiliki trek teks."
            else:
                success, err_msg = extract_audio_from_video(self.in_path, self.out_path)
                msg = "Sukses mengekstrak audio track!" if success else f"Gagal mengekstrak audio:\n{err_msg}"
            self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, f"Terjadi kesalahan internal:\n{e}")

class AudioSubExtractorWizard(QDialog):
    def __init__(self, parent=None, initial_dir=None):
        super().__init__(parent)
        self.setWindowTitle("Ekstraktor Subtitle & Audio")
        self.setFixedSize(600, 420)
        
        self.initial_dir = initial_dir or os.path.expanduser("~")
        self.processing = False
        self.worker = None
        
        self._build_ui()
        self._apply_stylesheet()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Header
        header_widget = QWidget(self)
        header_widget.setObjectName("HeaderWidget")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 12, 15, 12)
        
        lbl_title = QLabel("⚙️ Ekstraktor Subtitle & Audio", header_widget)
        lbl_title.setObjectName("HeaderTitle")
        
        lbl_subtitle = QLabel("Ekstrak subtitle internal MKV atau ambil audio video untuk persiapan transkripsi.", header_widget)
        lbl_subtitle.setObjectName("HeaderSubtitle")
        
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_subtitle)
        main_layout.addWidget(header_widget)
        
        # 2. Body Container
        body_widget = QWidget(self)
        body_widget.setObjectName("BodyWidget")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(20, 20, 20, 20)
        body_layout.setSpacing(12)
        
        # Input Video File
        lbl_in = QLabel("Pilih Berkas Video input (MKV / MP4):", body_widget)
        lbl_in.setObjectName("SectionTitle")
        body_layout.addWidget(lbl_in)
        
        in_layout = QHBoxLayout()
        self.txt_input = QLineEdit(body_widget)
        self.txt_input.setObjectName("PathInput")
        self.txt_input.textChanged.connect(self._on_input_changed)
        
        btn_browse_in = QPushButton("Pilih Berkas", body_widget)
        btn_browse_in.setObjectName("BrowseButton")
        btn_browse_in.setCursor(Qt.PointingHandCursor)
        btn_browse_in.clicked.connect(self._browse_input)
        
        in_layout.addWidget(self.txt_input)
        in_layout.addWidget(btn_browse_in)
        body_layout.addLayout(in_layout)
        
        # Mode Ekstraksi
        lbl_mode = QLabel("Pilih Jenis Ekstraksi:", body_widget)
        lbl_mode.setObjectName("SectionTitle")
        body_layout.addWidget(lbl_mode)
        
        self.btn_group = QButtonGroup(body_widget)
        
        self.rb_sub = QRadioButton("Ekstrak Subtitle Internal ke .srt (Hanya berkas MKV)", body_widget)
        self.rb_sub.setObjectName("ModeRadio")
        self.rb_sub.setChecked(True)
        self.rb_sub.toggled.connect(self._on_mode_changed)
        self.btn_group.addButton(self.rb_sub)
        body_layout.addWidget(self.rb_sub)
        
        self.rb_audio = QRadioButton("Ekstrak Audio Track ke .mp3 (Mendukung MKV & MP4)", body_widget)
        self.rb_audio.setObjectName("ModeRadio")
        self.rb_audio.toggled.connect(self._on_mode_changed)
        self.btn_group.addButton(self.rb_audio)
        body_layout.addWidget(self.rb_audio)
        
        # Output Target File
        lbl_out = QLabel("Pilih Berkas Output hasil:", body_widget)
        lbl_out.setObjectName("SectionTitle")
        body_layout.addWidget(lbl_out)
        
        out_layout = QHBoxLayout()
        self.txt_output = QLineEdit(body_widget)
        self.txt_output.setObjectName("PathInput")
        
        btn_browse_out = QPushButton("Browse...", body_widget)
        btn_browse_out.setObjectName("BrowseButton")
        btn_browse_out.setCursor(Qt.PointingHandCursor)
        btn_browse_out.clicked.connect(self._browse_output)
        
        out_layout.addWidget(self.txt_output)
        out_layout.addWidget(btn_browse_out)
        body_layout.addLayout(out_layout)
        
        # Progress Indicator
        self.lbl_status = QLabel("Silakan pilih input berkas video.", body_widget)
        self.lbl_status.setObjectName("StatusLabel")
        body_layout.addWidget(self.lbl_status)
        
        self.progress_bar = QProgressBar(body_widget)
        self.progress_bar.setObjectName("ProgressBar")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0) # Indeterminate mode by default
        self.progress_bar.hide()
        body_layout.addWidget(self.progress_bar)
        
        # Bottom Buttons
        bottom_layout = QHBoxLayout()
        
        self.btn_cancel = QPushButton("Batal", body_widget)
        self.btn_cancel.setObjectName("CancelButton")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.close)
        
        self.btn_start = QPushButton("Mulai Ekstraksi", body_widget)
        self.btn_start.setObjectName("StartButton")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self._start_extraction)
        
        bottom_layout.addWidget(self.btn_cancel)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_start)
        body_layout.addLayout(bottom_layout)
        
        main_layout.addWidget(body_widget)

    def _apply_stylesheet(self):
        qss = """
        QDialog {
            background-color: #0d0d1a;
        }
        #HeaderWidget {
            background-color: #16213e;
            border-bottom: 2px solid #1f4068;
        }
        #HeaderTitle {
            color: #a8dadc;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
            font-weight: bold;
        }
        #HeaderSubtitle {
            color: #8888aa;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
        }
        #BodyWidget {
            background-color: #0d0d1a;
        }
        #SectionTitle {
            color: #a8dadc;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
        }
        #PathInput {
            background-color: #16213e;
            color: white;
            border: 1px solid #1f4068;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            padding: 4px;
        }
        #BrowseButton {
            background-color: #1a1a3e;
            color: #7ec8e3;
            border: none;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
            padding: 5px 12px;
        }
        #BrowseButton:hover {
            background-color: #e94560;
            color: white;
        }
        #ModeRadio {
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }
        #StatusLabel {
            color: #8888aa;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
        }
        #ProgressBar {
            height: 12px;
            border: 1px solid #1e5f3a;
            border-radius: 4px;
            background-color: #0d0d1a;
        }
        #ProgressBar::chunk {
            background-color: #1e5f3a;
        }
        #CancelButton {
            background-color: #333333;
            color: white;
            border: none;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
            font-weight: bold;
            padding: 6px 18px;
        }
        #CancelButton:hover {
            background-color: #444444;
        }
        #StartButton {
            background-color: #1e5f3a;
            color: white;
            border: none;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
            font-weight: bold;
            padding: 6px 20px;
        }
        #StartButton:hover {
            background-color: #2a7f50;
        }
        """
        self.setStyleSheet(qss)

    def _browse_input(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Pilih Berkas Video", self.initial_dir,
                                            "Video (MKV/MP4) (*.mkv *.mp4);;Semua Berkas (*.*)")
        if fn:
            self.txt_input.setText(fn)

    def _browse_output(self):
        mode = "sub" if self.rb_sub.isChecked() else "audio"
        types = "Subtitle SRT (*.srt)" if mode == "sub" else "Audio MP3 (*.mp3)"
        
        in_path = self.txt_input.text()
        init_file = self.txt_output.text()
        init_dir = os.path.dirname(in_path) or self.initial_dir
        
        fn, _ = QFileDialog.getSaveFileName(self, "Simpan File Hasil", init_dir, types)
        if fn:
            self.txt_output.setText(fn)

    def _on_input_changed(self, text):
        if not text or not os.path.exists(text):
            return
            
        base, ext = os.path.splitext(text)
        
        if ext.lower() == ".mp4":
            self.rb_sub.setEnabled(False)
            self.rb_audio.setChecked(True)
            self.txt_output.setText(base + ".mp3")
        else:
            self.rb_sub.setEnabled(True)
            if self.rb_sub.isChecked():
                self.txt_output.setText(base + ".srt")
            else:
                self.txt_output.setText(base + ".mp3")
                
        self.lbl_status.setText("Siap untuk diekstrak.")

    def _on_mode_changed(self):
        in_path = self.txt_input.text()
        if not in_path:
            return
        base, _ = os.path.splitext(in_path)
        if self.rb_sub.isChecked():
            self.txt_output.setText(base + ".srt")
        else:
            self.txt_output.setText(base + ".mp3")

    def _start_extraction(self):
        if self.processing:
            return
            
        in_path = self.txt_input.text()
        out_path = self.txt_output.text()
        mode = "sub" if self.rb_sub.isChecked() else "audio"
        
        if not in_path or not os.path.exists(in_path):
            QMessageBox.critical(self, "Error", "Berkas video input tidak valid!")
            return
        if not out_path:
            QMessageBox.critical(self, "Error", "Tentukan lokasi berkas output!")
            return
            
        self.processing = True
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.show()
        self.lbl_status.setText("Sedang mengekstrak berkas via FFmpeg... Mohon tunggu.")
        
        # Luncurkan QThread asinkron
        self.worker = ExtractorWorker(mode, in_path, out_path)
        self.worker.finished.connect(self._extraction_complete)
        self.worker.start()

    def _extraction_complete(self, success, message):
        self.processing = False
        self.progress_bar.hide()
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.lbl_status.setText("Proses selesai.")
        
        if success:
            QMessageBox.information(self, "Sukses", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Gagal", message)
