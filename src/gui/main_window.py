"""
src/gui/main_window.py
Professional GUI with portable catalog system.
- Shared .iocat files via cloud sync
- Persistent tags and custom filenames
- Instant search by tag or filename
- Multi‑selection in gallery (Ctrl/Shift)
- Color label overlays on thumbnails
- Auto‑load catalog on open
"""
import sys
from pathlib import Path
from collections import defaultdict

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QMessageBox,
    QProgressBar, QFileDialog, QDockWidget, QLabel, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QAction, QKeySequence
import qtawesome as qta
import qdarktheme

from src.config import Config
from src.app import ImageOrganizerApp
from src.gui.styles import STYLESHEET
from src.gui.toolbar import Toolbar
from src.gui.panels.left_panel import LeftPanel
from src.gui.panels.middle_panel import MiddlePanel
from src.gui.panels.right_panel import RightPanel
from src.gui.panels.log_panel import LogPanel
from src.gui.workers import ScanWorker, ThumbnailLoader
from src.gui.preview_popup import PreviewPopup
from src.gui.settings_dialog import SettingsDialog
from src.gui.splash_screen import SplashScreen 
from src.logic.history import HistoryManager, UpdateMetadataCommand
from src.logic.catalog import ImageCatalog

class ImageOrganizerGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config = Config()
        qdarktheme.setup_theme(self.config.theme)

        self.setWindowTitle("Image Organizer Pro")
        self.setWindowIcon(qta.icon('fa5s.images', color='#0d6efd'))

        # SAFE DEFAULT SIZE
        self.resize(1400, 900)

        self.app = ImageOrganizerApp(self.config)
        
        # Splash screen
        self.splash = SplashScreen()
        self.splash.show()

        # Connect model loading signals
        self.app.tagger.load_progress.connect(self.splash.update_progress)
        self.app.tagger.model_ready.connect(self._on_model_ready)
        self.app.tagger.model_error.connect(self._on_model_error)
        
        self.history = HistoryManager()

        # Catalog system
        self.catalog: ImageCatalog = None
        self.catalog_path: Path = None
        self.image_root: Path = None

        self.current_plan = {}
        self.current_folder_name = None
        self.scan_thread = None
        self.thumbnail_loader = None

        self._setup_ui()
        self._setup_connections()
        self._load_saved_destination()
        self._restore_state()

        # Load last catalog on startup
        if self.config.last_catalog:
            try:
                p = Path(self.config.last_catalog)
                if p.exists():
                    self.catalog = ImageCatalog()
                    if self.catalog.load(p):
                        self.catalog_path = p
                        self.image_root = self.catalog.base_dir
                        self._update_window_title()
                        self.log_panel.log(f"Loaded catalog: {self.catalog_path.name}", "info")
                        # Auto‑load plan from catalog if root exists
                        if self.image_root and self.image_root.exists():
                            self.current_plan = self._build_plan_from_catalog()
                            self.left_panel.populate(self.current_plan)
                            self.left_panel.select_first()
            except Exception as e:
                self.log_panel.log(f"Failed to load last catalog: {e}", "error")

        # Only center if we didn't restore a position
        if not self.config.window_geometry:
            self.center()

        self.setFont(QFont("Segoe UI", 10))

    # ----------------------------------------------------------------------
    # UI Setup
    # ----------------------------------------------------------------------
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = Toolbar(self.config)
        layout.addWidget(self.toolbar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(2)
        layout.addWidget(self.splitter, 1)

        self.left_panel = LeftPanel()
        self.mid_panel = MiddlePanel()
        self.right_panel = RightPanel()

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.mid_panel)
        self.splitter.addWidget(self.right_panel)

        # Default sizes
        self.splitter.setSizes([280, 820, 380])
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(2, False)

        # Force gallery reflow when splitter moves
        self.splitter.splitterMoved.connect(self.mid_panel._reorganize_grid)

        self.dock_log = QDockWidget("Activity Log", self)
        self.dock_log.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.log_panel = LogPanel()
        self.dock_log.setWidget(self.log_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_log)

        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(400)
        self.progress_bar.setTextVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        padding = QWidget()
        padding.setFixedWidth(20)
        self.status_bar.addPermanentWidget(padding)

        self._create_menubar()
        self.setStyleSheet(self.styleSheet() + STYLESHEET)

        # Log startup messages
        self.log_panel.log("Application Started", "info")
        self.log_panel.log("AI Tagger (EfficientNet) ready", "success")

    # ----------------------------------------------------------------------
    # Catalog Operations
    # ----------------------------------------------------------------------
    def _build_plan_from_catalog(self):
        """Create a plan dict from the current catalog, grouping by folder."""
        if not self.catalog or not self.image_root:
            return {}
        plan = defaultdict(list)
        for rel_path, meta in self.catalog.images.items():
            abs_path = self.image_root / rel_path
            folder = rel_path.parent if rel_path.parent != '.' else "Root"
            file_data = {
                'original_path': str(abs_path),
                'filename': abs_path.name,
                'new_filename': meta.get('filename', abs_path.stem),
                'tags': meta.get('tags', []),
                'rating': meta.get('rating', 0),
                'color_label': meta.get('color_label', ''),
                'proposed_folder': str(folder)
            }
            plan[str(folder)].append(file_data)
        return dict(plan)

    def _new_catalog(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Create New Catalog",
            str(Path.home() / "MyImageCatalog.iocat"),
            "Image Catalog (*.iocat);;All Files (*)"
        )
        if path:
            self.catalog = ImageCatalog()
            self.catalog.create_new(Path(path))
            self.catalog_path = Path(path)
            self.config.last_catalog = path
            self.config.save({"last_catalog": path})
            self.log_panel.log(f"Created new catalog: {path}", "success")
            self._set_image_root()

    def _open_catalog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Catalog",
            self.config.last_catalog or str(Path.home()),
            "Image Catalog (*.iocat);;All Files (*)"
        )
        if path:
            self.catalog = ImageCatalog()
            if self.catalog.load(Path(path)):
                self.catalog_path = Path(path)
                self.config.last_catalog = path
                self.config.save({"last_catalog": path})
                self.image_root = self.catalog.base_dir
                self._update_window_title()
                self.log_panel.log(f"Opened catalog: {path}", "success")

                # If image root is set and exists, load the plan from catalog
                if self.image_root and self.image_root.exists():
                    self.current_plan = self._build_plan_from_catalog()
                    self.left_panel.populate(self.current_plan)
                    self.left_panel.select_first()
                    count = sum(len(v) for v in self.current_plan.values())
                    self.status_bar.showMessage(f"Catalog loaded: {count} items")
                else:
                    QMessageBox.information(self, "Set Image Root",
                                            "Please set the image root folder to view images.")
            else:
                QMessageBox.critical(self, "Error", "Failed to load catalog.")

    def _save_catalog(self):
        if self.catalog:
            if self.catalog.save():
                self.log_panel.log("Catalog saved.", "success")
            else:
                self.log_panel.log("Failed to save catalog.", "error")
        else:
            self._open_catalog()  # fallback

    def _set_image_root(self):
        if not self.catalog:
            QMessageBox.warning(self, "No Catalog", "Please open or create a catalog first.")
            return
        folder = QFileDialog.getExistingDirectory(
            self, "Select Image Root Folder (where all your images are stored)",
            str(self.image_root) if self.image_root else str(Path.home())
        )
        if folder:
            self.image_root = Path(folder)
            self.catalog.set_base_dir(self.image_root)
            self.catalog.save()
            self.log_panel.log(f"Image root set to: {folder}", "success")
            self._update_window_title()
            # Reload plan from catalog if we have one
            if self.catalog:
                self.current_plan = self._build_plan_from_catalog()
                self.left_panel.populate(self.current_plan)
                self.left_panel.select_first()

    def _update_window_title(self):
        title = "Image Organizer Pro"
        if self.catalog_path:
            title += f" - {self.catalog_path.stem}"
        if self.image_root:
            title += f" [{self.image_root.name}]"
        self.setWindowTitle(title)

    # ----------------------------------------------------------------------
    # State Saving
    # ----------------------------------------------------------------------
    def closeEvent(self, event):
        state = {
            "geometry": self.saveGeometry().toHex().data().decode(),
            "splitter": self.splitter.saveState().toHex().data().decode()
        }
        self.config.save(state)
        super().closeEvent(event)

    def _restore_state(self):
        if self.config.window_geometry:
            self.restoreGeometry(self.config.window_geometry)
        if self.config.splitter_state:
            self.splitter.restoreState(self.config.splitter_state)

    # ----------------------------------------------------------------------
    # Scanning
    # ----------------------------------------------------------------------
    def _start_scan(self):
        
        if self.app.tagger.model is None:
            QMessageBox.information(self, "AI Not Ready", 
                                    "The AI model is still loading. Please wait.")
            return
        if not self.catalog:
            reply = QMessageBox.question(
                self, "No Catalog",
                "You need to open or create a catalog before scanning.\n\nOpen one now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_catalog()
            return

        path = self.toolbar.get_source()
        if not path:
            return
        self.log_panel.log(f"Starting scan on: {path}", "cmd")
        self.toolbar.set_scan_state(True)
        self.toolbar.set_commit_enabled(False)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Initializing Scan...")
        self.left_panel.clear()
        self.mid_panel.clear()

        self.scan_thread = ScanWorker(self.app, path, group_by="tag")
        self.scan_thread.progress.connect(self.progress_bar.setValue)
        self.scan_thread.status_update.connect(self.status_bar.showMessage)
        self.scan_thread.finished.connect(self._on_scan_finished)
        self.scan_thread.error.connect(self._on_scan_error)
        self.scan_thread.start()

    def _on_scan_finished(self, plan):
        # Merge catalog metadata into the plan
        if self.catalog and self.image_root:
            for category, images in plan.items():
                for img in images:
                    abs_path = Path(img['original_path'])
                    meta = self.catalog.get_image_metadata(abs_path)
                    # Prefer plan's filename if set, else from catalog
                    if 'new_filename' not in img or not img['new_filename']:
                        img['new_filename'] = meta['filename']
                    # Merge tags
                    plan_tags = set(img.get('tags', []))
                    catalog_tags = set(meta['tags'])
                    img['tags'] = list(plan_tags | catalog_tags)
                    # Include rating and color label from catalog
                    img['rating'] = meta.get('rating', 0)
                    img['color_label'] = meta.get('color_label', '')

            # Save merged tags back to catalog
            for category, images in plan.items():
                for img in images:
                    abs_path = Path(img['original_path'])
                    self.catalog.add_or_update_image(
                        abs_path,
                        img['new_filename'],
                        img['tags'],
                        img.get('rating', 0),
                        img.get('color_label', '')
                    )
            self.catalog.save()
            self.log_panel.log("Catalog updated with AI tags.", "info")

        self.current_plan = plan
        self.progress_bar.setValue(0)
        self.toolbar.set_scan_state(False)
        self.toolbar.set_commit_enabled(True)
        count = sum(len(v) for v in plan.values())
        self.status_bar.showMessage(f"Done scanning. Found {count} items.")
        self.log_panel.log(f"Scan complete. Found {count} items.", "success")
        self.left_panel.populate(plan)
        self.left_panel.select_first()

    def _on_scan_error(self, err_msg):
        self.toolbar.set_scan_state(False)
        self.log_panel.log(f"Scan Error: {err_msg}", "error")
        self.status_bar.showMessage("Scan Failed.")

    def _cancel_scan(self):
        if self.scan_thread:
            self.scan_thread.stop()

    def _toggle_scan_stop(self):
        if not self.toolbar.is_scanning():
            self._start_scan()
        else:
            self._cancel_scan()

    # ----------------------------------------------------------------------
    # Folder & Image Selection
    # ----------------------------------------------------------------------
    def _on_folder_select(self, item, col):
        category = self.left_panel.current_category()
        if not category:
            return
        self.current_folder_name = category
        files = self.current_plan.get(category, [])
        self.mid_panel.clear()
        items_to_load = []
        for f in files:
            path = f['original_path']
            display = f.get('new_filename', Path(path).stem)
            self.mid_panel.add_item(path, display, f.get('color_label', ''))
            items_to_load.append((path, path))

        if self.thumbnail_loader and self.thumbnail_loader.isRunning():
            self.thumbnail_loader.terminate()
        self.thumbnail_loader = ThumbnailLoader(items_to_load)
        self.thumbnail_loader.thumbnail_ready.connect(self._set_thumbnail)
        self.thumbnail_loader.start()
        self.status_bar.showMessage(f"Viewing: {category} ({len(files)} items)")

    def _set_thumbnail(self, path, qimage):
        if not qimage.isNull():
            pixmap = QPixmap.fromImage(qimage)
            # Find the color label for this path
            color_label = ""
            if self.current_folder_name and self.current_plan:
                for img in self.current_plan.get(self.current_folder_name, []):
                    if img['original_path'] == path:
                        color_label = img.get('color_label', '')
                        break
            self.mid_panel.set_thumbnail(path, pixmap, color_label)

    def _on_image_select(self, path):
        """Single image selected (from click without modifiers)."""
        meta = None
        for m in self.current_plan.get(self.current_folder_name, []):
            if m['original_path'] == path:
                meta = m
                break
        if meta:
            self.right_panel.set_metadata(
                meta.get('new_filename', ''),
                meta.get('tags', []),
                meta.get('rating', 0),
                meta.get('color_label', '')
            )
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.right_panel.preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.right_panel.set_preview_pixmap(scaled)

    def _on_image_double_click(self, path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            popup = PreviewPopup(pixmap, self)
            popup.show()
            popup.raise_()
            popup.activateWindow()

    # ----------------------------------------------------------------------
    # Multi‑selection handling
    # ----------------------------------------------------------------------
    def _on_selection_changed(self, paths):
        """Called when gallery selection changes (single or multiple)."""
        if len(paths) == 1:
            self._on_image_select(paths[0])
        elif len(paths) > 1:
            # Multiple items selected – show count and disable editing
            self.right_panel.clear_preview()
            self.right_panel.set_metadata(f"{len(paths)} items selected", [], 0, '')
            self.status_bar.showMessage(f"{len(paths)} items selected")
        else:
            # No selection
            self.right_panel.clear_preview()
            self.status_bar.showMessage("No selection")

    # ----------------------------------------------------------------------
    # Metadata & Catalog Save
    # ----------------------------------------------------------------------
    def _update_local_meta(self):
        """Update metadata for the currently selected image (only when exactly one is selected)."""
        selected = self.mid_panel.get_selected_paths()
        if len(selected) != 1:
            return
        current_path = selected[0]
        if not self.current_folder_name:
            return

        new_data = self.right_panel.get_metadata()
        files = self.current_plan.get(self.current_folder_name, [])
        target_file = next((f for f in files if f['original_path'] == current_path), None)
        if target_file:
            old_snapshot = {
                'new_filename': target_file['new_filename'],
                'tags': list(target_file['tags']),
                'rating': target_file.get('rating', 0),
                'color_label': target_file.get('color_label', '')
            }
            new_snapshot = {
                'new_filename': new_data['filename'],
                'tags': list(new_data['tags']),
                'rating': new_data.get('rating', 0),
                'color_label': new_data.get('color_label', '')
            }
            cmd = UpdateMetadataCommand(
                files, current_path, old_snapshot, new_snapshot, self._ui_refresh_file
            )
            self.history.push(cmd)

            target_file['new_filename'] = new_data['filename']
            target_file['tags'] = new_data['tags']
            target_file['rating'] = new_data.get('rating', 0)
            target_file['color_label'] = new_data.get('color_label', '')

            # Update thumbnail color label
            if current_path in self.mid_panel.cards:
                self.mid_panel.cards[current_path].set_color_label(target_file['color_label'])

            # Save to catalog
            if self.catalog and self.image_root:
                abs_path = Path(target_file['original_path'])
                self.catalog.add_or_update_image(
                    abs_path,
                    new_data['filename'],
                    new_data['tags'],
                    new_data.get('rating', 0),
                    new_data.get('color_label', '')
                )
                self.catalog.save()
                self.log_panel.log(f"Saved to catalog: {target_file['filename']}", "cmd")
                self.status_bar.showMessage("✅ Catalog updated.", 3000)
            else:
                self.status_bar.showMessage("✅ Metadata updated (catalog not active).", 3000)

    def _ui_refresh_file(self, file_path):
        """Called after undo/redo to refresh UI for the affected file."""
        selected = self.mid_panel.get_selected_paths()
        if len(selected) == 1 and selected[0] == file_path:
            files = self.current_plan.get(self.current_folder_name, [])
            meta = next((f for f in files if f['original_path'] == file_path), None)
            if meta:
                self.right_panel.set_metadata(
                    meta['new_filename'],
                    meta['tags'],
                    meta.get('rating', 0),
                    meta.get('color_label', '')
                )
        self.log_panel.log(f"Restored state for {Path(file_path).name}", "success")

    # ----------------------------------------------------------------------
    # Search
    # ----------------------------------------------------------------------
    def _filter_by_search(self, text):
        """Filter left folder tree and middle gallery based on search query."""
        if not self.catalog or not self.current_plan:
            return

        query = text.strip()
        if not query:
            # Reset: show all folders and all images in current folder
            self.left_panel.populate(self.current_plan)
            if self.current_folder_name:
                self._on_folder_select(None, 0)
            return

        # Get matching relative paths from catalog
        matching_rel_paths = set(self.catalog.search(query))
        # Convert to absolute paths based on image_root
        matching_abs_paths = set()
        for rel in matching_rel_paths:
            if self.image_root:
                matching_abs_paths.add(str(self.image_root / rel))
            else:
                matching_abs_paths.add(rel)

        # Filter the current plan: only keep images that match
        filtered_plan = {}
        for category, images in self.current_plan.items():
            filtered_images = [
                img for img in images
                if img['original_path'] in matching_abs_paths
            ]
            if filtered_images:
                filtered_plan[category] = filtered_images

        # Update left panel with filtered categories
        self.left_panel.populate(filtered_plan)

        # If current folder is still in filtered plan, show its filtered images
        if self.current_folder_name in filtered_plan:
            self._on_folder_select(None, 0)
        else:
            self.mid_panel.clear()
            self.right_panel.clear_preview()

    # ----------------------------------------------------------------------
    # Commit (copy/move to destination)
    # ----------------------------------------------------------------------
    def _commit_changes(self):
        if not self.current_plan:
            return
        self.log_panel.log("Starting Commit...", "cmd")
        try:
            stats = self.app.execute_plan(self.current_plan)
            self.log_panel.log(f"Commit Done. Processed: {stats['processed']}", "success")
            QMessageBox.information(self, "Done", f"Processed: {stats['processed']}")
        except Exception as e:
            self.log_panel.log(f"Commit Failed: {e}", "error")

    # ----------------------------------------------------------------------
    # Folder Management (Rename / Delete)
    # ----------------------------------------------------------------------
    def _on_folder_deleted(self, folder_name):
        if folder_name not in self.current_plan:
            return
        orphaned = self.current_plan.pop(folder_name)
        if orphaned:
            target = "Uncategorized"
            for img in orphaned:
                img['proposed_folder'] = target
            if target in self.current_plan:
                self.current_plan[target].extend(orphaned)
            else:
                self.current_plan[target] = orphaned
            self.log_panel.log(
                f"Deleted folder '{folder_name}'. Moved {len(orphaned)} files to {target}.",
                "warning"
            )
            self.left_panel.populate(self.current_plan)

    def _on_folder_renamed(self, old_name, new_name):
        if old_name not in self.current_plan:
            return
        images = self.current_plan.pop(old_name)
        for img in images:
            img['proposed_folder'] = new_name
        if new_name in self.current_plan:
            self.current_plan[new_name].extend(images)
        else:
            self.current_plan[new_name] = images
        self.left_panel.populate(self.current_plan)
        items = self.left_panel.tree.findItems(
            new_name,
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchCaseSensitive,
            0
        )
        if items:
            self.left_panel.tree.setCurrentItem(items[0])
            self._on_folder_select(items[0], 0)
        self.log_panel.log(f"Renamed folder '{old_name}' to '{new_name}'", "info")

    # ----------------------------------------------------------------------
    # Undo / Redo
    # ----------------------------------------------------------------------
    def _undo(self):
        msg = self.history.undo()
        if msg:
            self.log_panel.log(f"Undo: {msg}", "warning")
            self.status_bar.showMessage("Undo successful", 2000)

    def _redo(self):
        msg = self.history.redo()
        if msg:
            self.log_panel.log(f"Redo: {msg}", "info")
            self.status_bar.showMessage("Redo successful", 2000)

    # ----------------------------------------------------------------------
    # Menu Bar
    # ----------------------------------------------------------------------
    def _create_menubar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        # Catalog actions first
        new_catalog = QAction(qta.icon('fa5s.file'), "New Catalog...", self)
        new_catalog.setShortcut("Ctrl+N")
        new_catalog.triggered.connect(self._new_catalog)
        file_menu.addAction(new_catalog)

        open_catalog = QAction(qta.icon('fa5s.folder-open'), "Open Catalog...", self)
        open_catalog.setShortcut("Ctrl+O")
        open_catalog.triggered.connect(self._open_catalog)
        file_menu.addAction(open_catalog)

        save_catalog = QAction(qta.icon('fa5s.save'), "Save Catalog", self)
        save_catalog.setShortcut("Ctrl+S")
        save_catalog.triggered.connect(self._save_catalog)
        file_menu.addAction(save_catalog)

        file_menu.addSeparator()

        # Source / Destination
        open_src = QAction(qta.icon('fa5s.folder-open'), "Open Source...", self)
        open_src.setShortcut("Ctrl+Shift+O")
        open_src.triggered.connect(self._browse_source_from_menu)
        file_menu.addAction(open_src)

        open_dest = QAction(qta.icon('fa5s.folder'), "Set Destination...", self)
        open_dest.setShortcut("Ctrl+Shift+D")
        open_dest.triggered.connect(self._browse_dest_from_menu)
        file_menu.addAction(open_dest)

        file_menu.addSeparator()

        set_root = QAction(qta.icon('fa5s.home'), "Set Image Root...", self)
        set_root.triggered.connect(self._set_image_root)
        file_menu.addAction(set_root)

        file_menu.addSeparator()

        pref = QAction(qta.icon('fa5s.cog'), "Preferences...", self)
        pref.setShortcut("Ctrl+P")
        pref.triggered.connect(self._show_settings)
        file_menu.addAction(pref)

        file_menu.addSeparator()
        exit_act = QAction(qta.icon('fa5s.power-off', color='#dc3545'), "Exit", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        self.undo_act = QAction(qta.icon('fa5s.undo'), "Undo", self)
        self.undo_act.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_act.triggered.connect(self._undo)
        edit_menu.addAction(self.undo_act)

        self.redo_act = QAction(qta.icon('fa5s.redo'), "Redo", self)
        self.redo_act.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_act.triggered.connect(self._redo)
        edit_menu.addAction(self.redo_act)

        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.dock_log.toggleViewAction())

        refresh = QAction(qta.icon('fa5s.sync'), "Refresh / Rescan", self)
        refresh.setShortcut("F5")
        refresh.triggered.connect(self._start_scan)
        view_menu.addAction(refresh)

    # ----------------------------------------------------------------------
    # Utility Methods
    # ----------------------------------------------------------------------
    def center(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _load_saved_destination(self):
        data = self.config.load()
        dest = data.get("destination", self.config.default_dest)
        self.toolbar.set_destination(dest)

    def _set_source(self, folder):
        self.toolbar.set_source(folder)

    def _set_destination(self, folder):
        self.toolbar.set_destination(folder)

    def _browse_source_from_menu(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Source", self.toolbar.get_source()
        )
        if folder:
            self._set_source(folder)

    def _browse_dest_from_menu(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Destination", self.toolbar.get_destination()
        )
        if folder:
            self._set_destination(folder)

    def _show_settings(self):
        dlg = SettingsDialog(self.config, self)
        dlg.settings_changed.connect(self._on_settings_changed)
        dlg.exec()

    def _on_settings_changed(self):
        self.app.update_ai_threshold(self.config.ai_threshold)
        self.log_panel.log(f"AI threshold set to {self.config.ai_threshold}", "info")
        reply = QMessageBox.question(
            self, "Rescan?",
            "AI threshold changed. Would you like to rescan the current source to apply new tags?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._start_scan()

    # ----------------------------------------------------------------------
    # Connections
    # ----------------------------------------------------------------------
    def _setup_connections(self):
        self.left_panel.folder_renamed.connect(self._on_folder_renamed)
        self.left_panel.folder_deleted.connect(self._on_folder_deleted)
        self.toolbar.on_browse_source(self._set_source)
        self.toolbar.on_browse_dest(self._set_destination)
        self.toolbar.on_scan_toggle(self._toggle_scan_stop)
        self.toolbar.on_commit(self._commit_changes)
        self.left_panel.set_on_item_clicked(self._on_folder_select)
        self.mid_panel.set_on_clicked(self._on_image_select)
        self.mid_panel.set_on_double_clicked(self._on_image_double_click)
        self.mid_panel.selectionChanged.connect(self._on_selection_changed)
        self.right_panel.tags_updated.connect(self._update_local_meta)
        self.right_panel.rating_changed.connect(self._update_local_meta)
        self.right_panel.color_label_changed.connect(self._update_local_meta)

    # ----------------------------------------------------------------------
    # Model Loader
    # ----------------------------------------------------------------------
    def _on_model_ready(self):
        self.splash.close()
        self.log_panel.log("AI Tagger (EfficientNet) ready", "success")

    def _on_model_error(self, error):
        self.splash.close()
        self.log_panel.log(f"AI Tagger failed to load: {error}", "error")

    # ----------------------------------------------------------------------
    # Placeholders
    # ----------------------------------------------------------------------
    def _show_ai_fix(self): pass
    def _show_about(self): pass