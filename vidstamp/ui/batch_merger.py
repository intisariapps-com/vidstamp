"""
vidstamp/ui/batch_merger.py - Jendela Wizard Pemrosesan & Penggabungan Video Massal (Bulk) menggunakan PySide6
"""
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QRadioButton, QButtonGroup, QCheckBox, 
                             QSlider, QLineEdit, QTableWidget, QTableWidgetItem, 
                             QProgressBar, QFileDialog, QMessageBox, QWidget, QApplication)
from PySide6.QtCore import Qt, QThread, Signal
from vidstamp.config import VIDEO_EXTS
from vidstamp.utils.time_formatter import format_time
from vidstamp.utils.file_manager import load_skip_config
from vidstamp.core.exporter import get_video_duration, get_mkv_chapters, export_bulk_and_merge
from vidstamp.core.subtitle import find_external_subtitle

class FolderScannerWorker(QThread):
    progress = Signal(int, str)
    item_scanned = Signal(str, dict)
    finished = Signal()

    def __init__(self, parent_dir):
        super().__init__()
        self.parent_dir = parent_dir

    def run(self):
        try:
            video_files = sorted([
                os.path.join(self.parent_dir, f) for f in os.listdir(self.parent_dir)
                if os.path.splitext(f)[1].lower() in VIDEO_EXTS and "_clean" not in f.lower()
            ], key=str.lower)
        except Exception as e:
            self.progress.emit(0, f"Gagal membaca direktori: {e}")
            self.finished.emit()
            return

        if not video_files:
            self.progress.emit(0, "Tidak ditemukan berkas video di folder.")
            self.finished.emit()
            return

        total = len(video_files)
        for idx, file_path in enumerate(video_files):
            basename = os.path.basename(file_path)
            self.progress.emit(10 + int((idx / total) * 80), f"Menganalisis [{idx+1}/{total}] {basename}...")
            
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
                
            data = {
                "filename": basename,
                "duration": duration,
                "subtitle": sub_status,
                "op_text": op_text,
                "ed_text": ed_text
            }
            self.item_scanned.emit(file_path, data)

        self.progress.emit(100, "Siap memproses.")
        self.finished.emit()

class MergeWorker(QThread):
    progress = Signal(int, float, str) # file_idx, pct, status_text
    finished = Signal(bool, str)

    def __init__(self, parent_dir, mode, merge, ocr_tolerance, cancel_event):
        super().__init__()
        self.parent_dir = parent_dir
        self.mode = mode
        self.merge = merge
        self.ocr_tolerance = ocr_tolerance
        self.cancel_event = cancel_event

    def run(self):
        # Inject parameter OCR tolerance ke dalam exporter module
        import vidstamp.core.exporter as core_exporter
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
                if norm_curr == norm_next and gap <= self.ocr_tolerance:
                    current['end'] = max(current['end'], next_sub['end'])
                else:
                    merged.append(current)
                    current = next_sub.copy()
            merged.append(current)
            return merged
            
        core_exporter.merge_duplicate_ocr_subtitles = patched_merge
        
        def progress_callback(file_idx, total, pct, status_text):
            self.progress.emit(file_idx, pct, status_text)
            
        try:
            success, msg = export_bulk_and_merge(
                self.parent_dir, mode=self.mode, merge_to_one=self.merge,
                progress_callback=progress_callback, cancel_event=self.cancel_event
            )
            core_exporter.merge_duplicate_ocr_subtitles = original_merge_logic
            self.finished.emit(success, msg)
        except Exception as ex:
            core_exporter.merge_duplicate_ocr_subtitles = original_merge_logic
            self.finished.emit(False, f"Terjadi kesalahan internal: {ex}")

