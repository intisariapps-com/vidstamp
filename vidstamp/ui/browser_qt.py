"""
vidstamp/ui/browser_qt.py - Komponen UI Browser Panel Kiri berbasis PySide6
"""
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QTreeView, QFileSystemModel, QApplication)
from PySide6.QtCore import Qt, QDir, QModelIndex

class LeftBrowserPanel(QWidget):
    def __init__(self, parent, on_video_select_callback, def_dir_callback):
        super().__init__(parent)
        
        self.on_video_select = on_video_select_callback
        self.get_default_dir = def_dir_callback
        self.cur_folder = ""
        
        self._build_ui()
        self._setup_file_system()
        self._apply_stylesheet()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(6)
        
        # 1. Header (Folder Browser Title & Browse Button)
        header_layout = QHBoxLayout()
        lbl_title = QLabel("📂 Folder Browser", self)
        lbl_title.setObjectName("BrowserTitle")
        
        btn_browse = QPushButton("Telusuri...", self)
        btn_browse.setObjectName("BrowseButton")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.clicked.connect(self._browse)
        
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(btn_browse)
        layout.addLayout(header_layout)
        
        # 2. Breadcrumb / Path Display
        self.txt_path = QLineEdit(self)
        self.txt_path.setObjectName("PathDisplay")
        self.txt_path.setReadOnly(True)
        layout.addWidget(self.txt_path)
        
        # 3. Filter / Search Box
        filter_layout = QHBoxLayout()
        lbl_filter = QLabel("Cari:", self)
        lbl_filter.setObjectName("FilterLabel")
        
        self.txt_filter = QLineEdit(self)
        self.txt_filter.setObjectName("FilterInput")
        self.txt_filter.setPlaceholderText("Filter nama video...")
        self.txt_filter.textChanged.connect(self._on_filter_changed)
        
        filter_layout.addWidget(lbl_filter)
        filter_layout.addWidget(self.txt_filter)
        layout.addLayout(filter_layout)
        
        # 4. Tree View File Browser (Terpadu & Modern)
        self.tree_view = QTreeView(self)
        self.tree_view.setObjectName("FileTree")
        self.tree_view.doubleClicked.connect(self._on_item_double_clicked)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        layout.addWidget(self.tree_view)
        
        # Status Label di bagian bawah
        self.lbl_status = QLabel("Silakan pilih folder video.", self)
        self.lbl_status.setObjectName("StatusLabel")
        layout.addWidget(self.lbl_status)

    def _setup_file_system(self):
        # Inisialisasi Model Sistem Berkas Qt6
        self.model = QFileSystemModel(self)
        self.model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        
        # Saring hanya berkas video anime populer
        self.model.setNameFilters(["*.mkv", "*.mp4", "*.avi"])
        self.model.setNameFilterDisables(False) # Sembunyikan berkas yang tidak lolos filter
        
        self.tree_view.setModel(self.model)

    def _apply_stylesheet(self):
        qss = """
        #BrowserTitle {
            color: #a8dadc;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
            font-weight: bold;
        }
        #BrowseButton {
            background-color: #e94560;
            color: white;
            border: none;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 10px;
        }
        #BrowseButton:hover {
            background-color: #ff5e7e;
        }
        #PathDisplay {
            background-color: #0b0b18;
            color: #8888aa;
            border: 1px solid #1f4068;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            padding: 3px 6px;
        }
        #FilterLabel {
            color: #555577;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }
        #FilterInput {
            background-color: #1a1a3e;
            color: #e0e0ff;
            border: 1px solid #1f4068;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            padding: 3px 6px;
        }
        #FilterInput:focus {
            border: 1px solid #e94560;
        }
        #FileTree {
            background-color: #0d0d1a;
            color: #e0e0ff;
            border: 1px solid #1f4068;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }
        #FileTree::item {
            padding: 4px;
        }
        #FileTree::item:hover {
            background-color: #16213e;
        }
        #FileTree::item:selected {
            background-color: #1a4a6e;
            color: white;
        }
        #StatusLabel {
            color: #555577;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
        }
        """
        self.setStyleSheet(qss)

    def navigate_to(self, folder):
        """Membuka folder tertentu di TreeView."""
        if not folder or not os.path.isdir(folder):
            return
            
        self.cur_folder = folder
        self.txt_path.setText(folder)
        
        # Set root index untuk model sistem berkas
        root_index = self.model.setRootPath(folder)
        self.tree_view.setRootIndex(root_index)
        
        # Sembunyikan kolom ukuran, jenis, dan tanggal modifikasi agar tampilan ringkas (hanya kolom nama)
        self.tree_view.setColumnHidden(1, True) # Size
        self.tree_view.setColumnHidden(2, True) # Type
        self.tree_view.setColumnHidden(3, True) # Date Modified
        self.tree_view.setHeaderHidden(True)   # Sembunyikan header kolom
        
        # Hitung jumlah file video di folder
        self._update_status_label()

    def _browse(self):
        from PySide6.QtWidgets import QFileDialog
        init = self.cur_folder or self.get_default_dir()
        d = QFileDialog.getExistingDirectory(self, "Pilih Folder Video", init)
        if d:
            self.navigate_to(d)

    def _on_filter_changed(self, text):
        # Menerapkan filter teks secara dinamis
        if text.strip():
            self.model.setNameFilters([f"*{text}*.mkv", f"*{text}*.mp4", f"*{text}*.avi"])
        else:
            self.model.setNameFilters(["*.mkv", "*.mp4", "*.avi"])

    def _on_item_double_clicked(self, index: QModelIndex):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self.on_video_select(path)

    def _update_status_label(self):
        # Hitung video secara manual di folder aktif saat ini
        try:
            vids = [n for n in os.listdir(self.cur_folder)
                    if os.path.isfile(os.path.join(self.cur_folder, n)) 
                    and os.path.splitext(n)[1].lower() in ['.mkv', '.mp4', '.avi']]
            self.lbl_status.setText(f"Menampilkan {len(vids)} video.")
        except Exception:
            self.lbl_status.setText("Menampilkan 0 video.")

    def highlight_video(self, path):
        """Memilih berkas video di dalam TreeView secara terfokus"""
        index = self.model.index(path)
        if index.isValid():
            self.tree_view.setCurrentIndex(index)
            self.tree_view.scrollTo(index)
