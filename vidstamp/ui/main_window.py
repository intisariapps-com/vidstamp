"""
vidstamp/ui/main_window.py - Koordinator Window Utama dan Event Loops berbasis PySide6
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
        self.setWindowTitle("VidStamp - Video Timestamp & Scene Marker")
        self.resize(1200, 760)
        self.setMinimumSize(900, 580)
        self.setObjectName("MainWindow")
        
        self.browser_visible = True
        self.start_path = start_path
        
        self._build_ui()
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
        # Gunakan QSplitter untuk membagi folder browser kiri dan player kanan
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.setHandleWidth(5)
        self.splitter.setObjectName("MainSplitter")
        
        self.left_panel = LeftBrowserPanel(self.splitter, 
                                           on_video_select_callback=self.load_video,
                                           def_dir_callback=self.get_default_dir)
        self.right_panel = PlayerView(self.splitter, on_video_loaded_callback=self._on_video_loaded)
        
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        
        # Atur proporsi split: kiri 20%, kanan 80%
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 8)
        
        self.setCentralWidget(self.splitter)

    def _build_menu(self):
        # Menu Bar
        self.menu_bar = self.menuBar()
        self.menu_bar.setObjectName("MenuBar")
        
        self.tools_menu = self.menu_bar.addMenu("Peralatan")
        self.tools_menu.setObjectName("ToolsMenu")
        
        # Action Batch Merger
        self.action_merger = QAction("Batch Merger Wizard...", self)
        self.action_merger.setShortcut(QKeySequence("Ctrl+M"))
        self.action_merger.triggered.connect(self.open_batch_merger)
        self.tools_menu.addAction(self.action_merger)
        
        # Action Extractor
        self.action_extractor = QAction("Ekstraktor Subtitle & Audio...", self)
        self.action_extractor.triggered.connect(self.open_extractor_tool)
        self.tools_menu.addAction(self.action_extractor)

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
        # Simpan posisi video lama
        if self.right_panel.engine.cap and self.right_panel.engine.video_path:
            cur_sec = self.right_panel.engine.cur_idx / self.right_panel.engine.fps
            from vidstamp.utils.file_manager import save_playback_state
            save_playback_state(self.right_panel.engine.video_path, cur_sec)
            
        self.right_panel.load_video(video_path)

    def _on_video_loaded(self, path):
        self.left_panel.highlight_video(path)
        self.setWindowTitle(f"VidStamp - {os.path.basename(path)}")

    def toggle_browser(self):
        self.browser_visible = not self.browser_visible
        if self.browser_visible:
            self.left_panel.show()
        else:
            self.left_panel.hide()
        self.right_panel.render_current_frame()

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        # Global Shortcuts
        if key == Qt.Key_Tab:
            self.toggle_browser()
        elif key == Qt.Key_F11:
            self.right_panel.toggle_fullscreen()
        elif key == Qt.Key_Escape:
            if self.right_panel.is_fullscreen:
                self.right_panel.toggle_fullscreen()
        elif key == Qt.Key_Left:
            if modifiers & Qt.ShiftModifier:
                self.right_panel.seek_offset(-10)
            else:
                self.right_panel.seek_offset(-1)
        elif key == Qt.Key_Right:
            if modifiers & Qt.ShiftModifier:
                self.right_panel.seek_offset(10)
            else:
                self.right_panel.seek_offset(1)
        else:
            super().keyPressEvent(event)

    def open_batch_merger(self):
        current_dir = None
        if self.right_panel.engine.video_path:
            current_dir = os.path.dirname(self.right_panel.engine.video_path)
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
        if self.right_panel.engine.video_path:
            current_dir = os.path.dirname(self.right_panel.engine.video_path)
        else:
            current_dir = self.left_panel.cur_folder or self.get_default_dir()
            
        from vidstamp.ui.extractor_tool import AudioSubExtractorWizard
        wizard = AudioSubExtractorWizard(self, current_dir)
        wizard.exec()

    def closeEvent(self, event):
        # Simpan posisi pemutaran detik terakhir saat aplikasi ditutup
        if self.right_panel.engine.cap and self.right_panel.engine.video_path:
            cur_sec = self.right_panel.engine.cur_idx / self.right_panel.engine.fps
            from vidstamp.utils.file_manager import save_playback_state
            save_playback_state(self.right_panel.engine.video_path, cur_sec)
            
        self.right_panel.timer.stop()
        self.right_panel.save_timer.stop()
        self.right_panel.engine.release()
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
