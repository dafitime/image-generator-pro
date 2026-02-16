"""
Right panel – Preview image and PRO Metadata editor.
Now includes rating and color label.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QHBoxLayout, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from src.gui.widgets.tag_widget import TagEditor

class RightPanel(QWidget):
    tags_updated = pyqtSignal()
    rating_changed = pyqtSignal(int)
    color_label_changed = pyqtSignal(str)

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

        # Tags
        form_layout.addWidget(QLabel("Tags:"), 1, 0)
        self.tag_editor = TagEditor()
        self.tag_editor.setMinimumHeight(80)
        self.tag_editor.tags_changed.connect(self._on_tags_changed)
        form_layout.addWidget(self.tag_editor, 1, 1)

        # Rating
        form_layout.addWidget(QLabel("Rating:"), 2, 0)
        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["None", "★", "★★", "★★★", "★★★★", "★★★★★"])
        self.rating_combo.currentIndexChanged.connect(self._on_rating_changed)
        form_layout.addWidget(self.rating_combo, 2, 1)

        # Color Label
        form_layout.addWidget(QLabel("Label:"), 3, 0)
        self.color_combo = QComboBox()
        self.color_combo.addItems(["None", "Red", "Yellow", "Green", "Blue", "Purple"])
        self.color_combo.currentTextChanged.connect(self._on_color_label_changed)
        form_layout.addWidget(self.color_combo, 3, 1)

        layout.addWidget(form_widget)

        self.setMinimumWidth(320)
        self.setMaximumWidth(450)

    def _on_tags_changed(self):
        self.tags_updated.emit()

    def _on_rating_changed(self, index):
        self.rating_changed.emit(index)  # 0=None, 1=1 star, etc.

    def _on_color_label_changed(self, text):
        self.color_label_changed.emit(text if text != "None" else "")

    def set_preview_pixmap(self, pixmap: QPixmap):
        self.preview.setPixmap(pixmap)

    def clear_preview(self):
        self.preview.clear()
        self.preview.setText("No Selection")

    def set_metadata(self, filename: str, tags: list, rating: int = 0, color_label: str = ""):
        self.filename_edit.setText(filename)
        self.tag_editor.set_tags(tags)
        self.rating_combo.setCurrentIndex(rating)  # 0=None, 1-5 stars
        # Find color label in combo
        index = self.color_combo.findText(color_label if color_label else "None")
        if index >= 0:
            self.color_combo.setCurrentIndex(index)

    def get_metadata(self):
        rating = self.rating_combo.currentIndex()  # 0=None, 1-5
        color = self.color_combo.currentText()
        return {
            'filename': self.filename_edit.text().strip(),
            'tags': self.tag_editor.get_tags(),
            'rating': rating,
            'color_label': '' if color == "None" else color
        }