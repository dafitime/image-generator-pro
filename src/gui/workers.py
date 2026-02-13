"""
src/gui/workers.py
Background workers.
FIXED: Uses QImage for thread-safety + Path normalization.
"""
import threading
import os
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage

class ThumbnailLoader(QThread):
    """
    Generates thumbnails using QImage (Thread-Safe).
    Emits (path_id, QImage).
    """
    thumbnail_ready = pyqtSignal(str, QImage)

    def __init__(self, items):
        super().__init__()
        self.items = items  # list of (path, path)

    def run(self):
        for index, path in self.items:
            try:
                # Normalize path for Windows
                clean_path = os.path.normpath(str(path))
                
                # Load as QImage (Safe for threads)
                image = QImage(clean_path)
                
                if not image.isNull():
                    # Scale efficiently in the background
                    thumb = image.scaledToHeight(
                        200,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.thumbnail_ready.emit(index, thumb)
                else:
                    print(f"Failed to load image: {clean_path}")
            except Exception as e:
                print(f"Thumbnail error for {path}: {e}")

class ScanWorker(QThread):
    """Scans folder and reports detailed progress."""
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str) 
    error = pyqtSignal(str)

    def __init__(self, app_backend, path, group_by):
        super().__init__()
        self.app = app_backend
        self.path = path
        self.group_by = group_by
        self._stop_event = threading.Event()

    def run(self):
        try:
            def progress_callback(current, total, filename):
                if total > 0:
                    percent = int((current / total) * 100)
                    self.progress.emit(percent)
                    self.status_update.emit(f"Scanning {current}/{total}: {filename}")

            plan = self.app.preview_organization(
                self.path, recursive=True, group_by=self.group_by,
                progress_callback=progress_callback, stop_event=self._stop_event
            )
            self.finished.emit(plan)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._stop_event.set()