from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QMessageBox, 
                             QHeaderView)
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5.QtGui import QKeySequence, QFont
import json
import os

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
        'ai_colorize': {'key': 'Ctrl+Shift+C', 'description': 'Colorize image'},
        
        'layer_new': {'key': 'Ctrl+Shift+N', 'description': 'New layer'},
        'layer_duplicate': {'key': 'Ctrl+J', 'description': 'Duplicate layer'},
        'layer_delete': {'key': 'Delete', 'description': 'Delete layer'},
        'layer_merge': {'key': 'Ctrl+E', 'description': 'Merge layers'},
        'layer_flatten': {'key': 'Ctrl+Shift+E', 'description': 'Flatten image'},
        
        'help_about': {'key': 'F1', 'description': 'About'},
        'help_shortcuts': {'key': 'F2', 'description': 'Show shortcuts'}
    }
    
    def __init__(self):
        self.settings = QSettings("AI Image Editor", "Shortcuts")
        self.shortcuts = self.load_shortcuts()
        self.conflict_cache = None
        
    def load_shortcuts(self):
        """Load shortcuts from settings"""
        shortcuts = {}
        for action_id, default in self.DEFAULT_SHORTCUTS.items():
            saved = self.settings.value(action_id)
            if saved and isinstance(saved, str):
                # Validate the saved shortcut
                if self._validate_shortcut(saved):
                    shortcuts[action_id] = saved
                else:
                    shortcuts[action_id] = default['key']
            else:
                shortcuts[action_id] = default['key']
        return shortcuts
    
    def _validate_shortcut(self, shortcut: str) -> bool:
        """Validate a shortcut string"""
        if not shortcut or not isinstance(shortcut, str):
            return False
        
        # Basic validation - check if it can be parsed as QKeySequence
        try:
            ks = QKeySequence(shortcut)
            return not ks.isEmpty()
        except:
            return False
    
    def save_shortcuts(self):
        """Save shortcuts to settings"""
        for action_id, key in self.shortcuts.items():
            self.settings.setValue(action_id, key)
        # Clear conflict cache
        self.conflict_cache = None
    
    def get_shortcut(self, action_id):
        """Get shortcut for action"""
        if action_id not in self.shortcuts:
            return self.DEFAULT_SHORTCUTS.get(action_id, {}).get('key', '')
        return self.shortcuts[action_id]
    
    def set_shortcut(self, action_id, key_sequence):
        """Set custom shortcut for action"""
        if action_id not in self.DEFAULT_SHORTCUTS:
            raise ValueError(f"Unknown action ID: {action_id}")
        
        if not self._validate_shortcut(key_sequence):
            raise ValueError(f"Invalid shortcut: {key_sequence}")
        
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
        if self.conflict_cache is not None:
            return self.conflict_cache
        
        conflicts = []
        used_keys = {}
        
        for action_id, key in self.shortcuts.items():
            if key in used_keys:
                conflicts.append((used_keys[key], action_id, key))
            else:
                used_keys[key] = action_id
        
        self.conflict_cache = conflicts
        return conflicts
    
    def export_shortcuts(self, filepath: str):
        """Export shortcuts to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.shortcuts, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to export shortcuts: {e}")
            return False
    
    def import_shortcuts(self, filepath: str):
        """Import shortcuts from JSON file"""
        try:
            with open(filepath, 'r') as f:
                imported = json.load(f)
            
            # Validate imported shortcuts
            valid_shortcuts = {}
            for action_id, shortcut in imported.items():
                if action_id in self.DEFAULT_SHORTCUTS and self._validate_shortcut(shortcut):
                    valid_shortcuts[action_id] = shortcut
            
            if valid_shortcuts:
                self.shortcuts.update(valid_shortcuts)
                self.save_shortcuts()
                return True
            return False
        except Exception as e:
            print(f"Failed to import shortcuts: {e}")
            return False

class ShortcutDialog(QDialog):
    """Dialog for customizing keyboard shortcuts"""
    
    shortcuts_changed = pyqtSignal()
    
    def __init__(self, shortcut_manager, parent=None):
        super().__init__(parent)
        self.manager = shortcut_manager
        self.setWindowTitle("Customize Keyboard Shortcuts")
        self.setGeometry(200, 200, 700, 500)
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        self.init_ui()
        self.load_shortcuts()
        
    def init_ui(self):
        """Initialize dialog UI"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Double-click a shortcut to edit it. Press the desired key combination.\n"
            "Use modifiers like Ctrl, Alt, Shift with letters, numbers, or function keys."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { color: #666; padding: 5px; }")
        layout.addWidget(instructions)
        
        # Shortcuts table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)
        
        # Conflict warning label
        self.conflict_label = QLabel("")
        self.conflict_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.conflict_label.setWordWrap(True)
        self.conflict_label.hide()
        layout.addWidget(self.conflict_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Export/Import buttons
        self.export_btn = QPushButton("Export Shortcuts...")
        self.export_btn.clicked.connect(self.export_shortcuts)
        button_layout.addWidget(self.export_btn)
        
        self.import_btn = QPushButton("Import Shortcuts...")
        self.import_btn.clicked.connect(self.import_shortcuts)
        button_layout.addWidget(self.import_btn)
        
        button_layout.addStretch()
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_defaults)
        button_layout.addWidget(self.reset_btn)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_changes)
        self.apply_btn.setDefault(True)
        button_layout.addWidget(self.apply_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def load_shortcuts(self):
        """Load shortcuts into table"""
        self.table.setRowCount(len(self.manager.DEFAULT_SHORTCUTS))
        
        # Sort actions for consistent display
        sorted_items = sorted(self.manager.DEFAULT_SHORTCUTS.items())
        
        for i, (action_id, default) in enumerate(sorted_items):
            # Action
            action_text = ' '.join(word.capitalize() for word in action_id.split('_'))
            action_item = QTableWidgetItem(action_text)
            action_item.setData(Qt.UserRole, action_id)
            action_item.setFlags(action_item.flags() & ~Qt.ItemIsEditable)
            action_item.setToolTip(f"Internal ID: {action_id}")
            self.table.setItem(i, 0, action_item)
            
            # Shortcut (editable)
            shortcut = self.manager.get_shortcut(action_id)
            shortcut_item = QTableWidgetItem(shortcut)
            shortcut_item.setFlags(shortcut_item.flags() | Qt.ItemIsEditable)
            shortcut_item.setToolTip("Double-click to edit")
            self.table.setItem(i, 1, shortcut_item)
            
            # Description
            desc_item = QTableWidgetItem(default['description'])
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 2, desc_item)
        
        # Check for initial conflicts
        self.check_for_conflicts()
    
    def check_for_conflicts(self):
        """Check for shortcut conflicts in the table"""
        used_keys = {}
        conflicts = []
        
        for i in range(self.table.rowCount()):
            action_item = self.table.item(i, 0)
            shortcut_item = self.table.item(i, 1)
            
            if not action_item or not shortcut_item:
                continue
                
            action_id = action_item.data(Qt.UserRole)
            shortcut = shortcut_item.text()
            
            if shortcut in used_keys:
                conflicts.append((used_keys[shortcut], action_id, shortcut))
                # Highlight conflicting rows
                self.table.item(used_keys[shortcut], 1).setBackground(Qt.red)
                self.table.item(i, 1).setBackground(Qt.red)
            else:
                used_keys[shortcut] = i
                # Reset background for non-conflicting rows
                self.table.item(i, 1).setBackground(Qt.white)
        
        # Show conflict message
        if conflicts:
            msg = "Conflicts detected:\n"
            for a1, a2, key in conflicts:
                desc1 = self.manager.get_action_description(a1)
                desc2 = self.manager.get_action_description(a2)
                msg += f"• '{key}' is used by both '{desc1}' and '{desc2}'\n"
            self.conflict_label.setText(msg)
            self.conflict_label.show()
        else:
            self.conflict_label.hide()
        
        return conflicts
    
    def reset_defaults(self):
        """Reset all shortcuts to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Shortcuts",
            "Reset all keyboard shortcuts to default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.manager.reset_to_defaults()
            self.load_shortcuts()
            self.check_for_conflicts()
    
    def export_shortcuts(self):
        """Export shortcuts to file"""
        from PyQt5.QtWidgets import QFileDialog
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Shortcuts",
            "shortcuts.json",
            "JSON Files (*.json)"
        )
        
        if filepath:
            if self.manager.export_shortcuts(filepath):
                QMessageBox.information(self, "Success", "Shortcuts exported successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to export shortcuts.")
    
    def import_shortcuts(self):
        """Import shortcuts from file"""
        from PyQt5.QtWidgets import QFileDialog
        
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Shortcuts",
            "",
            "JSON Files (*.json)"
        )
        
        if filepath:
            reply = QMessageBox.question(
                self,
                "Import Shortcuts",
                "Importing will overwrite current shortcuts. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.manager.import_shortcuts(filepath):
                    self.load_shortcuts()
                    self.check_for_conflicts()
                    QMessageBox.information(self, "Success", "Shortcuts imported successfully.")
                else:
                    QMessageBox.warning(self, "Error", "Failed to import shortcuts.")
    
    def apply_changes(self):
        """Apply shortcut changes"""
        # First check for conflicts
        conflicts = self.check_for_conflicts()
        if conflicts:
            reply = QMessageBox.question(
                self,
                "Conflicts Detected",
                "There are shortcut conflicts. Apply anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        changes = {}
        invalid_shortcuts = []
        
        for i in range(self.table.rowCount()):
            action_id = self.table.item(i, 0).data(Qt.UserRole)
            new_shortcut = self.table.item(i, 1).text().strip()
            
            # Validate shortcut
            if not self.manager._validate_shortcut(new_shortcut):
                invalid_shortcuts.append((action_id, new_shortcut))
                continue
            
            if new_shortcut != self.manager.get_shortcut(action_id):
                changes[action_id] = new_shortcut
        
        if invalid_shortcuts:
            msg = "The following shortcuts are invalid:\n\n"
            for action_id, shortcut in invalid_shortcuts:
                desc = self.manager.get_action_description(action_id)
                msg += f"• {desc}: '{shortcut}'\n"
            msg += "\nPlease fix them and try again."
            QMessageBox.warning(self, "Invalid Shortcuts", msg)
            return
        
        if changes:
            # Apply changes
            for action_id, shortcut in changes.items():
                try:
                    self.manager.set_shortcut(action_id, shortcut)
                except ValueError as e:
                    QMessageBox.warning(self, "Error", str(e))
                    return
            
            self.shortcuts_changed.emit()
            QMessageBox.information(self, "Success", "Shortcuts updated successfully.")
            self.accept()
        else:
            self.reject()