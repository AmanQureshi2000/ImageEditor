from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QListWidget, QListWidgetItem, QLabel, QSlider,
                            QComboBox, QGroupBox, QMessageBox,
                            QInputDialog,QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt5.QtGui import QPixmap, QMouseEvent
import io
from PIL import Image

class LayerItem(QWidget):
    """Custom widget for layer list item"""
    
    visibility_changed = pyqtSignal(int, bool)
    opacity_changed = pyqtSignal(int, float)
    blend_mode_changed = pyqtSignal(int, str)
    selected = pyqtSignal(int)
    rename_requested = pyqtSignal(int)
    
    def __init__(self, layer_index, layer_name, thumbnail, opacity=1.0, 
                 blend_mode='normal', visible=True):
        super().__init__()
        self.layer_index = layer_index
        self.visible = visible
        
        # Set object name for styling
        self.setObjectName(f"layer_item_{layer_index}")
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # Visibility toggle
        self.visibility_btn = QPushButton("👁" if visible else "◯")
        self.visibility_btn.setFixedSize(28, 28)
        self.visibility_btn.setToolTip("Toggle layer visibility")
        self.visibility_btn.clicked.connect(self.toggle_visibility)
        layout.addWidget(self.visibility_btn)
        
        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(40, 40)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setStyleSheet("QLabel { background-color: #1a1f2e; border: 1px solid #2a3347; border-radius: 4px; }")
        
        if thumbnail:
            pixmap = self._pil_to_pixmap(thumbnail)
            scaled_pixmap = pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumb_label.setPixmap(scaled_pixmap)
        layout.addWidget(self.thumb_label)
        
        # Name and controls (vertical)
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(4)
        
        # Name row with rename capability
        name_layout = QHBoxLayout()
        self.name_label = QLabel(layer_name)
        self.name_label.setStyleSheet("QLabel { font-weight: bold; }")
        self.name_label.setToolTip("Double-click to rename")
        name_layout.addWidget(self.name_label)
        name_layout.addStretch()
        controls_layout.addLayout(name_layout)
        
        # Blend mode and opacity row
        blend_layout = QHBoxLayout()
        blend_layout.setSpacing(4)
        
        # Blend mode combo
        self.blend_combo = QComboBox()
        self.blend_combo.addItems(['normal', 'multiply', 'screen', 'overlay', 
                                   'darken', 'lighten', 'difference', 'exclusion',
                                   'soft_light', 'hard_light'])
        self.blend_combo.setCurrentText(blend_mode)
        self.blend_combo.setToolTip("Blend mode")
        self.blend_combo.currentTextChanged.connect(self.on_blend_changed)
        self.blend_combo.setFixedWidth(90)
        blend_layout.addWidget(self.blend_combo)
        
        # Opacity slider
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(opacity * 100))
        self.opacity_slider.setToolTip("Opacity")
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        self.opacity_slider.setFixedWidth(80)
        blend_layout.addWidget(self.opacity_slider)
        
        # Opacity label
        self.opacity_label = QLabel(f"{int(opacity * 100)}%")
        self.opacity_label.setFixedWidth(35)
        self.opacity_label.setAlignment(Qt.AlignRight)
        blend_layout.addWidget(self.opacity_label)
        
        blend_layout.addStretch()
        controls_layout.addLayout(blend_layout)
        
        layout.addLayout(controls_layout)
        
    def _pil_to_pixmap(self, pil_image):
        """Convert PIL image to QPixmap"""
        try:
            byte_array = io.BytesIO()
            pil_image.save(byte_array, format='PNG')
            pixmap = QPixmap()
            pixmap.loadFromData(byte_array.getvalue())
            return pixmap
        except Exception as e:
            print(f"Error converting PIL to pixmap: {e}")
            # Return empty pixmap on error
            return QPixmap(40, 40)
    
    def toggle_visibility(self):
        """Toggle layer visibility"""
        self.visible = not self.visible
        self.visibility_btn.setText("👁" if self.visible else "◯")
        self.visibility_btn.setToolTip("Hide layer" if self.visible else "Show layer")
        self.visibility_changed.emit(self.layer_index, self.visible)
    
    def on_opacity_changed(self, value):
        """Handle opacity change"""
        self.opacity_label.setText(f"{value}%")
        self.opacity_changed.emit(self.layer_index, value / 100.0)
    
    def on_blend_changed(self, mode):
        """Handle blend mode change"""
        self.blend_mode_changed.emit(self.layer_index, mode)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for selection"""
        self.selected.emit(self.layer_index)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double click for rename"""
        self.rename_requested.emit(self.layer_index)
        super().mouseDoubleClickEvent(event)


