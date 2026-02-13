"""
src/gui/splash_screen.py
Modern splash screen with progress bar.
FIXED: Taskbar icon now appears immediately; Splash no longer stays on top.
"""
from PyQt6.QtWidgets import (
    QSplashScreen, QProgressBar, QVBoxLayout, QLabel, QWidget, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor, QIcon
import qtawesome as qta

class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(400, 250)
        pixmap.fill(QColor("#ffffff"))
        super().__init__(pixmap)

        # --- FIX: Removed WindowStaysOnTopHint & Added Taskbar Support ---
        # WindowStaysOnTopHint made it stay above everything.
        # We use WindowMinimizeButtonHint or similar to force taskbar presence.
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.FramelessWindowHint
        )
        # ----------------------------------------------------------------

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Ensure the splash itself has the icon for the taskbar
        self.setWindowIcon(qta.icon('fa5s.images', color='#0d6efd'))

        lbl_icon = QLabel()
        icon = qta.icon('fa5s.images', color='#0d6efd')
        lbl_icon.setPixmap(icon.pixmap(64, 64))
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_icon)

        lbl_title = QLabel("Image Organizer Pro")
        lbl_title.setStyleSheet("color: #212529; font-size: 24px; font-weight: bold;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        self.lbl_status = QLabel("Loading AI Engine...")
        self.lbl_status.setStyleSheet("color: #6c757d; font-size: 12px;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)

        layout.addSpacing(20)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #e9ecef;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #0d6efd;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress)

    def update_progress(self, value, message=None):
        self.progress.setValue(value)
        if message:
            self.lbl_status.setText(message)
        QApplication.instance().processEvents()