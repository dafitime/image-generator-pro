"""
Right panel – Preview image and PRO Metadata editor.
FIXED: Auto‑save on tag change.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from src.gui.widgets.tag_widget import TagEditor

class RightPanel(QWidget):
    tags_updated = pyqtSignal()   # 🟢 NEW SIGNAL: auto‑save trigger

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. Header
        lbl = QLabel("DETAILS")
        lbl.setObjectName("SubHeader")
        layout.addWidget(lbl)

        # 2. Preview Image
        self.preview = QLabel("No Selection")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet("""
            QLabel {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 8px;
            }
        """)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview.setMinimumHeight(200)
        layout.addWidget(self.preview, 2)

        # 3. Metadata Form
        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)
        form_layout.setContentsMargins(0, 10, 0, 0)
        form_layout.setVerticalSpacing(10)

        # Filename
        form_layout.addWidget(QLabel("Filename:"), 0, 0)
        self.filename_edit = QLineEdit()
        form_layout.addWidget(self.filename_edit, 0, 1)

        # Tags (Auto‑save enabled)
        form_layout.addWidget(QLabel("Tags:"), 1, 0)
        self.tag_editor = TagEditor()
        self.tag_editor.setMinimumHeight(80)
        self.tag_editor.tags_changed.connect(self._on_tags_changed)   # 🟢 CONNECT
        form_layout.addWidget(self.tag_editor, 1, 1)

        layout.addWidget(form_widget)

        self.setMinimumWidth(320)
        self.setMaximumWidth(450)

    def _on_tags_changed(self):
        """Emit the global signal so main window can auto‑save."""
        self.tags_updated.emit()

    def set_preview_pixmap(self, pixmap: QPixmap):
        self.preview.setPixmap(pixmap)

    def clear_preview(self):
        self.preview.clear()
        self.preview.setText("No Selection")

    def set_metadata(self, filename: str, tags: list):
        self.filename_edit.setText(filename)
        self.tag_editor.set_tags(tags)   # Does NOT emit tags_changed

    def get_metadata(self):
        return {
            'filename': self.filename_edit.text().strip(),
            'tags': self.tag_editor.get_tags()
        }