from PyQt5.QtWidgets import QToolTip, QWidget,QSlider,QSpinBox,QDoubleSpinBox
from PyQt5.QtCore import QTimer, QPoint, Qt, QObject
from PyQt5.QtGui import QFont

class TooltipManager(QObject):  # Must inherit from QObject
    """Manage tooltips for all UI elements"""
    
    TOOLTIPS = {
        # File operations
        'open_btn': 'Open an image file (Ctrl+O)',
        'save_btn': 'Save the current image (Ctrl+S)',
        'export_btn': 'Export image with custom options (Ctrl+E)',
        'batch_btn': 'Process multiple images at once',
        
        # Basic adjustments
        'brightness_slider': 'Adjust image brightness (-100 to +100)',
        'contrast_slider': 'Adjust image contrast (-100 to +100)',
        'saturation_slider': 'Adjust color saturation (-100 to +100)',
        'sharpness_slider': 'Adjust image sharpness (-100 to +100)',
        'hue_spin': 'Adjust hue rotation (-180 to +180)',
        'gamma_spin': 'Adjust gamma correction (0.1 to 3.0)',
        
        # Transformations
        'rotate_left_btn': 'Rotate image 90° counter-clockwise',
        'rotate_right_btn': 'Rotate image 90° clockwise',
        'flip_h_btn': 'Flip image horizontally',
        'flip_v_btn': 'Flip image vertically',
        'crop_btn': 'Crop image to selected area (Ctrl+Shift+C)',
        'resize_apply_btn': 'Resize image to specified dimensions',
        'resize_width_spin': 'Set new width for resize',
        'resize_height_spin': 'Set new height for resize',
        
        # Filters
        'blur_btn': 'Apply Gaussian blur filter',
        'edge_enhance_btn': 'Enhance edges in the image',
        
        # History
        'undo_btn': 'Undo last operation (Ctrl+Z)',
        'redo_btn': 'Redo last undone operation (Ctrl+Y)',
        'reset_btn': 'Reset to original image (Ctrl+R)',
        'compare_btn': 'Compare current image with original (Ctrl+D)',
        
        # AI tools
        'ai_enhance_btn': 'Automatically enhance image using AI',
        'ai_denoise_btn': 'Remove noise from image (Ctrl+N)',
        'ai_resolution_btn': 'Increase image resolution using AI (Ctrl+U)',
        'apply_style_btn': 'Apply artistic style to image',
        'ai_background_btn': 'Remove background from image (Ctrl+B)',
        'ai_facial_btn': 'Enhance facial features in portrait (Ctrl+F)',
        'colorize_btn': 'Colorize black and white images',
        
        # Style transfer
        'style_combo': 'Select artistic style to apply',
        
        # Zoom controls
        'zoom_in_btn': 'Zoom in (Ctrl++)',
        'zoom_out_btn': 'Zoom out (Ctrl+-)',
        'fit_btn': 'Fit image to window (Ctrl+0)',
        'actual_btn': 'Show actual size (Ctrl+1)',
        
        # Layer controls
        'layer_mode_btn': 'Toggle layer editing mode',
        'add_layer_btn': 'Add new layer',
        'delete_layer_btn': 'Delete selected layer',
        'duplicate_layer_btn': 'Duplicate selected layer',
        'merge_btn': 'Merge selected layers',
        'flatten_btn': 'Flatten all layers',
        
        # Batch processing
        'add_files_btn': 'Add image files to batch list',
        'add_folder_btn': 'Add all images from a folder',
        'clear_btn': 'Clear file list',
        'recursive_check': 'Include images in subfolders',
        'start_btn': 'Start batch processing',
        'batch_resize_width': 'Target width for batch resize',
        'batch_resize_height': 'Target height for batch resize',
        'batch_brightness_factor': 'Brightness adjustment factor (0.1-3.0)',
        'batch_contrast_factor': 'Contrast adjustment factor (0.1-3.0)',
        'batch_format_combo': 'Output format for converted images',
        
        # Export options
        'format_combo': 'Select output format',
        'quality_slider': 'Set image quality (higher = better quality, larger file)',
        'strip_metadata_check': 'Remove metadata from exported image',
        'keep_aspect_check': 'Maintain original aspect ratio when resizing'
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.show_tooltip)
        self.current_widget = None
        self.current_pos = None
        self.tooltips_enabled = True
        
    def setup_tooltips(self, widget: QWidget):
        """Setup tooltips for all child widgets"""
        for child in widget.findChildren(QWidget):
            if child.objectName() in self.TOOLTIPS:
                child.setToolTip(self.TOOLTIPS[child.objectName()])
                child.setToolTipDuration(5000)  # 5 seconds
                
                # Install event filter for custom tooltip handling
                child.installEventFilter(self)
    
    def set_tooltips_enabled(self, enabled: bool):
        """Enable or disable tooltips"""
        self.tooltips_enabled = enabled
        if not enabled:
            self.timer.stop()
            QToolTip.hideText()
    
    def eventFilter(self, obj, event):
        """Custom event filter for advanced tooltip handling"""
        if not self.tooltips_enabled:
            return super().eventFilter(obj, event)
            
        if event.type() == event.Enter:
            # Start timer for delayed tooltip
            self.current_widget = obj
            self.current_pos = event.globalPos()
            self.timer.start(500)  # 500ms delay
            
        elif event.type() == event.Leave:
            # Cancel timer
            self.timer.stop()
            self.current_widget = None
            QToolTip.hideText()
            
        elif event.type() == event.MouseMove:
            # Update position for tooltip
            self.current_pos = event.globalPos()
            
        return super().eventFilter(obj, event)
    
    def show_tooltip(self):
        """Show custom tooltip"""
        if self.current_widget and self.current_pos and self.tooltips_enabled:
            text = self.current_widget.toolTip()
            if text:
                # Add extra info for certain widgets
                if isinstance(self.current_widget, QSlider):
                    value = self.current_widget.value()
                    text += f"\nCurrent value: {value}"
                elif isinstance(self.current_widget, QSpinBox):
                    value = self.current_widget.value()
                    text += f"\nCurrent value: {value}"
                elif isinstance(self.current_widget, QDoubleSpinBox):
                    value = self.current_widget.value()
                    text += f"\nCurrent value: {value:.2f}"
                
                QToolTip.showText(self.current_pos, text, self.current_widget)
    
    @staticmethod
    def add_tooltip(widget: QWidget, text: str, shortcut: str = None):
        """Add tooltip to widget with optional shortcut"""
        if shortcut:
            text += f" ({shortcut})"
        widget.setToolTip(text)
        widget.setToolTipDuration(5000)
        widget.setStatusTip(text)  # Also show in status bar