class BatchMergerWizard(QDialog):
    def __init__(self, parent=None, current_dir=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Merger & Skip Config Wizard")
        self.resize(850, 680)
        self.setMinimumSize(800, 550)
        
        self.parent_dir = current_dir
        self.processing = False
        import threading
        self.cancel_event = threading.Event()
        
        self.video_files = []
        self.video_data = {}
        
        self._build_ui()
        self._apply_stylesheet()
        
        # Mulai load data file di background
        self._scanner = FolderScannerWorker(self.parent_dir)
        self._scanner.progress.connect(self._on_scan_progress)
        self._scanner.item_scanned.connect(self._on_item_scanned)
        self._scanner.finished.connect(self._on_scan_finished)
        self._scanner.start()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Header
        header_widget = QWidget(self)
        header_widget.setObjectName("HeaderWidget")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 12, 15, 12)
        
        lbl_title = QLabel("🎛️ Batch Merger & Skip Config Wizard", header_widget)
        lbl_title.setObjectName("HeaderTitle")
        
        self.lbl_folder = QLabel(f"Folder Aktif: {self.parent_dir}", header_widget)
        self.lbl_folder.setObjectName("HeaderSubtitle")
        
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(self.lbl_folder)
        main_layout.addWidget(header_widget)
        
        # Body Container
        body_widget = QWidget(self)
        body_widget.setObjectName("BodyWidget")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(15, 15, 15, 15)
        body_layout.setSpacing(10)
        
        # Table Video List
        lbl_queue = QLabel("Antrean Episode Video:", body_widget)
        lbl_queue.setObjectName("SectionTitle")
        body_layout.addWidget(lbl_queue)
        
        self.table = QTableWidget(body_widget)
        self.table.setObjectName("QueueTable")
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Episode / Nama Berkas", "Durasi", "Subtitel", 
            "Batas Skip Opening (OP)", "Batas Skip Ending (ED)"
        ])
        # Auto stretch kolom pertama
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setDefaultSectionSize(130)
        self.table.setColumnWidth(0, 260)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 140)
        body_layout.addWidget(self.table)
        
        # Options Frame
        opts_widget = QWidget(body_widget)
        opts_widget.setObjectName("OptionsPanel")
        opts_layout = QVBoxLayout(opts_widget)
        opts_layout.setContentsMargins(15, 12, 15, 12)
        opts_layout.setSpacing(10)
        
        # Subtitle Mode Choice
        sub_layout = QHBoxLayout()
        lbl_sub = QLabel("Mode Subtitle:", opts_widget)
        lbl_sub.setObjectName("OptionLabel")
        
        self.rb_soft = QRadioButton("Softsub (Ekspor .srt terpisah)", opts_widget)
        self.rb_soft.setObjectName("OptionRadio")
        self.rb_soft.setChecked(True)
        
        self.rb_hard = QRadioButton("Hardsub (Render teks ke video)", opts_widget)
        self.rb_hard.setObjectName("OptionRadio")
        
        self.sub_group = QButtonGroup(opts_widget)
        self.sub_group.addButton(self.rb_soft)
        self.sub_group.addButton(self.rb_hard)
        
        sub_layout.addWidget(lbl_sub)
        sub_layout.addWidget(self.rb_soft)
        sub_layout.addWidget(self.rb_hard)
        sub_layout.addStretch()
        opts_layout.addLayout(sub_layout)
        
        # Concat Checkbox
        merge_layout = QHBoxLayout()
        lbl_merge = QLabel("Penggabungan:", opts_widget)
        lbl_merge.setObjectName("OptionLabel")
        
        self.cb_merge = QCheckBox("Satukan semua hasil bulk menjadi 1 file utama (.mp4 & .srt)", opts_widget)
        self.cb_merge.setObjectName("OptionCheckbox")
        self.cb_merge.setChecked(True)
        
        merge_layout.addWidget(lbl_merge)
        merge_layout.addWidget(self.cb_merge)
        merge_layout.addStretch()
        opts_layout.addLayout(merge_layout)
        
        # OCR Tolerance
        ocr_layout = QHBoxLayout()
        lbl_ocr = QLabel("Toleransi OCR:", opts_widget)
        lbl_ocr.setObjectName("OptionLabel")
        
        self.ocr_slider = QSlider(Qt.Horizontal, opts_widget)
        self.ocr_slider.setObjectName("OcrSlider")
        self.ocr_slider.setRange(5, 50) # 0.5s ke 5.0s (skala 10)
        self.ocr_slider.setValue(20) # default 2.0s
        self.ocr_slider.setFixedWidth(150)
        self.ocr_slider.valueChanged.connect(self._on_ocr_slider_changed)
        
        self.lbl_ocr_val = QLabel("2.0 detik", opts_widget)
        self.lbl_ocr_val.setObjectName("OcrValLabel")
        
        ocr_layout.addWidget(lbl_ocr)
        ocr_layout.addWidget(self.ocr_slider)
        ocr_layout.addWidget(self.lbl_ocr_val)
        ocr_layout.addStretch()
        opts_layout.addLayout(ocr_layout)
        
        # Output Concat Name
        out_layout = QHBoxLayout()
        lbl_out = QLabel("File Gabungan:", opts_widget)
        lbl_out.setObjectName("OptionLabel")
        
        self.txt_output = QLineEdit(opts_widget)
        self.txt_output.setObjectName("OutputInput")
        folder_basename = os.path.basename(self.parent_dir.rstrip(r"\/"))
        self.txt_output.setText(os.path.join(self.parent_dir, f"{folder_basename}_clean.mp4"))
        
        btn_browse_out = QPushButton("Telusuri...", opts_widget)
        btn_browse_out.setObjectName("BrowseButton")
        btn_browse_out.setCursor(Qt.PointingHandCursor)
        btn_browse_out.clicked.connect(self._browse_output_file)
        
        out_layout.addWidget(lbl_out)
        out_layout.addWidget(self.txt_output)
        out_layout.addWidget(btn_browse_out)
        opts_layout.addLayout(out_layout)
        
        body_layout.addWidget(opts_widget)
        
        # Progress & Status Display
        self.lbl_status_text = QLabel("Menunggu inisialisasi berkas...", body_widget)
        self.lbl_status_text.setObjectName("StatusLabel")
        body_layout.addWidget(self.lbl_status_text)
        
        self.progress_bar = QProgressBar(body_widget)
        self.progress_bar.setObjectName("ProgressBar")
        self.progress_bar.setValue(0)
        body_layout.addWidget(self.progress_bar)
        
        # Bottom Buttons
        bottom_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Batal / Keluar", body_widget)
        self.btn_cancel.setObjectName("CancelButton")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self._on_cancel)
        
        self.btn_start = QPushButton("Mulai Proses Massal", body_widget)
        self.btn_start.setObjectName("StartButton")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self._start_processing)
        
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
        #QueueTable {
            background-color: #0d0d1a;
            color: #e0e0ff;
            border: 1px solid #1f4068;
            gridline-color: #1a1a3e;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
        }
        QHeaderView::section {
            background-color: #16213e;
            color: #a8dadc;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
            font-weight: bold;
            border: 1px solid #1f4068;
            padding: 4px;
        }
        #OptionsPanel {
            background-color: #0b0b18;
            border: 1px solid #1f4068;
            border-radius: 6px;
        }
        #OptionLabel {
            color: white;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
            min-width: 90px;
        }
        #OptionRadio, #OptionCheckbox {
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }
        #OptionCheckbox {
            color: #ffd700;
            font-weight: bold;
        }
        #OcrValLabel {
            color: #8888aa;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
        }
        #OutputInput {
            background-color: #16213e;
            color: white;
            border: 1px solid #1f4068;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-size: 10px;
            padding: 3px 6px;
        }
        #BrowseButton {
            background-color: #1a1a3e;
            color: #7ec8e3;
            border: none;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
            font-weight: bold;
            padding: 4px 10px;
        }
        #BrowseButton:hover {
            background-color: #e94560;
            color: white;
        }
        #StatusLabel {
            color: #8888aa;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }
        #ProgressBar {
            height: 12px;
            border: 1px solid #1e5f3a;
            border-radius: 4px;
            background-color: #0d0d1a;
            text-align: center;
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
            padding: 6px 22px;
        }
        #StartButton:hover {
            background-color: #2a7f50;
        }
        #StartButton:disabled {
            background-color: #223c2a;
            color: #668877;
        }
        """
        self.setStyleSheet(qss)

    def _browse_output_file(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Simpan File Gabungan", self.parent_dir, "Video MP4 (*.mp4)")
        if fn:
            self.txt_output.setText(fn)

    def _on_ocr_slider_changed(self, val):
        self.lbl_ocr_val.setText(f"{val/10.0:.1f} detik")

    def _on_scan_progress(self, percent, text):
        self.progress_bar.setValue(percent)
        self.lbl_status_text.setText(text)

    def _on_item_scanned(self, file_path, data):
        self.video_files.append(file_path)
        self.video_data[file_path] = data
        
        # Sisipkan baris ke QTableWidget
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(data["filename"]))
        self.table.setItem(row, 1, QTableWidgetItem(format_time(data["duration"])))
        self.table.setItem(row, 2, QTableWidgetItem(data["subtitle"]))
        self.table.setItem(row, 3, QTableWidgetItem(data["op_text"]))
        self.table.setItem(row, 4, QTableWidgetItem(data["ed_text"]))

    def _on_scan_finished(self):
        if not self.video_files:
            QMessageBox.information(self, "Informasi", "Tidak ditemukan berkas video di folder.")
            self.reject()
            return
            
        self.progress_bar.setValue(100)
        self.btn_start.setEnabled(True)
        self.lbl_status_text.setText(f"Siap memproses {len(self.video_files)} episode video anime.")

    def _start_processing(self):
        if self.processing:
            return
            
        self.processing = True
        self.cancel_event.clear()
        self.btn_start.setEnabled(False)
        self.btn_cancel.setText("Batalkan Proses")
        
        mode = "hardsub" if self.rb_hard.isChecked() else "softsub"
        merge = self.cb_merge.isChecked()
        ocr_tolerance = self.ocr_slider.value() / 10.0
        out_path = self.txt_output.text()
        
        # Luncurkan QThread asinkron
        self._merge_worker = MergeWorker(self.parent_dir, mode, merge, ocr_tolerance, self.cancel_event)
        self._merge_worker.progress.connect(self._on_merge_progress)
        self._merge_worker.finished.connect(self._on_merge_finished)
        self._merge_worker.start()

    def _on_merge_progress(self, file_idx, pct, status_text):
        total = len(self.video_files)
        overall_pct = int((file_idx / total) * 100 + (pct / total))
        self.progress_bar.setValue(overall_pct)
        self.lbl_status_text.setText(f"Eps {file_idx+1}/{total} ({pct:.1f}%) - {status_text}")

    def _on_merge_finished(self, success, msg):
        self.processing = False
        self.btn_start.setEnabled(True)
        self.btn_cancel.setText("Batal / Keluar")
        self.progress_bar.setValue(100)
        
        if self.cancel_event.is_set():
            self.lbl_status_text.setText("Proses dibatalkan oleh pengguna.")
            return

        folder_name = os.path.basename(self.parent_dir.rstrip(r"\/"))
        out_mp4_final = self.txt_output.text()
        out_srt_final = os.path.splitext(out_mp4_final)[0] + ".srt"
        
        default_mp4 = os.path.join(self.parent_dir, f"{folder_name}_clean.mp4")
        default_srt = os.path.join(self.parent_dir, f"{folder_name}_clean.srt")
        
        if success and self.cb_merge.isChecked():
            # Rename output kustom jika berbeda dari default
            if os.path.exists(default_mp4) and os.path.abspath(default_mp4) != os.path.abspath(out_mp4_final):
                try:
                    if os.path.exists(out_mp4_final): os.remove(out_mp4_final)
                    os.rename(default_mp4, out_mp4_final)
                except Exception as ex:
                    print(f"Gagal memindahkan mp4: {ex}")
            if os.path.exists(default_srt) and os.path.abspath(default_srt) != os.path.abspath(out_srt_final):
                try:
                    if os.path.exists(out_srt_final): os.remove(out_srt_final)
                    os.rename(default_srt, out_srt_final)
                except Exception as ex:
                    print(f"Gagal memindahkan srt: {ex}")
                    
        if success:
            QMessageBox.information(self, "Sukses", f"Proses Batch Selesai!\n{msg}")
            self.accept()
        else:
            QMessageBox.critical(self, "Gagal Ekspor Massal", f"Terjadi kesalahan:\n{msg}")

    def _on_cancel(self):
        if self.processing:
            reply = QMessageBox.question(self, "Konfirmasi", 
                                         "Apakah Anda yakin ingin membatalkan proses massal yang sedang berjalan?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.cancel_event.set()
                self.processing = False
                self.btn_start.setEnabled(True)
                self.btn_cancel.setText("Batal / Keluar")
                self.lbl_status_text.setText("Proses dibatalkan.")
        else:
            self.reject()
