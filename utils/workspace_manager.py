from PyQt5.QtCore import QByteArray, QSettings
from PyQt5.QtWidgets import QMainWindow, QSplitter, QToolBar,QTabWidget
import json
import os

class WorkspaceManager:
    """Manage workspace persistence (window state, splitter positions, etc.)"""
    
    def __init__(self, app_name="AI Image Editor"):
        self.app_name = app_name
        self.settings = QSettings(app_name, app_name)
        self.workspace_file = "workspace.json"
        self.preferences = self.load_preferences()
        
    def save_workspace(self, window: QMainWindow):
        """Save current workspace state"""
        try:
            workspace = {
                'geometry': window.saveGeometry().toBase64().data().decode(),
                'state': window.saveState().toBase64().data().decode(),
                'splitter_sizes': self._get_splitter_sizes(window),
                'last_file': self._get_last_file(window),
                'recent_files': self._get_recent_files(window),
                'active_tab': self._get_active_tab(window),
                'toolbar_positions': self._get_toolbar_positions(window)
            }
            
            with open(self.workspace_file, 'w') as f:
                json.dump(workspace, f, indent=2)
                
            # Also save to QSettings as backup
            self.settings.setValue("workspace", workspace)
            
            return True
        except Exception as e:
            print(f"Error saving workspace: {e}")
            return False
    
    def load_workspace(self, window: QMainWindow):
        """Load workspace state"""
        try:
            # Try to load from file first
            if os.path.exists(self.workspace_file):
                with open(self.workspace_file, 'r') as f:
                    workspace = json.load(f)
            else:
                # Fallback to QSettings
                workspace = self.settings.value("workspace")
                if not workspace:
                    return False
            
            # Restore geometry and state
            if 'geometry' in workspace:
                window.restoreGeometry(QByteArray.fromBase64(workspace['geometry'].encode()))
            
            if 'state' in workspace:
                window.restoreState(QByteArray.fromBase64(workspace['state'].encode()))
            
            # Restore splitter sizes
            if 'splitter_sizes' in workspace:
                self._restore_splitter_sizes(window, workspace['splitter_sizes'])
            
            # Restore toolbar positions
            if 'toolbar_positions' in workspace:
                self._restore_toolbar_positions(window, workspace['toolbar_positions'])
            
            return True
        except Exception as e:
            print(f"Error loading workspace: {e}")
            return False
    
    def _get_splitter_sizes(self, window):
        """Get sizes of all splitters in window"""
        sizes = {}
        for widget in window.findChildren(QSplitter):
            name = widget.objectName() or f"splitter_{id(widget)}"
            sizes[name] = widget.sizes()
        return sizes
    
    def _restore_splitter_sizes(self, window, sizes):
        """Restore splitter sizes"""
        for widget in window.findChildren(QSplitter):
            name = widget.objectName() or f"splitter_{id(widget)}"
            if name in sizes:
                try:
                    widget.setSizes(sizes[name])
                except:
                    pass
    
    def _get_last_file(self, window):
        """Get last opened file path"""
        if hasattr(window, 'controller') and window.controller.image_model.image_data:
            return window.controller.image_model.image_data.path
        return None
    
    def _get_recent_files(self, window):
        """Get recent files list"""
        if hasattr(window, 'recent_files'):
            return window.recent_files
        return []
    
    def _get_active_tab(self, window):
        """Get active tab indices"""
        tabs = {}
        # Find all tab widgets and their current indices
        for tab_widget in window.findChildren(QTabWidget):
            name = tab_widget.objectName() or f"tab_{id(tab_widget)}"
            tabs[name] = tab_widget.currentIndex()
        return tabs
    
    def _get_toolbar_positions(self, window):
        """Get toolbar positions"""
        positions = {}
        for toolbar in window.findChildren(QToolBar):
            name = toolbar.objectName() or f"toolbar_{id(toolbar)}"
            positions[name] = {
                'area': window.toolBarArea(toolbar),
                'break': window.toolBarBreak(toolbar)
            }
        return positions
    
    def _restore_toolbar_positions(self, window, positions):
        """Restore toolbar positions"""
        for toolbar in window.findChildren(QToolBar):
            name = toolbar.objectName() or f"toolbar_{id(toolbar)}"
            if name in positions:
                pos = positions[name]
                window.addToolBar(pos['area'], toolbar)
                if pos['break']:
                    window.insertToolBarBreak(toolbar)
    
    def save_recent_files(self, recent_files):
        """Save recent files list"""
        self.settings.setValue("recent_files", recent_files)
    
    def load_recent_files(self):
        """Load recent files list"""
        return self.settings.value("recent_files", [])
    
    def save_preferences(self, preferences):
        """Save user preferences"""
        self.preferences.update(preferences)
        for key, value in preferences.items():
            self.settings.setValue(f"preferences/{key}", value)
    
    def load_preferences(self):
        """Load user preferences"""
        preferences = {}
        for key in self.settings.allKeys():
            if key.startswith("preferences/"):
                pref_key = key.replace("preferences/", "")
                preferences[pref_key] = self.settings.value(key)
        return preferences
    
    def get_preference(self, key, default=None):
        """Get a specific preference value"""
        return self.preferences.get(key, default)