from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QSpinBox, QSlider, QCheckBox,
                            QPushButton, QGroupBox, QRadioButton, QFileDialog,
                            QApplication, QButtonGroup)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QIcon
import os

class ExportDialog(QDialog):
    """Export options dialog with preview"""
    
    export_requested = pyqtSignal(str, dict)  # filepath, options
    
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.setWindowTitle("Export Options")
        self.setGeometry(200, 200, 550, 500)
        self.setMinimumSize(500, 450)
        self.setModal(True)
        
        # Store original dimensions
        self.original_width = pixmap.width() if not pixmap.isNull() else 800
        self.original_height = pixmap.height() if not pixmap.isNull() else 600
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize export dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Preview label (optional)
        if not self.pixmap.isNull():
            preview_layout = QHBoxLayout()
            preview_label = QLabel("Preview:")
            preview_label.setStyleSheet("font-weight: bold;")
            preview_layout.addWidget(preview_label)
            
            # Small thumbnail preview
            thumbnail = self.pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumb_label = QLabel()
            thumb_label.setPixmap(thumbnail)
            thumb_label.setFixedSize(82, 82)
            thumb_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; padding: 1px;")
            preview_layout.addWidget(thumb_label)
            preview_layout.addStretch()
            layout.addLayout(preview_layout)
        
        # Format selection
        format_group = QGroupBox("Format")
        format_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        format_layout = QVBoxLayout()
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPEG", "PNG", "WEBP", "TIFF", "BMP", "GIF"])
        self.format_combo.setMinimumHeight(30)
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Quality settings
        self.quality_group = QGroupBox("Quality")
        self.quality_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        quality_layout = QVBoxLayout()
        quality_layout.setSpacing(10)
        
        # Quality slider
        quality_slider_layout = QHBoxLayout()
        quality_slider_layout.addWidget(QLabel("Quality:"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(95)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(10)
        self.quality_slider.valueChanged.connect(self.on_quality_changed)
        quality_slider_layout.addWidget(self.quality_slider)
        
        self.quality_value = QLabel("95%")
        self.quality_value.setMinimumWidth(40)
        self.quality_value.setAlignment(Qt.AlignRight)
        quality_slider_layout.addWidget(self.quality_value)
        quality_layout.addLayout(quality_slider_layout)
        
        # Quality presets
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(5)
        
        self.low_quality_btn = QPushButton("Low")
        self.low_quality_btn.setToolTip("60% quality")
        self.low_quality_btn.clicked.connect(lambda: self.quality_slider.setValue(60))
        self.low_quality_btn.setFixedHeight(28)
        preset_layout.addWidget(self.low_quality_btn)
        
        self.medium_quality_btn = QPushButton("Medium")
        self.medium_quality_btn.setToolTip("80% quality")
        self.medium_quality_btn.clicked.connect(lambda: self.quality_slider.setValue(80))
        self.medium_quality_btn.setFixedHeight(28)
        preset_layout.addWidget(self.medium_quality_btn)
        
        self.high_quality_btn = QPushButton("High")
        self.high_quality_btn.setToolTip("95% quality")
        self.high_quality_btn.clicked.connect(lambda: self.quality_slider.setValue(95))
        self.high_quality_btn.setFixedHeight(28)
        preset_layout.addWidget(self.high_quality_btn)
        
        self.max_quality_btn = QPushButton("Maximum")
        self.max_quality_btn.setToolTip("100% quality")
        self.max_quality_btn.clicked.connect(lambda: self.quality_slider.setValue(100))
        self.max_quality_btn.setFixedHeight(28)
        preset_layout.addWidget(self.max_quality_btn)
        
        quality_layout.addLayout(preset_layout)
        
        self.quality_group.setLayout(quality_layout)
        layout.addWidget(self.quality_group)
        
        # Size settings
        size_group = QGroupBox("Size")
        size_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        size_layout = QVBoxLayout()
        size_layout.setSpacing(10)
        
        # Size options - use QButtonGroup for radio buttons
        self.size_button_group = QButtonGroup(self)
        
        self.original_size_radio = QRadioButton("Original Size")
        self.original_size_radio.setChecked(True)
        self.original_size_radio.toggled.connect(self.on_size_option_changed)
        size_layout.addWidget(self.original_size_radio)
        self.size_button_group.addButton(self.original_size_radio)
        
        self.percentage_radio = QRadioButton("Scale by percentage")
        self.percentage_radio.toggled.connect(self.on_size_option_changed)
        size_layout.addWidget(self.percentage_radio)
        self.size_button_group.addButton(self.percentage_radio)
        
        # Percentage controls
        percentage_layout = QHBoxLayout()
        percentage_layout.addSpacing(30)
        self.percentage_spin = QSpinBox()
        self.percentage_spin.setRange(1, 500)
        self.percentage_spin.setValue(100)
        self.percentage_spin.setSuffix("%")
        self.percentage_spin.setEnabled(False)
        self.percentage_spin.valueChanged.connect(self.update_size_info)
        self.percentage_spin.setFixedWidth(100)
        percentage_layout.addWidget(self.percentage_spin)
        percentage_layout.addStretch()
        size_layout.addLayout(percentage_layout)
        
        # Custom dimensions
        self.custom_size_radio = QRadioButton("Custom dimensions")
        self.custom_size_radio.toggled.connect(self.on_size_option_changed)
        size_layout.addWidget(self.custom_size_radio)
        self.size_button_group.addButton(self.custom_size_radio)
        
        # Dimension controls
        dim_layout = QHBoxLayout()
        dim_layout.addSpacing(30)
        
        dim_layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(self.original_width)
        self.width_spin.setEnabled(False)
        self.width_spin.valueChanged.connect(self.on_width_changed)
        self.width_spin.setFixedWidth(100)
        dim_layout.addWidget(self.width_spin)
        
        dim_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(self.original_height)
        self.height_spin.setEnabled(False)
        self.height_spin.valueChanged.connect(self.on_height_changed)
        self.height_spin.setFixedWidth(100)
        dim_layout.addWidget(self.height_spin)
        
        self.keep_aspect_check = QCheckBox("Keep aspect ratio")
        self.keep_aspect_check.setChecked(True)
        self.keep_aspect_check.setEnabled(False)
        dim_layout.addWidget(self.keep_aspect_check)
        dim_layout.addStretch()
        
        size_layout.addLayout(dim_layout)
        
        # Size info
        self.size_info = QLabel()
        self.size_info.setStyleSheet("QLabel { color: #666; padding: 5px; background-color: #f5f5f5; border-radius: 3px; }")
        self.size_info.setAlignment(Qt.AlignCenter)
        self.update_size_info()
        size_layout.addWidget(self.size_info)
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        # Metadata options
        metadata_group = QGroupBox("Metadata")
        metadata_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        metadata_layout = QVBoxLayout()
        
        self.strip_metadata_check = QCheckBox("Strip all metadata")
        self.strip_metadata_check.setChecked(False)
        self.strip_metadata_check.setToolTip("Remove all EXIF and metadata from the exported image")
        metadata_layout.addWidget(self.strip_metadata_check)
        
        self.strip_location_check = QCheckBox("Strip location data")
        self.strip_location_check.setChecked(False)
        self.strip_location_check.setToolTip("Remove GPS coordinates and location information")
        metadata_layout.addWidget(self.strip_location_check)
        
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)
        
        # Output options
        output_group = QGroupBox("Output")
        output_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        output_layout = QHBoxLayout()
        
        self.output_path_edit = QLabel("No file selected")
        self.output_path_edit.setStyleSheet("QLabel { color: #666; padding: 5px; background-color: #f5f5f5; border-radius: 3px; }")
        self.output_path_edit.setWordWrap(True)
        output_layout.addWidget(self.output_path_edit, 1)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setObjectName("")
        self.browse_btn.clicked.connect(self.browse_output)
        self.browse_btn.setFixedHeight(30)
        self.browse_btn.setFixedWidth(100)
        output_layout.addWidget(self.browse_btn)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setObjectName("primary_btn")
        self.export_btn.clicked.connect(self.export)
        self.export_btn.setEnabled(False)
        self.export_btn.setFixedHeight(35)
        self.export_btn.setFixedWidth(120)
        button_layout.addWidget(self.export_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("danger_btn")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setFixedHeight(35)
        self.cancel_btn.setFixedWidth(120)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Initial setup
        self.on_format_changed("JPEG")
    
    def on_format_changed(self, format_name):
        """Handle format change"""
        # Enable/disable quality based on format
        lossless_formats = ["PNG", "BMP", "TIFF", "GIF"]
        if format_name in lossless_formats:
            self.quality_group.setEnabled(False)
        else:
            self.quality_group.setEnabled(True)
        
        # Update file extension hint if a file is already selected
        current_path = self.output_path_edit.text()
        if current_path and current_path != "No file selected":
            # Suggest new extension
            base = os.path.splitext(current_path)[0]
            ext = format_name.lower()
            if ext == 'jpeg':
                ext = 'jpg'
            new_path = f"{base}.{ext}"
            self.output_path_edit.setText(new_path)
    
    def on_quality_changed(self, value):
        """Handle quality change"""
        self.quality_value.setText(f"{value}%")
    
    def on_size_option_changed(self):
        """Handle size option change"""
        # Enable/disable controls based on selection
        self.percentage_spin.setEnabled(self.percentage_radio.isChecked())
        self.width_spin.setEnabled(self.custom_size_radio.isChecked())
        self.height_spin.setEnabled(self.custom_size_radio.isChecked())
        self.keep_aspect_check.setEnabled(self.custom_size_radio.isChecked())
        
        # Reset custom dimensions to original when switching to custom
        if self.custom_size_radio.isChecked():
            self.width_spin.blockSignals(True)
            self.height_spin.blockSignals(True)
            self.width_spin.setValue(self.original_width)
            self.height_spin.setValue(self.original_height)
            self.width_spin.blockSignals(False)
            self.height_spin.blockSignals(False)
        
        self.update_size_info()
    
    def on_width_changed(self, value):
        """Handle width change for custom dimensions"""
        if self.keep_aspect_check.isChecked() and not self.pixmap.isNull():
            # Maintain aspect ratio
            aspect = self.original_height / self.original_width
            new_height = int(value * aspect)
            self.height_spin.blockSignals(True)
            self.height_spin.setValue(max(1, new_height))
            self.height_spin.blockSignals(False)
        
        self.update_size_info()
    
    def on_height_changed(self, value):
        """Handle height change for custom dimensions"""
        if self.keep_aspect_check.isChecked() and not self.pixmap.isNull():
            # Maintain aspect ratio
            aspect = self.original_width / self.original_height
            new_width = int(value * aspect)
            self.width_spin.blockSignals(True)
            self.width_spin.setValue(max(1, new_width))
            self.width_spin.blockSignals(False)
        
        self.update_size_info()
    
    def update_size_info(self):
        """Update size information display"""
        if self.pixmap.isNull():
            self.size_info.setText("No image loaded")
            return
        
        original_size = f"Original: {self.original_width} × {self.original_height}"
        
        if self.percentage_radio.isChecked():
            scale = self.percentage_spin.value() / 100.0
            new_width = int(self.original_width * scale)
            new_height = int(self.original_height * scale)
            self.size_info.setText(f"{original_size} → Output: {new_width} × {new_height}")
        
        elif self.custom_size_radio.isChecked():
            self.size_info.setText(
                f"{original_size} → Output: {self.width_spin.value()} × {self.height_spin.value()}"
            )
        
        else:
            self.size_info.setText(original_size)
    
    def browse_output(self):
        """Browse for output file"""
        format_name = self.format_combo.currentText().lower()
        ext = format_name
        if format_name == 'jpeg':
            ext = 'jpg'
        
        # Suggest filename based on original
        suggested_name = f"exported_image.{ext}"
        
        filepath, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            suggested_name,
            f"{format_name.upper()} files (*.{ext});;All files (*.*)"
        )
        
        if filepath:
            # Ensure the file has the correct extension
            if not filepath.lower().endswith(f'.{ext}'):
                filepath = f"{filepath}.{ext}"
            
            self.output_path_edit.setText(filepath)
            self.export_btn.setEnabled(True)
            self.export_btn.setObjectName("primary_btn")
            # Refresh style
            self.export_btn.style().unpolish(self.export_btn)
            self.export_btn.style().polish(self.export_btn)
    
    def get_export_options(self):
        """Get current export options"""
        options = {
            'format': self.format_combo.currentText(),
            'quality': self.quality_slider.value() if self.quality_group.isEnabled() else 95,
            'strip_metadata': self.strip_metadata_check.isChecked(),
            'strip_location': self.strip_location_check.isChecked()
        }
        
        # Size options
        if self.percentage_radio.isChecked():
            options['scale'] = self.percentage_spin.value() / 100.0
        elif self.custom_size_radio.isChecked():
            options['width'] = self.width_spin.value()
            options['height'] = self.height_spin.value()
        
        return options
    
    def export(self):
        """Export image with selected options"""
        filepath = self.output_path_edit.text()
        if filepath and filepath != "No file selected":
            options = self.get_export_options()
            self.export_requested.emit(filepath, options)
            self.accept()
    
    def resizeEvent(self, event):
        """Handle resize event"""
        # Update size info when dialog is resized
        self.update_size_info()
        super().resizeEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.export_btn.isEnabled():
                self.export()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)