from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QKeySequenceEdit, QMessageBox, QHeaderView
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QKeySequence

class ShortcutManager:
    """Manage keyboard shortcuts with customization"""
    
    DEFAULT_SHORTCUTS = {
        'file_open': {'key': 'Ctrl+O', 'description': 'Open image'},
        'file_save': {'key': 'Ctrl+S', 'description': 'Save image'},
        'file_save_as': {'key': 'Ctrl+Shift+S', 'description': 'Save as'},
        'file_export': {'key': 'Ctrl+E', 'description': 'Export'},
        'file_exit': {'key': 'Ctrl+Q', 'description': 'Exit'},
        
        'edit_undo': {'key': 'Ctrl+Z', 'description': 'Undo'},
        'edit_redo': {'key': 'Ctrl+Y', 'description': 'Redo'},
        'edit_reset': {'key': 'Ctrl+R', 'description': 'Reset'},
        
        'image_crop': {'key': 'Ctrl+Shift+C', 'description': 'Crop'},
        'image_resize': {'key': 'Ctrl+Shift+R', 'description': 'Resize'},
        'image_rotate_left': {'key': 'Ctrl+[', 'description': 'Rotate left'},
        'image_rotate_right': {'key': 'Ctrl+]', 'description': 'Rotate right'},
        'image_flip_h': {'key': 'Ctrl+H', 'description': 'Flip horizontal'},
        'image_flip_v': {'key': 'Ctrl+V', 'description': 'Flip vertical'},
        
        'view_compare': {'key': 'Ctrl+D', 'description': 'Compare before/after'},
        'view_zoom_in': {'key': 'Ctrl++', 'description': 'Zoom in'},
        'view_zoom_out': {'key': 'Ctrl+-', 'description': 'Zoom out'},
        'view_fit': {'key': 'Ctrl+0', 'description': 'Fit to window'},
        'view_actual': {'key': 'Ctrl+1', 'description': 'Actual size'},
        
        'ai_auto_enhance': {'key': 'Ctrl+A', 'description': 'Auto enhance'},
        'ai_denoise': {'key': 'Ctrl+N', 'description': 'Denoise'},
        'ai_super_res': {'key': 'Ctrl+U', 'description': 'Super resolution'},
        'ai_remove_bg': {'key': 'Ctrl+B', 'description': 'Remove background'},
        'ai_facial': {'key': 'Ctrl+F', 'description': 'Facial enhancement'},
        
        'layer_new': {'key': 'Ctrl+Shift+N', 'description': 'New layer'},
        'layer_duplicate': {'key': 'Ctrl+J', 'description': 'Duplicate layer'},
        'layer_delete': {'key': 'Delete', 'description': 'Delete layer'},
        'layer_merge': {'key': 'Ctrl+E', 'description': 'Merge layers'},
        'layer_flatten': {'key': 'Ctrl+Shift+E', 'description': 'Flatten image'},
        
        'help_about': {'key': 'F1', 'description': 'About'}
    }
    
    def __init__(self):
        self.settings = QSettings("AI Image Editor", "Shortcuts")
        self.shortcuts = self.load_shortcuts()
        
    def load_shortcuts(self):
        """Load shortcuts from settings"""
        shortcuts = {}
        for action_id, default in self.DEFAULT_SHORTCUTS.items():
            saved = self.settings.value(action_id)
            if saved:
                shortcuts[action_id] = saved
            else:
                shortcuts[action_id] = default['key']
        return shortcuts
    
    def save_shortcuts(self):
        """Save shortcuts to settings"""
        for action_id, key in self.shortcuts.items():
            self.settings.setValue(action_id, key)
    
    def get_shortcut(self, action_id):
        """Get shortcut for action"""
        return self.shortcuts.get(action_id, self.DEFAULT_SHORTCUTS[action_id]['key'])
    
    def set_shortcut(self, action_id, key_sequence):
        """Set custom shortcut for action"""
        self.shortcuts[action_id] = key_sequence
        self.save_shortcuts()
    
    def reset_to_defaults(self):
        """Reset all shortcuts to defaults"""
        self.shortcuts = {aid: default['key'] for aid, default in self.DEFAULT_SHORTCUTS.items()}
        self.save_shortcuts()
    
    def get_action_description(self, action_id):
        """Get description of action"""
        return self.DEFAULT_SHORTCUTS.get(action_id, {}).get('description', action_id)
    
    def check_conflicts(self):
        """Check for shortcut conflicts"""
        conflicts = []
        used_keys = {}
        
        for action_id, key in self.shortcuts.items():
            if key in used_keys:
                conflicts.append((used_keys[key], action_id, key))
            else:
                used_keys[key] = action_id
        
        return conflicts

class ShortcutDialog(QDialog):
    """Dialog for customizing keyboard shortcuts"""
    
    def __init__(self, shortcut_manager, parent=None):
        super().__init__(parent)
        self.manager = shortcut_manager
        self.setWindowTitle("Customize Keyboard Shortcuts")
        self.setGeometry(200, 200, 600, 400)
        self.setModal(True)
        
        self.init_ui()
        self.load_shortcuts()
        
    def init_ui(self):
        """Initialize dialog UI"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("Double-click a shortcut to edit it. Press the desired key combination.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Shortcuts table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_defaults)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_changes)
        button_layout.addWidget(self.apply_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def load_shortcuts(self):
        """Load shortcuts into table"""
        self.table.setRowCount(len(self.manager.DEFAULT_SHORTCUTS))
        
        for i, (action_id, default) in enumerate(self.manager.DEFAULT_SHORTCUTS.items()):
            # Action
            action_item = QTableWidgetItem(action_id.replace('_', ' ').title())
            action_item.setData(Qt.UserRole, action_id)
            action_item.setFlags(action_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, action_item)
            
            # Shortcut (editable)
            shortcut = self.manager.get_shortcut(action_id)
            shortcut_item = QTableWidgetItem(shortcut)
            shortcut_item.setFlags(shortcut_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(i, 1, shortcut_item)
            
            # Description
            desc_item = QTableWidgetItem(default['description'])
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 2, desc_item)
    
    def reset_defaults(self):
        """Reset all shortcuts to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Shortcuts",
            "Reset all keyboard shortcuts to default values?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.manager.reset_to_defaults()
            self.load_shortcuts()
    
    def apply_changes(self):
        """Apply shortcut changes"""
        changes = {}
        
        for i in range(self.table.rowCount()):
            action_id = self.table.item(i, 0).data(Qt.UserRole)
            new_shortcut = self.table.item(i, 1).text()
            
            if new_shortcut != self.manager.get_shortcut(action_id):
                changes[action_id] = new_shortcut
        
        if changes:
            # Check for conflicts
            conflicts = self.manager.check_conflicts()
            if conflicts:
                conflict_msg = "The following shortcuts conflict:\n\n"
                for a1, a2, key in conflicts:
                    desc1 = self.manager.get_action_description(a1)
                    desc2 = self.manager.get_action_description(a2)
                    conflict_msg += f"• {desc1} and {desc2} both use '{key}'\n"
                
                QMessageBox.warning(self, "Shortcut Conflicts", conflict_msg)
                return
            
            # Apply changes
            for action_id, shortcut in changes.items():
                self.manager.set_shortcut(action_id, shortcut)
            
            QMessageBox.information(self, "Success", "Shortcuts updated successfully.")
            self.accept()
        else:
            self.reject()