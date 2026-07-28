"""
vidstamp/ui/main_window.py - Koordinator Jendela Utama Pendamping MPC-HC berbasis PySide6
"""
import sys
import os
from PySide6.QtWidgets import QMainWindow, QSplitter, QMenuBar, QMenu, QMessageBox, QApplication, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QAction

from vidstamp.config import ROOT_DIRS
from vidstamp.ui.browser import LeftBrowserPanel
from vidstamp.ui.player_view import PlayerView

class VideoAppController(QMainWindow):
    def __init__(self, start_path=None):
        super().__init__()
        self.setWindowTitle("VidStamp - MPC-HC Companion")
        self.resize(750, 200) # Ukuran yang sangat kompak dan elegan untuk Companion App!
        self.setMinimumSize(600, 180)
        self.setObjectName("MainWindow")
        
        self.browser_visible = False
        self.start_path = start_path
        
        self._build_ui()
        self.left_panel.hide()  # Sembunyikan Folder Browser secara default saat startup
        self._build_menu()
        self._apply_stylesheet()
        
        # Load initial path
        init_path = start_path or self.get_default_dir()
        if init_path and os.path.isdir(init_path):
            self.left_panel.navigate_to(init_path)
        elif init_path and os.path.isfile(init_path):
            self.left_panel.navigate_to(os.path.dirname(init_path))
            self.load_video(init_path)

    def get_default_dir(self):
        for d in ROOT_DIRS:
            if os.path.isdir(d):
                return d
        return os.path.expanduser("~")

    def _build_ui(self):
        # Gunakan QSplitter untuk membagi folder browser kiri dan panel kontrol kanan
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.setHandleWidth(5)
        self.splitter.setObjectName("MainSplitter")
        
        self.left_panel = LeftBrowserPanel(self.splitter, 
                                           on_video_select_callback=self.load_video,
                                           def_dir_callback=self.get_default_dir)
        self.right_panel = PlayerView(self.splitter, on_video_loaded_callback=self._on_video_loaded)
        
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 7)
        
        self.setCentralWidget(self.splitter)

    def _build_menu(self):
        # Menu Bar
        self.menu_bar = self.menuBar()
        self.menu_bar.setObjectName("MenuBar")
        
        # 1. Menu Berkas
        self.file_menu = self.menu_bar.addMenu("Berkas")
        self.file_menu.setObjectName("FileMenu")
        
        self.action_open = QAction("Buka Video...", self)
        self.action_open.setShortcut(QKeySequence("Ctrl+O"))
        self.action_open.triggered.connect(self.open_video_dialog)
        self.file_menu.addAction(self.action_open)
        
        self.file_menu.addSeparator()
        
        self.action_quit = QAction("Keluar", self)
        self.action_quit.setShortcut(QKeySequence("Ctrl+Q"))
        self.action_quit.triggered.connect(self.close)
        self.file_menu.addAction(self.action_quit)
        
        # 2. Menu Peralatan
        self.tools_menu = self.menu_bar.addMenu("Peralatan")
        self.tools_menu.setObjectName("ToolsMenu")
        
        # Action Daftar Catatan Adegan
        self.action_scenes = QAction("Daftar Catatan Adegan...", self)
        self.action_scenes.setShortcut(QKeySequence("Ctrl+L"))
        self.action_scenes.triggered.connect(self.right_panel.open_scenes_dialog)
        self.tools_menu.addAction(self.action_scenes)
        
        self.tools_menu.addSeparator()
        
        # Action Batch Merger
        self.action_merger = QAction("Batch Merger Wizard...", self)
        self.action_merger.setShortcut(QKeySequence("Ctrl+M"))
        self.action_merger.triggered.connect(self.open_batch_merger)
        self.tools_menu.addAction(self.action_merger)
        
        # Action Extractor
        self.action_extractor = QAction("Ekstraktor Subtitle & Audio...", self)
        self.action_extractor.triggered.connect(self.open_extractor_tool)
        self.tools_menu.addAction(self.action_extractor)

    def open_video_dialog(self):
        from PySide6.QtWidgets import QFileDialog
        init = self.left_panel.cur_folder or self.get_default_dir()
        fn, _ = QFileDialog.getOpenFileName(self, "Pilih Berkas Video", init, "Video Files (*.mkv *.mp4 *.avi)")
        if fn:
            self.load_video(fn)

    def _apply_stylesheet(self):
        qss = """
        QMainWindow {
            background-color: #0d0d1a;
        }
        #MenuBar {
            background-color: #0d0d1a;
            color: white;
            border-bottom: 1px solid #1f4068;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }
        #MenuBar::item {
            background-color: #0d0d1a;
            color: white;
            padding: 4px 10px;
        }
        #MenuBar::item:selected {
            background-color: #1a1a3e;
            color: #7ec8e3;
        }
        QMenu {
            background-color: #0d0d1a;
            color: white;
            border: 1px solid #1f4068;
        }
        QMenu::item:selected {
            background-color: #1a1a3e;
            color: #7ec8e3;
        }
        #MainSplitter::handle {
            background-color: #1f4068;
        }
        """
        self.setStyleSheet(qss)

    def load_video(self, video_path):
        # Menyuruh OS membuka video dengan default handler (MPC-HC) jika dipicu secara lokal
        if os.path.exists(video_path):
            try:
                os.startfile(video_path)
            except Exception as err:
                print(f"Gagal meluncurkan berkas video via OS: {err}")
                
        self.right_panel.load_video(video_path)

    def _on_video_loaded(self, path):
        self.left_panel.highlight_video(path)
        self.setWindowTitle(f"VidStamp - [Companion] {os.path.basename(path)}")

    def toggle_browser(self):
        self.browser_visible = not self.browser_visible
        if self.browser_visible:
            self.left_panel.show()
        else:
            self.left_panel.hide()

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        # Global Shortcuts
        if modifiers & Qt.ControlModifier and key == Qt.Key_O:
            self.open_video_dialog()
        elif modifiers & Qt.ControlModifier and key == Qt.Key_L:
            self.right_panel.open_scenes_dialog()
        elif modifiers & Qt.ControlModifier and key == Qt.Key_T:
            # Ctrl+T: Toggle record pintar
            if self.right_panel.mark_start is None:
                self.right_panel._mark_start_fn()
            else:
                self.right_panel._mark_end_fn()
        elif modifiers & Qt.ControlModifier and key == Qt.Key_Space:
            # Ctrl+Space: Batal rekam
            self.right_panel.mark_start = None
            self.right_panel.mark_end = None
            self.right_panel.btn_start.setText("[M] Start")
            self.right_panel.btn_end.setText("[N] End")
            self.right_panel.lbl_status_bar_update("Perekaman dibatalkan.")
        elif key == Qt.Key_M:
            self.right_panel._mark_start_fn()
        elif key == Qt.Key_N:
            self.right_panel._mark_end_fn()
        elif key == Qt.Key_Tab:
            self.toggle_browser()
        elif key == Qt.Key_Space:
            self.right_panel.client.toggle_play()
        elif key == Qt.Key_Left:
            if modifiers & Qt.ShiftModifier:
                self.right_panel.client.jump_backward(10)
            else:
                self.right_panel.client.jump_backward(5)
        elif key == Qt.Key_Right:
            if modifiers & Qt.ShiftModifier:
                self.right_panel.client.jump_forward(10)
            else:
                self.right_panel.client.jump_forward(5)
        else:
            super().keyPressEvent(event)

    def open_batch_merger(self):
        current_dir = None
        if self.right_panel.video_path:
            current_dir = os.path.dirname(self.right_panel.video_path)
        else:
            current_dir = self.left_panel.cur_folder or self.get_default_dir()
            
        if not current_dir or not os.path.isdir(current_dir):
            QMessageBox.critical(self, "Pemberitahuan", "Silakan buka folder video terlebih dahulu pada panel folder kiri.")
            return
            
        from vidstamp.ui.batch_merger import BatchMergerWizard
        wizard = BatchMergerWizard(self, current_dir)
        wizard.exec()

    def open_extractor_tool(self):
        current_dir = None
        if self.right_panel.video_path:
            current_dir = os.path.dirname(self.right_panel.video_path)
        else:
            current_dir = self.left_panel.cur_folder or self.get_default_dir()
            
        from vidstamp.ui.extractor_tool import AudioSubExtractorWizard
        wizard = AudioSubExtractorWizard(self, current_dir)
        wizard.exec()

    def closeEvent(self, event):
        self.right_panel.sync_timer.stop()
        event.accept()

