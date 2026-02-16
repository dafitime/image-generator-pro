from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QSizePolicy, QGridLayout, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QPixmap, QMouseEvent, QPainter, QColor

class CardWidget(QFrame):
    clicked = pyqtSignal(str, Qt.KeyboardModifier)
    doubleClicked = pyqtSignal(str)

    THUMB_HEIGHT = 180
    # Color mapping for labels (semi‑transparent overlay)
    COLOR_MAP = {
        "Red":    (255, 0, 0, 60),
        "Yellow": (255, 255, 0, 60),
        "Green":  (0, 255, 0, 60),
        "Blue":   (0, 0, 255, 60),
        "Purple": (128, 0, 128, 60),
    }

    def __init__(self, path, filename, color_label=""):
        super().__init__()
        self.path = path
        self.filename = filename
        self.color_label = color_label
        self.pixmap = None
        self._selected = False

        self.setFrameShape(QFrame.Shape.NoFrame)
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
        if pixmap.isNull():
            return
        scaled = pixmap.scaledToHeight(self.THUMB_HEIGHT,
                                       Qt.TransformationMode.SmoothTransformation)
        # Apply color overlay if label exists
        if self.color_label and self.color_label in self.COLOR_MAP:
            tinted = self._apply_color_overlay(scaled, self.COLOR_MAP[self.color_label])
            self.thumb_label.setPixmap(tinted)
        else:
            self.thumb_label.setPixmap(scaled)

    def _apply_color_overlay(self, pixmap, color_rgba):
        """Return a copy of pixmap with a semi‑transparent color overlay."""
        tinted = pixmap.copy()
        painter = QPainter(tinted)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.fillRect(tinted.rect(), QColor(*color_rgba))
        painter.end()
        return tinted

    def set_color_label(self, color):
        self.color_label = color
        if self.pixmap:
            self.set_thumbnail(self.pixmap)  # refresh

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.path, event.modifiers())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.doubleClicked.emit(self.path)
        super().mouseDoubleClickEvent(event)

    def set_selected(self, selected: bool):
        if self._selected == selected:
            return
        self._selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class MiddlePanel(QWidget):
    itemClicked = pyqtSignal(str)
    itemDoubleClicked = pyqtSignal(str)
    selectionChanged = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
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
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll.setWidget(self.grid_container)
        layout.addWidget(self.scroll)

        self.cards = {}               # path -> CardWidget
        self.selected_paths = set()
        self.last_clicked_index = -1
        self.path_list = []

        self.grid_container.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.grid_container and event.type() == QEvent.Type.Resize:
            self._reorganize_grid()
        return super().eventFilter(obj, event)

    def _reorganize_grid(self):
        if not self.cards:
            return

        viewport_width = self.scroll.viewport().width()
        spacing = self.grid_layout.horizontalSpacing()
        card_width = CardWidget.THUMB_HEIGHT + 40

        cols = max(1, (viewport_width + spacing) // (card_width + spacing))

        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        for i, path in enumerate(self.path_list):
            card = self.cards[path]
            self.grid_layout.addWidget(card, i // cols, i % cols)

        self.grid_layout.activate()

    def add_item(self, path, name, color_label=""):
        if path in self.cards:
            return
        card = CardWidget(path, name, color_label)
        card.clicked.connect(self._handle_click)
        card.doubleClicked.connect(self.itemDoubleClicked.emit)
        self.cards[path] = card
        self.path_list.append(path)
        self._reorganize_grid()

    def _handle_click(self, path, modifiers):
        new_selection = set()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            new_selection = self.selected_paths.copy()
            if path in new_selection:
                new_selection.remove(path)
            else:
                new_selection.add(path)
            self.last_clicked_index = self.path_list.index(path)

        elif modifiers & Qt.KeyboardModifier.ShiftModifier and self.last_clicked_index != -1:
            current_index = self.path_list.index(path)
            start = min(self.last_clicked_index, current_index)
            end = max(self.last_clicked_index, current_index)
            new_selection = set(self.path_list[start:end+1])

        else:
            new_selection = {path}
            self.last_clicked_index = self.path_list.index(path)

        self.set_selection(new_selection)

        if len(new_selection) == 1:
            self.itemClicked.emit(path)

    def set_selection(self, paths):
        if not isinstance(paths, set):
            paths = set(paths)

        for p, card in self.cards.items():
            card.set_selected(p in paths)

        self.selected_paths = paths
        self.selectionChanged.emit(list(paths))

    def clear_selection(self):
        self.set_selection(set())

    def set_thumbnail(self, path, pixmap, color_label=""):
        if path in self.cards:
            self.cards[path].set_color_label(color_label)
            self.cards[path].set_thumbnail(pixmap)

    def clear(self):
        for card in self.cards.values():
            card.deleteLater()
        self.cards.clear()
        self.path_list.clear()
        self.selected_paths.clear()
        self.last_clicked_index = -1
        self._reorganize_grid()

    def set_on_clicked(self, callback):
        self.itemClicked.connect(callback)

    def set_on_double_clicked(self, callback):
        self.itemDoubleClicked.connect(callback)

    def get_selected_paths(self):
        return list(self.selected_paths)