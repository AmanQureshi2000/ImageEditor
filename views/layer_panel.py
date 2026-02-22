from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QListWidget, QListWidgetItem, QLabel, QSlider,
                            QComboBox, QGroupBox, QMenu, QMessageBox,
                            QInputDialog, QDialog, QLineEdit, QDialogButtonBox)
from PyQt5.QtCore import Qt, pyqtSignal,QSize
from PyQt5.QtGui import QPixmap, QIcon, QPainter
import io
from PIL import Image

class LayerItem(QWidget):
    """Custom widget for layer list item"""
    
    visibility_changed = pyqtSignal(int, bool)
    opacity_changed = pyqtSignal(int, float)
    blend_mode_changed = pyqtSignal(int, str)
    selected = pyqtSignal(int)
    
    def __init__(self, layer_index, layer_name, thumbnail, opacity=1.0, 
                 blend_mode='normal', visible=True):
        super().__init__()
        self.layer_index = layer_index
        self.visible = visible
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Visibility toggle
        self.visibility_btn = QPushButton("👁" if visible else "◯")
        self.visibility_btn.setFixedSize(24, 24)
        self.visibility_btn.clicked.connect(self.toggle_visibility)
        layout.addWidget(self.visibility_btn)
        
        # Thumbnail
        thumb_label = QLabel()
        if thumbnail:
            pixmap = self._pil_to_pixmap(thumbnail)
            thumb_label.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(thumb_label)
        
        # Name and controls
        controls_layout = QVBoxLayout()
        
        # Name
        self.name_label = QLabel(layer_name)
        controls_layout.addWidget(self.name_label)
        
        # Blend mode and opacity
        blend_layout = QHBoxLayout()
        self.blend_combo = QComboBox()
        self.blend_combo.addItems(['normal', 'multiply', 'screen', 'overlay', 
                                   'darken', 'lighten', 'difference'])
        self.blend_combo.setCurrentText(blend_mode)
        self.blend_combo.currentTextChanged.connect(self.on_blend_changed)
        blend_layout.addWidget(self.blend_combo)
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(opacity * 100))
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        blend_layout.addWidget(self.opacity_slider)
        
        self.opacity_label = QLabel(f"{int(opacity * 100)}%")
        blend_layout.addWidget(self.opacity_label)
        
        controls_layout.addLayout(blend_layout)
        layout.addLayout(controls_layout)
        
    def _pil_to_pixmap(self, pil_image):
        """Convert PIL image to QPixmap"""
        byte_array = io.BytesIO()
        pil_image.save(byte_array, format='PNG')
        pixmap = QPixmap()
        pixmap.loadFromData(byte_array.getvalue())
        return pixmap
    
    def toggle_visibility(self):
        """Toggle layer visibility"""
        self.visible = not self.visible
        self.visibility_btn.setText("👁" if self.visible else "◯")
        self.visibility_changed.emit(self.layer_index, self.visible)
    
    def on_opacity_changed(self, value):
        """Handle opacity change"""
        self.opacity_label.setText(f"{value}%")
        self.opacity_changed.emit(self.layer_index, value / 100.0)
    
    def on_blend_changed(self, mode):
        """Handle blend mode change"""
        self.blend_mode_changed.emit(self.layer_index, mode)
    
    def mousePressEvent(self, event):
        """Handle selection"""
        self.selected.emit(self.layer_index)
        super().mousePressEvent(event)