def start_gui(start_path=None):
    from PySide6.QtWidgets import QApplication
    from vidstamp.ui.launcher import LauncherWindow
    from vidstamp.config import ROOT_DIRS
    
    app = QApplication(sys.argv) if QApplication.instance() is None else QApplication.instance()
    
    def get_default_dir():
        for d in ROOT_DIRS:
            if os.path.isdir(d):
                return d
        return os.path.expanduser("~")

    # List reference untuk menyimpan objek window agar tidak di-garbage collect
    active_windows = []

    def launch_player():
        launcher.close()
        controller = VideoAppController(start_path)
        controller.show()
        active_windows.append(controller)

    def launch_wizard(folder_path):
        launcher.close()
        from vidstamp.ui.batch_merger import BatchMergerWizard
        wizard = BatchMergerWizard(None, folder_path)
        wizard.show()
        active_windows.append(wizard)

    # Jika start_path diberikan langsung buka player
    if start_path and os.path.exists(start_path):
        controller = VideoAppController(start_path)
        controller.show()
        active_windows.append(controller)
    else:
        # Jalankan launcher screen
        launcher = LauncherWindow(
            launch_player_fn=launch_player,
            launch_wizard_fn=launch_wizard,
            get_def_dir_fn=get_default_dir
        )
        launcher.show()
        
    sys.exit(app.exec())
