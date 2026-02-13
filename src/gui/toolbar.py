"""
Top toolbar – Uses qtawesome icons for a cleaner look.
Matches the professional menu style.
"""
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QFileDialog, QSizePolicy, QLineEdit
)
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta

class Toolbar(QFrame):
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # We don't need manual borders; qdarktheme handles the container style
        # just nice padding.
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10) 
        main_layout.setSpacing(10)

        # ROW 1: Source & Destination
        row1 = QHBoxLayout()
        row1.setSpacing(15)

        # Helper to create nice icon buttons
        def create_icon_btn(icon_name, tooltip):
            btn = QPushButton()
            btn.setIcon(qta.icon(icon_name, color='#495057'))
            btn.setFixedSize(36, 36)
            btn.setToolTip(tooltip)
            return btn

        # Source Input
        src_label = QLabel("SOURCE:")
        src_label.setStyleSheet("font-weight: bold;")
        row1.addWidget(src_label)

        self.src_path = QLineEdit(config.default_source)
        self.src_path.setReadOnly(True)
        self.src_path.setPlaceholderText("Select source folder...")
        row1.addWidget(self.src_path)

        self.btn_src = create_icon_btn('fa5s.folder-open', "Browse Source")
        row1.addWidget(self.btn_src)

        # Destination Input
        dest_label = QLabel("DESTINATION:")
        dest_label.setStyleSheet("font-weight: bold; margin-left: 10px;")
        row1.addWidget(dest_label)

        self.dest_path = QLineEdit(config.default_dest)
        self.dest_path.setReadOnly(True)
        self.dest_path.setPlaceholderText("Select destination folder...")
        row1.addWidget(self.dest_path)

        self.btn_dest = create_icon_btn('fa5s.folder', "Browse Destination")
        row1.addWidget(self.btn_dest)

        main_layout.addLayout(row1)

        # ROW 2: Primary Actions (Scan / Commit)
        row2 = QHBoxLayout()
        row2.setSpacing(15)

        # SCAN BUTTON (Big, Blue)
        self.btn_scanstop = QPushButton(" START SCAN")
        self.btn_scanstop.setIcon(qta.icon('fa5s.play', color='white'))
        self.btn_scanstop.setIconSize(QSize(16, 16))
        self.btn_scanstop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scanstop.setFixedSize(140, 40)
        # We rely on qdarktheme for base, but can override colors for emphasis
        self.btn_scanstop.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd; 
                color: white; 
                font-weight: bold; 
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #0b5ed7; }
        """)
        row2.addWidget(self.btn_scanstop)

        # COMMIT BUTTON (Green, initially disabled)
        self.btn_commit = QPushButton(" COMMIT FILES")
        self.btn_commit.setIcon(qta.icon('fa5s.check', color='white'))
        self.btn_commit.setIconSize(QSize(16, 16))
        self.btn_commit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_commit.setFixedSize(140, 40)
        self.btn_commit.setEnabled(False)
        self.btn_commit.setStyleSheet("""
            QPushButton {
                background-color: #198754; 
                color: white; 
                font-weight: bold; 
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #157347; }
            QPushButton:disabled { background-color: #6c757d; color: #dee2e6; }
        """)
        row2.addWidget(self.btn_commit)

        row2.addStretch(1) # Push buttons to left
        main_layout.addLayout(row2)

    # --- Public API ---
    def set_source(self, path: str): self.src_path.setText(path)
    def set_destination(self, path: str): self.dest_path.setText(path)
    def get_source(self) -> str: return self.src_path.text()
    def get_destination(self) -> str: return self.dest_path.text()

    def set_scan_state(self, is_scanning: bool):
        if is_scanning:
            self.btn_scanstop.setText(" STOP SCAN")
            self.btn_scanstop.setIcon(qta.icon('fa5s.stop', color='white'))
            self.btn_scanstop.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545; color: white; 
                    font-weight: bold; border-radius: 6px; font-size: 14px;
                }
                QPushButton:hover { background-color: #bb2d3b; }
            """)
        else:
            self.btn_scanstop.setText(" START SCAN")
            self.btn_scanstop.setIcon(qta.icon('fa5s.play', color='white'))
            self.btn_scanstop.setStyleSheet("""
                QPushButton {
                    background-color: #0d6efd; color: white; 
                    font-weight: bold; border-radius: 6px; font-size: 14px;
                }
                QPushButton:hover { background-color: #0b5ed7; }
            """)

    def is_scanning(self) -> bool:
        return "STOP" in self.btn_scanstop.text()

    def set_commit_enabled(self, enabled: bool):
        self.btn_commit.setEnabled(enabled)

    def on_browse_source(self, callback):
        self.btn_src.clicked.connect(lambda: self._browse(callback, True))
    def on_browse_dest(self, callback):
        self.btn_dest.clicked.connect(lambda: self._browse(callback, False))
    def _browse(self, callback, is_source):
        current = self.get_source() if is_source else self.get_destination()
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", current)
        if folder: callback(folder)

    def on_scan_toggle(self, callback):
        self.btn_scanstop.clicked.connect(callback)

    def on_commit(self, callback):
        self.btn_commit.clicked.connect(callback)