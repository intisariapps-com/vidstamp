"""
vidstamp/ui/launcher.py - Jendela Menu Pembuka (Startup Launcher Screen) menggunakan PySide6
"""
import sys
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QApplication
from PySide6.QtCore import Qt

class LauncherWindow(QWidget):
    def __init__(self, launch_player_fn, launch_wizard_fn, get_def_dir_fn):
        super().__init__()
        self.launch_player = launch_player_fn
        self.launch_wizard = launch_wizard_fn
        self.get_default_dir = get_def_dir_fn
        
        self.setWindowTitle("VidStamp Launcher")
        self.setFixedSize(520, 350)
        self.setObjectName("LauncherWindow")
        
        # Center di screen
        self._center_on_screen()
        self._build_ui()
        self._apply_stylesheet()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Header Frame
        header_widget = QWidget(self)
        header_widget.setObjectName("HeaderWidget")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel("⚡ WELCOME TO VIDSTAMP ⚡", header_widget)
        lbl_title.setObjectName("HeaderTitle")
        lbl_title.setAlignment(Qt.AlignCenter)
        
        lbl_subtitle = QLabel("Video Timestamp, Skip OP/ED & Batch Merger Manager", header_widget)
        lbl_subtitle.setObjectName("HeaderSubtitle")
        lbl_subtitle.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_subtitle)
        main_layout.addWidget(header_widget)
        
        # 2. Body Container
        body_widget = QWidget(self)
        body_widget.setObjectName("BodyWidget")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(40, 20, 40, 20)
        body_layout.setSpacing(15)
        
        lbl_desc = QLabel("Silakan pilih mode operasi yang ingin dibuka:", body_widget)
        lbl_desc.setObjectName("DescLabel")
        lbl_desc.setAlignment(Qt.AlignCenter)
        body_layout.addWidget(lbl_desc)
        
        # Buttons
        self.btn_player = QPushButton("📺 Buka Pemutar Media & Marker (VidStamp)", body_widget)
        self.btn_player.setObjectName("PlayerButton")
        self.btn_player.setFixedHeight(45)
        self.btn_player.clicked.connect(self._click_player)
        body_layout.addWidget(self.btn_player)
        
        self.btn_wizard = QPushButton("🎛️ Buka Batch Merger & Skip Config Wizard", body_widget)
        self.btn_wizard.setObjectName("WizardButton")
        self.btn_wizard.setFixedHeight(45)
        self.btn_wizard.clicked.connect(self._click_wizard)
        body_layout.addWidget(self.btn_wizard)
        
        # 3. Bottom Row
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 10, 0, 0)
        
        self.btn_exit = QPushButton("Keluar", body_widget)
        self.btn_exit.setObjectName("ExitButton")
        self.btn_exit.setFixedSize(80, 28)
        self.btn_exit.clicked.connect(QApplication.quit)
        
        lbl_ver = QLabel("v1.3.0", body_widget)
        lbl_ver.setObjectName("VersionLabel")
        lbl_ver.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        bottom_layout.addWidget(self.btn_exit)
        bottom_layout.addStretch()
        bottom_layout.addWidget(lbl_ver)
        
        body_layout.addLayout(bottom_layout)
        main_layout.addWidget(body_widget)

    def _apply_stylesheet(self):
        qss = """
        #LauncherWindow {
            background-color: #0d0d1a;
        }
        #HeaderWidget {
            background-color: #16213e;
            border-bottom: 2px solid #1f4068;
        }
        #HeaderTitle {
            color: #a8dadc;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 16px;
            font-weight: bold;
        }
        #HeaderSubtitle {
            color: #8888aa;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
            font-style: italic;
        }
        #BodyWidget {
            background-color: #0d0d1a;
        }
        #DescLabel {
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }
        #PlayerButton {
            background-color: #1a1a3e;
            color: #7ec8e3;
            border: none;
            border-radius: 6px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
            font-weight: bold;
        }
        #PlayerButton:hover {
            background-color: #e94560;
            color: #ffffff;
        }
        #WizardButton {
            background-color: #1e5f3a;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
            font-weight: bold;
        }
        #WizardButton:hover {
            background-color: #2a7f50;
        }
        #ExitButton {
            background-color: #333333;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
            font-weight: bold;
        }
        #ExitButton:hover {
            background-color: #444444;
        }
        #VersionLabel {
            color: #444466;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
        }
        """
        self.setStyleSheet(qss)

    def _click_player(self):
        self.close()
        self.launch_player()

    def _click_wizard(self):
        init_dir = self.get_default_dir()
        d = QFileDialog.getExistingDirectory(self, "Pilih Folder Video Anime", init_dir)
        if d:
            self.close()
            self.launch_wizard(d)
