from PyQt5.QtWidgets import QToolTip, QWidget, QSlider, QSpinBox, QDoubleSpinBox
from PyQt5.QtCore import QTimer, QPoint, Qt, QObject, QEvent
from PyQt5.QtGui import QFont, QHelpEvent,QCursor

class TooltipManager(QObject):
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
        'keep_aspect_check': 'Maintain original aspect ratio when resizing',
        
        # Menu items
        'file_menu': 'File operations - Open, Save, Export, Exit',
        'edit_menu': 'Edit operations - Undo, Redo, Reset',
        'image_menu': 'Image transformations - Crop, Resize, Rotate, Flip',
        'filter_menu': 'Apply filters to image',
        'ai_menu': 'AI-powered image enhancements',
        'view_menu': 'View options - Compare, Zoom',
        'layer_menu': 'Layer management',
        'tools_menu': 'Tools and preferences',
        'help_menu': 'Help and about',
        
        # Toolbar items
        'toolbar_open': 'Open image (Ctrl+O)',
        'toolbar_save': 'Save image (Ctrl+S)',
        'toolbar_undo': 'Undo last operation (Ctrl+Z)',
        'toolbar_redo': 'Redo last operation (Ctrl+Y)',
        'toolbar_crop': 'Crop image (Ctrl+Shift+C)',
        'toolbar_rotate': 'Rotate image 90° right',
        'toolbar_auto': 'Auto enhance image',
        'toolbar_denoise': 'Remove noise',
        'toolbar_style': 'Apply style transfer',
        'toolbar_compare': 'Compare before/after (Ctrl+D)',
        'toolbar_layers': 'Toggle layer mode',
        
        # Status bar items
        'status_label': 'Current status',
        'progress_bar': 'Operation progress',
        'theme_indicator': 'Current theme',
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
        if not widget:
            return
            
        for child in widget.findChildren(QWidget):
            if child.objectName() and child.objectName() in self.TOOLTIPS:
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
        
        # Handle tooltip events
        if event.type() == QEvent.ToolTip:
            # Let Qt handle normal tooltips
            return False
            
        elif event.type() == QEvent.Enter:
            # Start timer for delayed custom tooltip
            self.current_widget = obj
            self.current_pos = event.globalPos() if hasattr(event, 'globalPos') else QCursor.pos()
            self.timer.start(500)  # 500ms delay
            return False
            
        elif event.type() == QEvent.Leave:
            # Cancel timer
            self.timer.stop()
            self.current_widget = None
            QToolTip.hideText()
            return False
            
        elif event.type() == QEvent.MouseMove:
            # Update position for tooltip
            if hasattr(event, 'globalPos'):
                self.current_pos = event.globalPos()
            return False
            
        return super().eventFilter(obj, event)
    
    def show_tooltip(self):
        """Show custom tooltip"""
        if self.current_widget and self.current_pos and self.tooltips_enabled:
            text = self.current_widget.toolTip()
            if text:
                # Add extra info for certain widget types
                if isinstance(self.current_widget, QSlider):
                    value = self.current_widget.value()
                    minimum = self.current_widget.minimum()
                    maximum = self.current_widget.maximum()
                    text += f"\nCurrent value: {value} (Range: {minimum} to {maximum})"
                elif isinstance(self.current_widget, QSpinBox):
                    value = self.current_widget.value()
                    text += f"\nCurrent value: {value}"
                elif isinstance(self.current_widget, QDoubleSpinBox):
                    value = self.current_widget.value()
                    text += f"\nCurrent value: {value:.2f}"
                
                # Show tooltip at stored position
                QToolTip.showText(self.current_pos, text, self.current_widget)
    
    @staticmethod
    def add_tooltip(widget: QWidget, text: str, shortcut: str = None):
        """Add tooltip to widget with optional shortcut"""
        if not widget:
            return
            
        if shortcut:
            text += f" ({shortcut})"
        widget.setToolTip(text)
        widget.setToolTipDuration(5000)
        widget.setStatusTip(text)  # Also show in status bar
    
    def remove_tooltips(self, widget: QWidget):
        """Remove tooltips from all child widgets"""
        if not widget:
            return
            
        for child in widget.findChildren(QWidget):
            child.setToolTip("")
            child.removeEventFilter(self)
    
    def refresh_tooltips(self, widget: QWidget):
        """Refresh tooltips for all child widgets"""
        self.remove_tooltips(widget)
        self.setup_tooltips(widget)
    
    def get_tooltip_text(self, object_name: str) -> str:
        """Get tooltip text for an object name"""
        return self.TOOLTIPS.get(object_name, "")
    
    def add_custom_tooltip(self, object_name: str, tooltip_text: str):
        """Add or update a custom tooltip in the dictionary"""
        if object_name and tooltip_text:
            self.TOOLTIPS[object_name] = tooltip_text
    
    def get_all_tooltips(self) -> dict:
        """Get all tooltips dictionary"""
        return self.TOOLTIPS.copy()