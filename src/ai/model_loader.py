"""
src/ai/model_loader.py
Background model loader with progress simulation.
"""
import threading
from PyQt6.QtCore import QObject, pyqtSignal

class ModelLoader(QObject):
    finished = pyqtSignal(object)   # emits the loaded model
    error = pyqtSignal(str)
    progress = pyqtSignal(int)      # 0-100 (simulated)

    def __init__(self, device=None):
        super().__init__()
        self.device = device
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._load)
        self._thread.daemon = True
        self._thread.start()

    def _load(self):
        try:
            self.progress.emit(10)
            import torch
            from torchvision import models

            self.progress.emit(30)
            # This triggers download if not cached
            model = models.efficientnet_b7(weights='DEFAULT')
            self.progress.emit(70)

            model.eval()
            device = self.device if self.device else ("cuda" if torch.cuda.is_available() else "cpu")
            model.to(device)

            self.progress.emit(100)
            self.finished.emit(model)
        except Exception as e:
            self.error.emit(str(e))