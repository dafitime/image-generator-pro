"""
src/gui/widgets/tag_widget.py
Professional Tag Editor.
FIXED: Signal emits correctly (no argument).
"""
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QLineEdit, QLayout, QSizePolicy, QWidgetItem
)
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize

class TagChip(QWidget):
    removed = pyqtSignal(str)

    def __init__(self, text):
        super().__init__()
        self.text = text
        
        self.setStyleSheet("""
            QWidget {
                background-color: palette(button);
                border: 1px solid palette(mid);
                border-radius: 4px;
            }
            QLabel {
                color: palette(text);
                font-size: 12px;
                font-weight: 600;
                border: none;
                padding: 4px 0px 4px 8px;
                background: transparent;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: palette(text);
                opacity: 0.6;
                font-size: 16px;
                font-weight: bold;
                padding: 0px 8px 2px 0px;
                margin: 0;
            }
            QPushButton:hover {
                color: #dc3545;
                opacity: 1.0;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        lbl = QLabel(text)
        layout.addWidget(lbl)

        btn_close = QPushButton("×")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(lambda: self.removed.emit(self.text))
        layout.addWidget(btn_close)
        
        self.setFixedHeight(28)

class TagFlowLayout(QLayout):
    # ... (keep this class exactly as you have it) ...
    # No changes needed here
    def __init__(self, parent=None, margin=0, spacing=6):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.items = []

    def addItem(self, item): self.items.append(item)
    def count(self): return len(self.items)
    def itemAt(self, index): return self.items[index] if 0 <= index < len(self.items) else None
    
    def takeAt(self, index): 
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None
    
    def insertWidget(self, index, widget):
        widget.setParent(self.parentWidget())
        widget.show()
        item = QWidgetItem(widget)
        self.items.insert(index, item)
        self.invalidate() 

    def expandingDirections(self): return Qt.Orientation(0)
    def hasHeightForWidth(self): return True
    
    def heightForWidth(self, width): 
        return self._do_layout(QRect(0, 0, width, 0), False)
        
    def setGeometry(self, rect): 
        super().setGeometry(rect)
        self._do_layout(rect, True)

    def sizeHint(self): return self.minimumSize()
    
    def minimumSize(self): 
        size = QSize()
        for item in self.items: size = size.expandedTo(item.minimumSize())
        return size + QSize(20, 20)

    def _do_layout(self, rect, move):
        x, y, row_h = rect.x(), rect.y(), 0
        spacing = self.spacing()
        effective_width = rect.width()
        
        for item in self.items:
            wid = item.widget()
            if not wid: continue
            
            size = wid.sizeHint()
            w, h = size.width(), size.height()
            
            if x + w > rect.x() + effective_width and row_h > 0:
                x = rect.x()
                y += row_h + spacing
                row_h = 0
            
            if move: 
                item.setGeometry(QRect(QPoint(x, y), size))
            
            x += w + spacing
            row_h = max(row_h, h)
            
        return y + row_h - rect.y()

class TagEditor(QWidget):
    tags_changed = pyqtSignal()  # 🟢 NO ARGUMENT – emit without data

    def __init__(self):
        super().__init__()
        self.tags = []
        
        self.setStyleSheet("""
            TagEditor {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 4px;
            }
        """)
        
        self.flow = TagFlowLayout(self, margin=8, spacing=6)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Add tag...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: transparent; 
                border: none; 
                padding: 4px;
                color: palette(text);
            }
        """)
        self.input_field.setFixedWidth(80)
        self.input_field.returnPressed.connect(self._add_tag_from_input)
        
        self.flow.addWidget(self.input_field)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)

    def set_tags(self, tags):
        while self.flow.count() > 1:
            item = self.flow.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        self.tags = []
        for t in tags:
            self._create_chip(t)
        
        self.updateGeometry()

    def get_tags(self):
        return self.tags

    def _create_chip(self, text):
        if text in self.tags: return
        
        chip = TagChip(text)
        chip.removed.connect(self._remove_tag)
        
        self.flow.insertWidget(self.flow.count() - 1, chip)
        self.tags.append(text)
        self.updateGeometry()
        
    def _add_tag_from_input(self):
        text = self.input_field.text().strip()
        if text:
            self._create_chip(text)
            self.input_field.clear()
            self.input_field.setFocus()
            self.tags_changed.emit()  # 🟢 EMIT WITH NO ARGUMENTS

    def _remove_tag(self, text):
        for i in range(self.flow.count()):
            item = self.flow.itemAt(i)
            widget = item.widget()
            
            if isinstance(widget, TagChip) and widget.text == text:
                self.flow.takeAt(i)
                widget.deleteLater()
                self.tags.remove(text)
                self.flow.invalidate()
                self.updateGeometry()
                self.tags_changed.emit()  # 🟢 EMIT WITH NO ARGUMENTS
                break