from PyQt5.QtWidgets import QLabel, QScrollArea
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QWheelEvent, QMouseEvent

class ImageView(QLabel):
    """Custom image view widget with zoom and pan capabilities"""
    
    zoom_changed = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("image_view")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("QLabel#image_view { background-color: #1a1f2e; border: 1px solid #2a3347; }")
        
        self.original_pixmap = None
        self.scaled_pixmap = None
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # For panning
        self.panning = False
        self.last_pan_point = None
        self.pan_start_pos = QPoint()
        self.scroll_start_values = (0, 0)
        
        # For tracking
        self.is_overlay_visible = False
        self.mouse_position = QPoint()
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
    def setPixmap(self, pixmap: QPixmap):
        """Set the pixmap and update display"""
        self.original_pixmap = pixmap
        self.zoom_factor = 1.0  # Reset zoom when loading new image
        self.update_display()
        
    def update_display(self):
        """Update the displayed pixmap with current zoom"""
        if self.original_pixmap and not self.original_pixmap.isNull():
            # Calculate new size
            new_width = max(1, int(self.original_pixmap.width() * self.zoom_factor))
            new_height = max(1, int(self.original_pixmap.height() * self.zoom_factor))
            
            # Scale the pixmap
            self.scaled_pixmap = self.original_pixmap.scaled(
                new_width, new_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            super().setPixmap(self.scaled_pixmap)
            self.zoom_changed.emit(self.zoom_factor)
            self.update()
            
    def zoom_in(self):
        """Zoom in"""
        self.zoom_factor = min(self.zoom_factor * 1.2, self.max_zoom)
        self.update_display()
        
    def zoom_out(self):
        """Zoom out"""
        self.zoom_factor = max(self.zoom_factor / 1.2, self.min_zoom)
        self.update_display()
        
    def zoom_to_fit(self):
        """Zoom to fit the view"""
        if self.original_pixmap and not self.original_pixmap.isNull():
            # Find the parent scroll area
            parent = self.parent()
            while parent and not isinstance(parent, QScrollArea):
                parent = parent.parent()
            
            if parent and isinstance(parent, QScrollArea):
                view_width = parent.viewport().width()
                view_height = parent.viewport().height()
                
                # Calculate zoom factor to fit (with some padding)
                padding = 20
                available_width = view_width - padding
                available_height = view_height - padding
                
                if available_width > 0 and available_height > 0:
                    width_ratio = available_width / self.original_pixmap.width()
                    height_ratio = available_height / self.original_pixmap.height()
                    
                    self.zoom_factor = min(width_ratio, height_ratio, 1.0)
                    self.update_display()
                    
                    # Center the image
                    self._center_image()
            
    def zoom_actual(self):
        """Zoom to actual size"""
        self.zoom_factor = 1.0
        self.update_display()
        self._center_image()
        
    def _center_image(self):
        """Center the image in the scroll area"""
        parent = self.parent()
        while parent and not isinstance(parent, QScrollArea):
            parent = parent.parent()
        
        if parent and isinstance(parent, QScrollArea):
            h_bar = parent.horizontalScrollBar()
            v_bar = parent.verticalScrollBar()
            
            if h_bar and v_bar:
                h_bar.setValue((h_bar.maximum() - h_bar.minimum()) // 2)
                v_bar.setValue((v_bar.maximum() - v_bar.minimum()) // 2)
        
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming"""
        if event.modifiers() == Qt.ControlModifier:
            # Zoom with Ctrl + wheel
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # Scroll normally
            super().wheelEvent(event)
            
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for panning"""
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.AltModifier:
            self.panning = True
            self.last_pan_point = event.pos()
            self.pan_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            
            # Store current scroll bar positions
            parent = self._get_scroll_area()
            if parent:
                h_bar = parent.horizontalScrollBar()
                v_bar = parent.verticalScrollBar()
                if h_bar and v_bar:
                    self.scroll_start_values = (h_bar.value(), v_bar.value())
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for panning"""
        self.mouse_position = event.pos()
        
        if self.panning and self.last_pan_point:
            # Calculate delta
            delta = event.pos() - self.last_pan_point
            
            # Scroll the parent scroll area
            parent = self._get_scroll_area()
            if parent:
                h_bar = parent.horizontalScrollBar()
                v_bar = parent.verticalScrollBar()
                
                if h_bar and v_bar:
                    # Invert delta for natural panning
                    h_bar.setValue(h_bar.value() - delta.x())
                    v_bar.setValue(v_bar.value() - delta.y())
                
            self.last_pan_point = event.pos()
            
            # Show overlay with zoom info
            self.is_overlay_visible = True
            self.update()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton and self.panning:
            self.panning = False
            self.last_pan_point = None
            self.is_overlay_visible = False
            self.setCursor(Qt.ArrowCursor)
            self.update()
        else:
            super().mouseReleaseEvent(event)
            
    def leaveEvent(self, event):
        """Handle mouse leaving the widget"""
        self.is_overlay_visible = False
        self.update()
        super().leaveEvent(event)
        
    def _get_scroll_area(self):
        """Get the parent scroll area"""
        parent = self.parent()
        while parent and not isinstance(parent, QScrollArea):
            parent = parent.parent()
        return parent if isinstance(parent, QScrollArea) else None
        
    def paintEvent(self, event):
        """Custom paint event to add overlays"""
        super().paintEvent(event)
        
        # Draw overlay if needed
        if self.is_overlay_visible and self.original_pixmap:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw semi-transparent background for text
            text_rect = QRect(10, 10, 150, 60)
            painter.fillRect(text_rect, QColor(0, 0, 0, 180))
            
            # Draw zoom info
            painter.setPen(Qt.white)
            zoom_percent = int(self.zoom_factor * 100)
            painter.drawText(QRect(10, 10, 150, 25), Qt.AlignCenter, f"Zoom: {zoom_percent}%")
            
            # Draw image dimensions
            dim_text = f"{self.original_pixmap.width()} x {self.original_pixmap.height()}"
            painter.drawText(QRect(10, 35, 150, 25), Qt.AlignCenter, dim_text)
            
            # Draw panning hint
            if self.panning:
                painter.drawText(QRect(10, 60, 150, 25), Qt.AlignCenter, "Panning...")
                
            painter.end()
            
    def get_image_info(self) -> dict:
        """Get information about the current image"""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return {"error": "No image loaded"}
            
        return {
            "width": self.original_pixmap.width(),
            "height": self.original_pixmap.height(),
            "zoom": self.zoom_factor,
            "zoom_percent": int(self.zoom_factor * 100),
            "display_size": (self.scaled_pixmap.width() if self.scaled_pixmap else 0,
                           self.scaled_pixmap.height() if self.scaled_pixmap else 0)
        }
        
    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        # Optionally auto-fit on resize
        # self.zoom_to_fit()
        
    def has_image(self) -> bool:
        """Check if an image is loaded"""
        return self.original_pixmap is not None and not self.original_pixmap.isNull()
        
    def clear(self):
        """Clear the current image"""
        self.original_pixmap = None
        self.scaled_pixmap = None
        self.zoom_factor = 1.0
        super().clear()
        self.update()