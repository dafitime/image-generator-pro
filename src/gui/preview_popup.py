"""
Full‑screen image preview with zoom and pan.
- Mouse wheel to zoom in/out with limits
- Left drag to pan
- Double‑click or ESC to close
- Resizable window
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QWheelEvent, QPainter


class ZoomableGraphicsView(QGraphicsView):
    """QGraphicsView with mouse wheel zoom (clamped) and drag panning."""
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHints(
            self.renderHints() | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(self.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(self.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(self.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(self.Shape.NoFrame)

        self._min_scale = 0.2
        self._max_scale = 5.0

    def wheelEvent(self, event: QWheelEvent):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        old_factor = self.transform().m11()  # horizontal scale factor

        if event.angleDelta().y() > 0:
            new_factor = old_factor * zoom_in_factor
            if new_factor <= self._max_scale:
                self.scale(zoom_in_factor, zoom_in_factor)
        else:
            new_factor = old_factor * zoom_out_factor
            if new_factor >= self._min_scale:
                self.scale(zoom_out_factor, zoom_out_factor)


class PreviewPopup(QDialog):
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Preview")
        self.setWindowFlags(Qt.WindowType.Window)
        self.resize(900, 700)
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scene = QGraphicsScene()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        scene.addItem(self.pixmap_item)

        self.view = ZoomableGraphicsView(scene)
        layout.addWidget(self.view)

        # Center the image initially
        self.view.setSceneRect(QRectF(pixmap.rect()))
        self.view.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

        self.setModal(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.close()