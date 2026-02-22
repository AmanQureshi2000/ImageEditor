from PyQt5.QtCore import QByteArray, QSettings, QPoint, QSize
from PyQt5.QtWidgets import QMainWindow, QSplitter, QToolBar, QTabWidget
from PyQt5.QtGui import QIcon
import json
import os
import base64

class WorkspaceManager:
    """Manage workspace persistence (window state, splitter positions, etc.)"""
    
    def __init__(self, app_name="AI Image Editor"):
        self.app_name = app_name
        self.settings = QSettings(app_name, app_name)
        self.workspace_file = "workspace.json"
        self.preferences = self.load_preferences()
        self.max_recent_files = 10
        
    def save_workspace(self, window: QMainWindow):
        """Save current workspace state"""
        try:
            # Convert QByteArray to string safely
            geometry_data = window.saveGeometry().toBase64().data()
            state_data = window.saveState().toBase64().data()
            
            # Handle both bytes and string types
            geometry_str = geometry_data.decode('utf-8') if isinstance(geometry_data, bytes) else str(geometry_data)
            state_str = state_data.decode('utf-8') if isinstance(state_data, bytes) else str(state_data)
            
            workspace = {
                'geometry': geometry_str,
                'state': state_str,
                'splitter_sizes': self._get_splitter_sizes(window),
                'last_file': self._get_last_file(window),
                'recent_files': self._get_recent_files(window),
                'active_tabs': self._get_active_tabs(window),
                'toolbar_positions': self._get_toolbar_positions(window),
                'window_position': self._get_window_position(window),
                'window_size': self._get_window_size(window),
                'version': '1.0'
            }
            
            # Save to file
            with open(self.workspace_file, 'w', encoding='utf-8') as f:
                json.dump(workspace, f, indent=2, ensure_ascii=False)
                
            # Also save to QSettings as backup
            self.settings.setValue("workspace", workspace)
            
            return True
        except Exception as e:
            print(f"Error saving workspace: {e}")
            return False
    
    def load_workspace(self, window: QMainWindow):
        """Load workspace state"""
        try:
            workspace = None
            
            # Try to load from file first
            if os.path.exists(self.workspace_file):
                try:
                    with open(self.workspace_file, 'r', encoding='utf-8') as f:
                        workspace = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Error reading workspace file: {e}")
            
            # Fallback to QSettings
            if not workspace:
                workspace = self.settings.value("workspace")
                if not workspace:
                    return False
            
            # Restore geometry and state
            if 'geometry' in workspace and workspace['geometry']:
                try:
                    geometry_bytes = workspace['geometry'].encode('utf-8')
                    window.restoreGeometry(QByteArray.fromBase64(geometry_bytes))
                except Exception as e:
                    print(f"Error restoring geometry: {e}")
            
            if 'state' in workspace and workspace['state']:
                try:
                    state_bytes = workspace['state'].encode('utf-8')
                    window.restoreState(QByteArray.fromBase64(state_bytes))
                except Exception as e:
                    print(f"Error restoring state: {e}")
            
            # Restore splitter sizes
            if 'splitter_sizes' in workspace:
                self._restore_splitter_sizes(window, workspace['splitter_sizes'])
            
            # Restore toolbar positions
            if 'toolbar_positions' in workspace:
                self._restore_toolbar_positions(window, workspace['toolbar_positions'])
            
            # Restore window position and size if needed
            if 'window_position' in workspace and workspace['window_position']:
                try:
                    pos = workspace['window_position']
                    window.move(pos['x'], pos['y'])
                except:
                    pass
            
            if 'window_size' in workspace and workspace['window_size']:
                try:
                    size = workspace['window_size']
                    window.resize(size['width'], size['height'])
                except:
                    pass
            
            return True
        except Exception as e:
            print(f"Error loading workspace: {e}")
            return False
    
    def _get_splitter_sizes(self, window):
        """Get sizes of all splitters in window"""
        sizes = {}
        try:
            for widget in window.findChildren(QSplitter):
                name = widget.objectName() or f"splitter_{id(widget)}"
                sizes[name] = list(widget.sizes())  # Convert to list for JSON
        except Exception as e:
            print(f"Error getting splitter sizes: {e}")
        return sizes
    
    def _restore_splitter_sizes(self, window, sizes):
        """Restore splitter sizes"""
        try:
            for widget in window.findChildren(QSplitter):
                name = widget.objectName() or f"splitter_{id(widget)}"
                if name in sizes:
                    try:
                        widget.setSizes([int(s) for s in sizes[name]])
                    except Exception as e:
                        print(f"Error restoring splitter {name}: {e}")
        except Exception as e:
            print(f"Error restoring splitter sizes: {e}")
    
    def _get_last_file(self, window):
        """Get last opened file path"""
        try:
            if hasattr(window, 'controller') and window.controller:
                if hasattr(window.controller, 'image_model') and window.controller.image_model:
                    if hasattr(window.controller.image_model, 'image_data') and window.controller.image_model.image_data:
                        return window.controller.image_model.image_data.path
        except Exception:
            pass
        return None
    
    def _get_recent_files(self, window):
        """Get recent files list"""
        try:
            if hasattr(window, 'recent_files'):
                return window.recent_files[:self.max_recent_files]
        except Exception:
            pass
        return []
    
    def _get_active_tabs(self, window):
        """Get active tab indices for all tab widgets"""
        tabs = {}
        try:
            for tab_widget in window.findChildren(QTabWidget):
                name = tab_widget.objectName() or f"tab_{id(tab_widget)}"
                tabs[name] = tab_widget.currentIndex()
        except Exception as e:
            print(f"Error getting active tabs: {e}")
        return tabs
    
    def _get_toolbar_positions(self, window):
        """Get toolbar positions"""
        positions = {}
        try:
            for toolbar in window.findChildren(QToolBar):
                name = toolbar.objectName() or f"toolbar_{id(toolbar)}"
                positions[name] = {
                    'area': int(window.toolBarArea(toolbar)),  # Convert to int for JSON
                    'break': window.toolBarBreak(toolbar)
                }
        except Exception as e:
            print(f"Error getting toolbar positions: {e}")
        return positions
    
    def _restore_toolbar_positions(self, window, positions):
        """Restore toolbar positions"""
        try:
            from PyQt5.QtCore import Qt
            for toolbar in window.findChildren(QToolBar):
                name = toolbar.objectName() or f"toolbar_{id(toolbar)}"
                if name in positions:
                    try:
                        pos = positions[name]
                        area = Qt.ToolBarArea(pos['area']) if isinstance(pos['area'], int) else pos['area']
                        window.addToolBar(area, toolbar)
                        if pos.get('break', False):
                            window.insertToolBarBreak(toolbar)
                    except Exception as e:
                        print(f"Error restoring toolbar {name}: {e}")
        except Exception as e:
            print(f"Error restoring toolbar positions: {e}")
    
    def _get_window_position(self, window):
        """Get window position"""
        try:
            pos = window.pos()
            return {'x': pos.x(), 'y': pos.y()}
        except:
            return None
    
    def _get_window_size(self, window):
        """Get window size"""
        try:
            size = window.size()
            return {'width': size.width(), 'height': size.height()}
        except:
            return None
    
    def save_recent_files(self, recent_files):
        """Save recent files list"""
        try:
            # Limit to max recent files
            trimmed = recent_files[:self.max_recent_files]
            self.settings.setValue("recent_files", trimmed)
        except Exception as e:
            print(f"Error saving recent files: {e}")
    
    def load_recent_files(self):
        """Load recent files list"""
        try:
            files = self.settings.value("recent_files", [])
            return files if isinstance(files, list) else []
        except Exception:
            return []
    
    def save_preferences(self, preferences):
        """Save user preferences"""
        try:
            self.preferences.update(preferences)
            for key, value in preferences.items():
                # Convert non-serializable values to strings
                if not isinstance(value, (str, int, float, bool, list, dict)):
                    value = str(value)
                self.settings.setValue(f"preferences/{key}", value)
        except Exception as e:
            print(f"Error saving preferences: {e}")
    
    def load_preferences(self):
        """Load user preferences"""
        preferences = {}
        try:
            for key in self.settings.allKeys():
                if key.startswith("preferences/"):
                    pref_key = key.replace("preferences/", "")
                    preferences[pref_key] = self.settings.value(key)
        except Exception as e:
            print(f"Error loading preferences: {e}")
        return preferences
    
    def get_preference(self, key, default=None):
        """Get a specific preference value"""
        return self.preferences.get(key, default)
    
    def set_preference(self, key, value):
        """Set a specific preference value"""
        self.preferences[key] = value
        self.save_preferences({key: value})
    
    def clear_all(self):
        """Clear all saved workspace data"""
        try:
            if os.path.exists(self.workspace_file):
                os.remove(self.workspace_file)
            self.settings.clear()
            self.preferences = {}
            print("All workspace data cleared")
        except Exception as e:
            print(f"Error clearing workspace data: {e}")
    
    def export_workspace(self, filepath):
        """Export workspace to a file"""
        try:
            # Get current settings
            workspace = {
                'recent_files': self.load_recent_files(),
                'preferences': self.preferences,
                'version': '1.0'
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(workspace, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting workspace: {e}")
            return False
    
    def import_workspace(self, filepath):
        """Import workspace from a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                workspace = json.load(f)
            
            if 'recent_files' in workspace:
                self.save_recent_files(workspace['recent_files'])
            
            if 'preferences' in workspace:
                self.save_preferences(workspace['preferences'])
            
            return True
        except Exception as e:
            print(f"Error importing workspace: {e}")
            return False