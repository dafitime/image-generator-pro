"""
src/gui/settings_dialog.py
Settings dialog with theme selector and AI confidence threshold.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QComboBox, QPushButton, QWidget, QGroupBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import qdarktheme

class SettingsDialog(QDialog):
    # Signal emitted when settings change (including threshold)
    settings_changed = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Theme selection
        theme_group = QGroupBox("Appearance")
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["auto", "dark", "light"])
        self.theme_combo.setCurrentText(self.config.theme)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # AI Confidence Threshold
        ai_group = QGroupBox("AI Tagging Sensitivity")
        ai_layout = QVBoxLayout()

        # Slider + spinbox for threshold
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Confidence threshold:"))
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 100)  # 0.00 to 1.00
        self.threshold_slider.setValue(int(self.config.ai_threshold * 100))
        self.threshold_slider.setTickInterval(5)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        threshold_layout.addWidget(self.threshold_slider)

        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.0, 1.0)
        self.threshold_spin.setSingleStep(0.05)
        self.threshold_spin.setValue(self.config.ai_threshold)
        threshold_layout.addWidget(self.threshold_spin)

        ai_layout.addLayout(threshold_layout)

        # Explanation label
        info_label = QLabel(
            "Lower values = more tags (may include less relevant ones).\n"
            "Higher values = fewer but more confident tags."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 11px;")
        ai_layout.addWidget(info_label)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # Connect slider and spinbox
        self.threshold_slider.valueChanged.connect(self._slider_to_spin)
        self.threshold_spin.valueChanged.connect(self._spin_to_slider)

    def _slider_to_spin(self, value):
        self.threshold_spin.setValue(value / 100.0)

    def _spin_to_slider(self, value):
        self.threshold_slider.setValue(int(value * 100))

    def accept(self):
        # Save settings
        self.config.theme = self.theme_combo.currentText()
        self.config.ai_threshold = self.threshold_spin.value()
        self.config.save({
            "theme": self.config.theme,
            "ai_threshold": self.config.ai_threshold
        })
        # Apply theme immediately
        qdarktheme.setup_theme(self.config.theme)
        # Emit signal so main window can update the tagger
        self.settings_changed.emit()
        super().accept()