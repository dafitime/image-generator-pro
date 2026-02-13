"""
src/gui/panels/log_panel.py
Dockable Log Viewer. Shows actions in real-time.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QDateTime
import qtawesome as qta

class LogPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header = QHBoxLayout()
        lbl = QLabel("ACTIVITY LOG")
        lbl.setObjectName("SubHeader")
        header.addWidget(lbl)
        
        btn_clear = QPushButton()
        btn_clear.setIcon(qta.icon('fa5s.trash-alt', color='#6c757d'))
        btn_clear.setFlat(True)
        btn_clear.setToolTip("Clear Log")
        btn_clear.clicked.connect(self.clear_log)
        header.addWidget(btn_clear)
        
        header.addStretch()
        layout.addLayout(header)

        # Log Area (Read Only)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("""
            QTextEdit {
                border: 1px solid palette(mid);
                border-radius: 4px;
                font-family: "Consolas", monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.text_area)

    def log(self, message, level="info"):
        """
        Levels: info, success, error, warning
        """
        timestamp = QDateTime.currentDateTime().toString("HH:mm:ss")
        
        color = "palette(text)" # Default
        if level == "success": color = "#198754"
        elif level == "error": color = "#dc3545"
        elif level == "warning": color = "#ffc107"
        elif level == "cmd": color = "#0d6efd"

        # HTML formatting for color
        html = f'<span style="color:#888;">[{timestamp}]</span> <span style="color:{color};">{message}</span>'
        self.text_area.append(html)

    def clear_log(self):
        self.text_area.clear()