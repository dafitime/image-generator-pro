from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QPixmap

class CardWidget(QFrame):
    clicked = pyqtSignal(str)
    doubleClicked = pyqtSignal(str)

    THUMB_HEIGHT = 180   # fixed

    def __init__(self, path, filename):
        super().__init__()
        self.path = path
        self.filename = filename
        self.pixmap = None

        self.setFrameShape(QFrame.Shape.NoFrame)
        # fixed size: thumb + 40 width, thumb + 80 height
        self.setFixedSize(self.THUMB_HEIGHT + 40, self.THUMB_HEIGHT + 80)

        self.setStyleSheet("""
            CardWidget { background-color: transparent; border-radius: 6px; }
            CardWidget:hover { background-color: rgba(13, 110, 253, 0.1); border: 1px solid #0d6efd; }
            CardWidget[selected="true"] { background-color: rgba(13, 110, 253, 0.3); border: 2px solid #0d6efd; }
            QLabel { color: palette(text); background: transparent; font-size: 11px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        self.thumb_label = QLabel("...")
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumb_label)

        self.name_label = QLabel(filename)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(45)
        layout.addWidget(self.name_label)

    def set_thumbnail(self, pixmap):
        self.pixmap = pixmap
        if not pixmap.isNull():
            scaled = pixmap.scaledToHeight(self.THUMB_HEIGHT,
                                           Qt.TransformationMode.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.path)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.doubleClicked.emit(self.path)
        super().mouseDoubleClickEvent(event)

    def set_selected(self, selected):
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class MiddlePanel(QWidget):
    itemClicked = pyqtSignal(str)
    itemDoubleClicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # no margins – clean

        # Header – only the "GALLERY" label now
        header = QHBoxLayout()
        lbl = QLabel("GALLERY")
        lbl.setObjectName("SubHeader")
        header.addWidget(lbl)
        header.addStretch()
        layout.addLayout(header)

        # Scrollable Grid – centered
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter)  # center horizontally

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll.setWidget(self.grid_container)
        layout.addWidget(self.scroll)

        self.cards = {}
        self.current_selected_path = None

        # React to container resizes
        self.grid_container.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.grid_container and event.type() == QEvent.Type.Resize:
            self._reorganize_grid()
        return super().eventFilter(obj, event)

    def _reorganize_grid(self):
        """Calculate column count using fixed card width, no stretching, then center."""
        if not self.cards:
            return

        viewport_width = self.scroll.viewport().width()
        spacing = self.grid_layout.horizontalSpacing()
        card_width = CardWidget.THUMB_HEIGHT + 40   # fixed

        # number of columns that fit without horizontal scrollbar
        cols = max(1, (viewport_width + spacing) // (card_width + spacing))

        # Clear layout
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        # Add cards in new column order
        for i, card in enumerate(self.cards.values()):
            self.grid_layout.addWidget(card, i // cols, i % cols)

        # NO column stretching – columns keep their natural size
        # Force immediate layout update
        self.grid_layout.activate()

    def add_item(self, path, name):
        card = CardWidget(path, name)
        card.clicked.connect(self._handle_click)
        card.doubleClicked.connect(self.itemDoubleClicked.emit)
        self.cards[path] = card
        self._reorganize_grid()

    def _handle_click(self, path):
        if self.current_selected_path in self.cards:
            self.cards[self.current_selected_path].set_selected(False)
        self.cards[path].set_selected(True)
        self.current_selected_path = path
        self.itemClicked.emit(path)

    def set_thumbnail(self, path, pixmap):
        if path in self.cards:
            self.cards[path].set_thumbnail(pixmap)

    def clear(self):
        for card in self.cards.values():
            card.deleteLater()
        self.cards.clear()
        self.current_selected_path = None

    def set_on_clicked(self, callback):
        self.itemClicked.connect(callback)

    def set_on_double_clicked(self, callback):
        self.itemDoubleClicked.connect(callback)