"""
Left panel – Hierarchical Folder Tree.
FIXED: Inline renaming (F2 or double-click style).
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QMenu, QMessageBox, QAbstractItemView, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

class HierarchyTree(QTreeWidget):
    """Custom TreeWidget that auto-expands the target folder upon drop."""
    def dropEvent(self, event):
        target_item = self.itemAt(event.position().toPoint())
        super().dropEvent(event)
        if target_item:
            target_item.setExpanded(True)

class LeftPanel(QWidget):
    folder_renamed = pyqtSignal(str, str) 
    folder_deleted = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(220)
        self.setMaximumWidth(450)
        
        # Block signals during internal updates to prevent accidental triggers
        self._is_populating = False 

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 10, 20)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        lbl = QLabel("FOLDERS")
        lbl.setObjectName("SubHeader")
        header_layout.addWidget(lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Toolbar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        
        self.btn_add = QPushButton()
        self.btn_add.setIcon(qta.icon('fa5s.plus', color='#198754'))
        self.btn_add.setToolTip("Create New Folder")
        self.btn_add.setFixedSize(28, 28)
        self.btn_add.clicked.connect(self._add_folder_btn) 
        
        self.btn_del = QPushButton()
        self.btn_del.setIcon(qta.icon('fa5s.minus', color='#dc3545'))
        self.btn_del.setToolTip("Delete Selected Folder")
        self.btn_del.setFixedSize(28, 28)
        self.btn_del.clicked.connect(self._delete_folder_btn)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_del)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tree
        self.tree = HierarchyTree()
        self.tree.setHeaderLabels(["Folder", "#"]) 
        
        # Columns
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.tree.setColumnWidth(1, 45)
        self.tree.header().setStretchLastSection(False) 

        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        
        self.tree.setIndentation(20)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)

        layout.addWidget(self.tree)

        # Signals
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        # --- NEW: Detect Inline Edit Changes ---
        self.tree.itemChanged.connect(self._on_item_changed)

    def populate(self, plan):
        self._is_populating = True # Prevent itemChanged signals during load
        self.tree.clear()
        
        for category in sorted(plan.keys()):
            files = plan[category]
            item = QTreeWidgetItem(self.tree)
            item.setText(0, category)
            item.setText(1, str(len(files)))
            item.setData(0, Qt.ItemDataRole.UserRole, category) # Store original name
            item.setIcon(0, qta.icon('fa5s.folder', color='#FFC107'))
            item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
            
            # Allow editing
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

        self._is_populating = False

    def _on_item_changed(self, item, column):
        """Called when user finishes editing the folder name."""
        if self._is_populating: return
        if column != 0: return # Only care about folder name change

        new_name = item.text(0).strip()
        old_name = item.data(0, Qt.ItemDataRole.UserRole)

        # If name didn't change or is empty, ignore (or revert)
        if not new_name or new_name == old_name:
            return

        # Emit signal to Main Window to update data structure
        # Main Window will call populate() again, refreshing the tree
        self.folder_renamed.emit(old_name, new_name)

    # --- Actions ---
    def _add_folder_btn(self):
        # Create a placeholder item and edit it immediately
        item = QTreeWidgetItem(self.tree)
        item.setText(0, "New Folder")
        item.setText(1, "0")
        item.setIcon(0, qta.icon('fa5s.folder', color='#FFC107'))
        item.setData(0, Qt.ItemDataRole.UserRole, "New Folder")
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.tree.editItem(item, 0) # Start typing immediately

    def _delete_folder_btn(self):
        self._delete_folder(self.tree.currentItem())

    def _show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu()
        add_action = menu.addAction(qta.icon('fa5s.plus'), "New Subfolder")
        
        rename_action = None
        delete_action = None
        
        if item:
            self.tree.setCurrentItem(item)
            menu.addSeparator()
            rename_action = menu.addAction(qta.icon('fa5s.pen'), "Rename")
            delete_action = menu.addAction(qta.icon('fa5s.trash'), "Delete")

        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        
        if action == add_action:
            self._add_folder_btn()
        elif action == rename_action and item:
            self.tree.editItem(item, 0) # Trigger inline edit
        elif action == delete_action and item:
            self._delete_folder(item)

    def _delete_folder(self, item):
        if item is None: return
        try:
            folder_name = item.text(0)
        except RuntimeError: return 
        
        reply = QMessageBox.question(
            self, "Delete", 
            f"Delete folder '{folder_name}'?\n\nFiles will be moved to 'Uncategorized'.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.folder_deleted.emit(folder_name)
            
    # API helpers
    def current_category(self) -> str:
        item = self.tree.currentItem()
        return item.text(0) if item else None

    def set_on_item_clicked(self, callback):
        self.tree.itemClicked.connect(callback)

    def select_first(self):
        if self.tree.topLevelItemCount() > 0:
            item = self.tree.topLevelItem(0)
            self.tree.setCurrentItem(item)
            return item
        return None
    
    def clear(self): self.tree.clear()