class LayerPanel(QWidget):
    """Panel for layer management"""
    
    layer_selected = pyqtSignal(int)
    layer_added = pyqtSignal()
    layer_removed = pyqtSignal(int)
    layer_duplicate_requested = pyqtSignal(int)
    layer_renamed = pyqtSignal(int, str)
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
        layout.setSpacing(8)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)
        
        self.add_btn = QPushButton("➕")
        self.add_btn.setToolTip("Add new layer")
        self.add_btn.setFixedSize(32, 32)
        self.add_btn.clicked.connect(self.add_layer)
        toolbar.addWidget(self.add_btn)
        
        self.delete_btn = QPushButton("🗑")
        self.delete_btn.setToolTip("Delete selected layer")
        self.delete_btn.setFixedSize(32, 32)
        self.delete_btn.clicked.connect(self.delete_layer)
        toolbar.addWidget(self.delete_btn)
        
        self.duplicate_btn = QPushButton("📋")
        self.duplicate_btn.setToolTip("Duplicate selected layer")
        self.duplicate_btn.setFixedSize(32, 32)
        self.duplicate_btn.clicked.connect(self.duplicate_layer)
        toolbar.addWidget(self.duplicate_btn)
        
        self.merge_btn = QPushButton("🔄")
        self.merge_btn.setToolTip("Merge selected layers")
        self.merge_btn.setFixedSize(32, 32)
        self.merge_btn.clicked.connect(self.merge_layers)
        toolbar.addWidget(self.merge_btn)
        
        self.flatten_btn = QPushButton("📦")
        self.flatten_btn.setToolTip("Flatten all layers")
        self.flatten_btn.setFixedSize(32, 32)
        self.flatten_btn.clicked.connect(self.flatten_layers)
        toolbar.addWidget(self.flatten_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Layer list
        self.layer_list = QListWidget()
        self.layer_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.layer_list.setDragDropMode(QListWidget.InternalMove)
        self.layer_list.setDefaultDropAction(Qt.MoveAction)
        self.layer_list.setAlternatingRowColors(True)
        self.layer_list.setStyleSheet("QListWidget::item { padding: 2px; }")
        self.layer_list.itemClicked.connect(self.on_layer_clicked)
        self.layer_list.model().rowsMoved.connect(self.on_layers_reordered)
        layout.addWidget(self.layer_list)
        
        # Layer properties
        props_group = QGroupBox("Properties")
        props_layout = QVBoxLayout()
        props_layout.setSpacing(4)
        
        # Name edit
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Layer name")
        self.name_edit.returnPressed.connect(self.update_layer_name)
        self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        props_layout.addLayout(name_layout)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
    def add_layer(self):
        """Add new layer"""
        name, ok = QInputDialog.getText(self, "New Layer", "Enter layer name:")
        if ok and name:
            self.layer_added.emit()
    
    def delete_layer(self):
        """Delete selected layer"""
        current_row = self.layer_list.currentRow()
        if current_row >= 0:
            layer_name = self.layers[current_row] if current_row < len(self.layers) else "this layer"
            reply = QMessageBox.question(
                self, "Delete Layer",
                f"Delete layer '{layer_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.layer_removed.emit(current_row)
    
    def duplicate_layer(self):
        """Duplicate selected layer"""
        current_row = self.layer_list.currentRow()
        if current_row >= 0:
            self.layer_duplicate_requested.emit(current_row)
    
    def merge_layers(self):
        """Merge selected layers"""
        selected = [item.row() for item in self.layer_list.selectedIndexes()]
        if len(selected) >= 2:
            self.layer_merged.emit(selected)
        else:
            QMessageBox.information(self, "Merge Layers", "Select at least two layers to merge.")
    
    def flatten_layers(self):
        """Flatten all layers"""
        if len(self.layers) > 1:
            reply = QMessageBox.question(
                self, "Flatten Layers",
                "Flatten all layers into one? This cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.layer_flattened.emit()
    
    def on_layers_reordered(self):
        """Handle layer reordering via drag and drop"""
        # Get the new order
        new_order = []
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            widget = self.layer_list.itemWidget(item)
            if widget and hasattr(widget, 'layer_index'):
                new_order.append(widget.layer_index)
        
        # Emit move signals if needed
        if len(new_order) == len(self.layers):
            # This is simplified - in a real implementation you'd track actual moves
            pass
    
    def update_layer_list(self, layer_names, thumbnails, opacities, blend_modes, visibilities):
        """Update the layer list display"""
        self.layer_list.clear()
        self.layer_widgets.clear()
        self.layers = layer_names
        
        for i, (name, thumb, opacity, mode, visible) in enumerate(zip(
                layer_names, thumbnails, opacities, blend_modes, visibilities)):
            
            item = QListWidgetItem(self.layer_list)
            item.setSizeHint(QSize(280, 70))
            item.setData(Qt.UserRole, i)
            
            widget = LayerItem(i, name, thumb, opacity, mode, visible)
            widget.visibility_changed.connect(self.on_visibility_changed)
            widget.opacity_changed.connect(self.on_opacity_changed)
            widget.blend_mode_changed.connect(self.on_blend_changed)
            widget.selected.connect(self.on_layer_selected)
            widget.rename_requested.connect(self.on_rename_requested)
            
            self.layer_list.addItem(item)
            self.layer_list.setItemWidget(item, widget)
            self.layer_widgets.append(widget)
    
    def on_layer_clicked(self, item):
        """Handle layer click"""
        row = self.layer_list.row(item)
        if 0 <= row < len(self.layers):
            self.current_layer = row
            self.name_edit.setText(self.layers[row])
            self.name_edit.setEnabled(True)
            self.layer_selected.emit(row)
    
    def on_layer_selected(self, index):
        """Handle layer selection from widget"""
        if 0 <= index < len(self.layers):
            self.layer_list.setCurrentRow(index)
            self.current_layer = index
            self.name_edit.setText(self.layers[index])
            self.name_edit.setEnabled(True)
            self.layer_selected.emit(index)
    
    def on_rename_requested(self, index):
        """Handle rename request from double-click"""
        if 0 <= index < len(self.layers):
            current_name = self.layers[index]
            new_name, ok = QInputDialog.getText(
                self, "Rename Layer", 
                "Enter new layer name:",
                text=current_name
            )
            if ok and new_name and new_name != current_name:
                self.layers[index] = new_name
                widget = self.layer_widgets[index]
                widget.name_label.setText(new_name)
                self.layer_renamed.emit(index, new_name)
    
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
        """Update layer name and notify controller"""
        if 0 <= self.current_layer < len(self.layers):
            new_name = self.name_edit.text().strip()
            if new_name and new_name != self.layers[self.current_layer]:
                self.layers[self.current_layer] = new_name
                widget = self.layer_widgets[self.current_layer]
                widget.name_label.setText(new_name)
                self.layer_renamed.emit(self.current_layer, new_name)
    
    def get_selected_layers(self) -> list:
        """Get list of selected layer indices"""
        return [item.row() for item in self.layer_list.selectedIndexes()]
    
    def select_layer(self, index: int):
        """Select a specific layer"""
        if 0 <= index < len(self.layers):
            self.layer_list.setCurrentRow(index)
            self.current_layer = index
            self.name_edit.setText(self.layers[index])
            self.name_edit.setEnabled(True)