class LayerPanel(QWidget):
    """Panel for layer management"""
    
    layer_selected = pyqtSignal(int)
    layer_added = pyqtSignal()
    layer_removed = pyqtSignal(int)
    layer_moved = pyqtSignal(int, int)
    layer_merged = pyqtSignal(list)
    layer_flattened = pyqtSignal()
    layer_opacity_changed = pyqtSignal(int, float)
    layer_blend_changed = pyqtSignal(int, str)
    layer_visibility_changed = pyqtSignal(int, bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layers = []
        self.layer_widgets = []
        self.current_layer = -1
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize layer panel UI"""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Add")
        self.add_btn.clicked.connect(self.add_layer)
        toolbar.addWidget(self.add_btn)
        
        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.clicked.connect(self.delete_layer)
        toolbar.addWidget(self.delete_btn)
        
        self.duplicate_btn = QPushButton("📋 Duplicate")
        self.duplicate_btn.clicked.connect(self.duplicate_layer)
        toolbar.addWidget(self.duplicate_btn)
        
        self.merge_btn = QPushButton("🔄 Merge")
        self.merge_btn.clicked.connect(self.merge_layers)
        toolbar.addWidget(self.merge_btn)
        
        self.flatten_btn = QPushButton("📦 Flatten")
        self.flatten_btn.clicked.connect(self.flatten_layers)
        toolbar.addWidget(self.flatten_btn)
        
        layout.addLayout(toolbar)
        
        # Layer list
        self.layer_list = QListWidget()
        self.layer_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.layer_list.itemClicked.connect(self.on_layer_clicked)
        layout.addWidget(self.layer_list)
        
        # Layer properties
        props_group = QGroupBox("Layer Properties")
        props_layout = QVBoxLayout()
        
        # Name edit
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.returnPressed.connect(self.update_layer_name)
        name_layout.addWidget(self.name_edit)
        props_layout.addLayout(name_layout)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
    def add_layer(self):
        """Add new layer"""
        name, ok = QInputDialog.getText(self, "New Layer", "Layer name:")
        if ok and name:
            self.layer_added.emit()
    
    def delete_layer(self):
        """Delete selected layer"""
        current_row = self.layer_list.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self, "Delete Layer",
                f"Delete layer '{self.layers[current_row]}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.layer_removed.emit(current_row)
    
    def duplicate_layer(self):
        """Duplicate selected layer"""
        current_row = self.layer_list.currentRow()
        if current_row >= 0:
            self.layer_added.emit()  # Will be handled by controller
    
    def merge_layers(self):
        """Merge selected layers"""
        selected = [item.row() for item in self.layer_list.selectedIndexes()]
        if len(selected) >= 2:
            self.layer_merged.emit(selected)
    
    def flatten_layers(self):
        """Flatten all layers"""
        if len(self.layers) > 1:
            reply = QMessageBox.question(
                self, "Flatten Layers",
                "Flatten all layers into one?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.layer_flattened.emit()
    
    def update_layer_list(self, layers, thumbnails, opacities, blend_modes, visibilities):
        """Update the layer list display"""
        self.layer_list.clear()
        self.layer_widgets.clear()
        self.layers = layers
        
        for i, (name, thumb, opacity, mode, visible) in enumerate(zip(
                layers, thumbnails, opacities, blend_modes, visibilities)):
            
            item = QListWidgetItem(self.layer_list)
            item.setSizeHint(QSize(250, 60))
            
            widget = LayerItem(i, name, thumb, opacity, mode, visible)
            widget.visibility_changed.connect(self.on_visibility_changed)
            widget.opacity_changed.connect(self.on_opacity_changed)
            widget.blend_mode_changed.connect(self.on_blend_changed)
            widget.selected.connect(self.on_layer_selected)
            
            self.layer_list.addItem(item)
            self.layer_list.setItemWidget(item, widget)
            self.layer_widgets.append(widget)
    
    def on_layer_clicked(self, item):
        """Handle layer click"""
        row = self.layer_list.row(item)
        if row >= 0:
            self.current_layer = row
            self.name_edit.setText(self.layers[row])
            self.layer_selected.emit(row)
    
    def on_layer_selected(self, index):
        """Handle layer selection from widget"""
        self.layer_list.setCurrentRow(index)
        self.current_layer = index
        self.name_edit.setText(self.layers[index])
        self.layer_selected.emit(index)
    
    def on_visibility_changed(self, index, visible):
        """Handle visibility change"""
        self.layer_visibility_changed.emit(index, visible)
    
    def on_opacity_changed(self, index, opacity):
        """Handle opacity change"""
        self.layer_opacity_changed.emit(index, opacity)
    
    def on_blend_changed(self, index, mode):
        """Handle blend mode change"""
        self.layer_blend_changed.emit(index, mode)
    
    def update_layer_name(self):
        """Update layer name"""
        if self.current_layer >= 0:
            new_name = self.name_edit.text()
            if new_name:
                self.layers[self.current_layer] = new_name
                widget = self.layer_widgets[self.current_layer]
                widget.name_label.setText(new_name)