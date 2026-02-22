from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QSpinBox, QSlider, QCheckBox,
                            QPushButton, QGroupBox, QRadioButton, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap

class ExportDialog(QDialog):
    """Export options dialog with preview"""
    
    export_requested = pyqtSignal(str, dict)  # filepath, options
    
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.setWindowTitle("Export Options")
        self.setGeometry(200, 200, 500, 400)
        self.setModal(True)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize export dialog UI"""
        layout = QVBoxLayout(self)
        
        # Format selection
        format_group = QGroupBox("Format")
        format_layout = QVBoxLayout()
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPEG", "PNG", "WEBP", "TIFF", "BMP", "GIF"])
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Quality settings
        self.quality_group = QGroupBox("Quality")
        quality_layout = QVBoxLayout()
        
        # Quality slider
        quality_slider_layout = QHBoxLayout()
        quality_slider_layout.addWidget(QLabel("Quality:"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(95)
        self.quality_slider.valueChanged.connect(self.on_quality_changed)
        quality_slider_layout.addWidget(self.quality_slider)
        
        self.quality_value = QLabel("95%")
        quality_slider_layout.addWidget(self.quality_value)
        quality_layout.addLayout(quality_slider_layout)
        
        # Quality presets
        preset_layout = QHBoxLayout()
        self.low_quality_btn = QPushButton("Low (60%)")
        self.low_quality_btn.clicked.connect(lambda: self.quality_slider.setValue(60))
        preset_layout.addWidget(self.low_quality_btn)
        
        self.medium_quality_btn = QPushButton("Medium (80%)")
        self.medium_quality_btn.clicked.connect(lambda: self.quality_slider.setValue(80))
        preset_layout.addWidget(self.medium_quality_btn)
        
        self.high_quality_btn = QPushButton("High (95%)")
        self.high_quality_btn.clicked.connect(lambda: self.quality_slider.setValue(95))
        preset_layout.addWidget(self.high_quality_btn)
        
        self.max_quality_btn = QPushButton("Maximum (100%)")
        self.max_quality_btn.clicked.connect(lambda: self.quality_slider.setValue(100))
        preset_layout.addWidget(self.max_quality_btn)
        
        quality_layout.addLayout(preset_layout)
        
        self.quality_group.setLayout(quality_layout)
        layout.addWidget(self.quality_group)
        
        # Size settings
        size_group = QGroupBox("Size")
        size_layout = QVBoxLayout()
        
        # Size options
        self.original_size_radio = QRadioButton("Original Size")
        self.original_size_radio.setChecked(True)
        self.original_size_radio.toggled.connect(self.on_size_option_changed)
        size_layout.addWidget(self.original_size_radio)
        
        self.percentage_radio = QRadioButton("Scale by percentage")
        self.percentage_radio.toggled.connect(self.on_size_option_changed)
        size_layout.addWidget(self.percentage_radio)
        
        # Percentage controls
        percentage_layout = QHBoxLayout()
        percentage_layout.addSpacing(20)
        self.percentage_spin = QSpinBox()
        self.percentage_spin.setRange(1, 500)
        self.percentage_spin.setValue(100)
        self.percentage_spin.setSuffix("%")
        self.percentage_spin.setEnabled(False)
        self.percentage_spin.valueChanged.connect(self.update_size_info)
        percentage_layout.addWidget(self.percentage_spin)
        size_layout.addLayout(percentage_layout)
        
        # Custom dimensions
        self.custom_size_radio = QRadioButton("Custom dimensions")
        self.custom_size_radio.toggled.connect(self.on_size_option_changed)
        size_layout.addWidget(self.custom_size_radio)
        
        # Dimension controls
        dim_layout = QHBoxLayout()
        dim_layout.addSpacing(20)
        
        dim_layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(self.pixmap.width() if not self.pixmap.isNull() else 800)
        self.width_spin.setEnabled(False)
        self.width_spin.valueChanged.connect(self.on_width_changed)
        dim_layout.addWidget(self.width_spin)
        
        dim_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(self.pixmap.height() if not self.pixmap.isNull() else 600)
        self.height_spin.setEnabled(False)
        self.height_spin.valueChanged.connect(self.on_height_changed)
        dim_layout.addWidget(self.height_spin)
        
        self.keep_aspect_check = QCheckBox("Keep aspect ratio")
        self.keep_aspect_check.setChecked(True)
        self.keep_aspect_check.setEnabled(False)
        dim_layout.addWidget(self.keep_aspect_check)
        
        size_layout.addLayout(dim_layout)
        
        # Size info
        self.size_info = QLabel()
        self.update_size_info()
        size_layout.addWidget(self.size_info)
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        # Metadata options
        metadata_group = QGroupBox("Metadata")
        metadata_layout = QVBoxLayout()
        
        self.strip_metadata_check = QCheckBox("Strip all metadata")
        self.strip_metadata_check.setChecked(False)
        metadata_layout.addWidget(self.strip_metadata_check)
        
        self.strip_location_check = QCheckBox("Strip location data")
        self.strip_location_check.setChecked(False)
        metadata_layout.addWidget(self.strip_location_check)
        
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)
        
        # Output options
        output_group = QGroupBox("Output")
        output_layout = QHBoxLayout()
        
        self.output_path_edit = QLabel("Not selected")
        output_layout.addWidget(self.output_path_edit)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(self.browse_btn)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export)
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        button_layout.addWidget(self.export_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Initial setup
        self.on_format_changed("JPEG")
    
    def on_format_changed(self, format):
        """Handle format change"""
        # Enable/disable quality based on format
        lossless_formats = ["PNG", "BMP", "TIFF"]
        if format in lossless_formats:
            self.quality_group.setEnabled(False)
        else:
            self.quality_group.setEnabled(True)
    
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
        
        self.update_size_info()
    
    def on_width_changed(self, value):
        """Handle width change for custom dimensions"""
        if self.keep_aspect_check.isChecked() and not self.pixmap.isNull():
            # Maintain aspect ratio
            aspect = self.pixmap.height() / self.pixmap.width()
            new_height = int(value * aspect)
            self.height_spin.blockSignals(True)
            self.height_spin.setValue(new_height)
            self.height_spin.blockSignals(False)
        
        self.update_size_info()
    
    def on_height_changed(self, value):
        """Handle height change for custom dimensions"""
        if self.keep_aspect_check.isChecked() and not self.pixmap.isNull():
            # Maintain aspect ratio
            aspect = self.pixmap.width() / self.pixmap.height()
            new_width = int(value * aspect)
            self.width_spin.blockSignals(True)
            self.width_spin.setValue(new_width)
            self.width_spin.blockSignals(False)
        
        self.update_size_info()
    
    def update_size_info(self):
        """Update size information display"""
        if self.pixmap.isNull():
            self.size_info.setText("No image loaded")
            return
        
        original_size = f"Original: {self.pixmap.width()} x {self.pixmap.height()}"
        
        if self.percentage_radio.isChecked():
            scale = self.percentage_spin.value() / 100.0
            new_width = int(self.pixmap.width() * scale)
            new_height = int(self.pixmap.height() * scale)
            self.size_info.setText(f"{original_size} → Output: {new_width} x {new_height}")
        
        elif self.custom_size_radio.isChecked():
            self.size_info.setText(f"{original_size} → Output: {self.width_spin.value()} x {self.height_spin.value()}")
        
        else:
            self.size_info.setText(original_size)
    
    def browse_output(self):
        """Browse for output file"""
        format = self.format_combo.currentText().lower()
        if format == 'jpeg':
            format = 'jpg'
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            "",
            f"{format.upper()} files (*.{format});;All files (*.*)"
        )
        
        if filepath:
            self.output_path_edit.setText(filepath)
            self.export_btn.setEnabled(True)
    
    def get_export_options(self):
        """Get current export options"""
        options = {
            'format': self.format_combo.currentText(),
            'quality': self.quality_slider.value() if self.quality_group.isEnabled() else None,
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
        if filepath:
            options = self.get_export_options()
            self.export_requested.emit(filepath, options)
            self.accept()