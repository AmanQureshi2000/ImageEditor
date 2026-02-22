from PyQt5.QtWidgets import QLabel, QScrollArea
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor

class ImageView(QLabel):
    """Custom image view widget with zoom and pan capabilities"""
    
    zoom_changed = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        
        self.original_pixmap = None
        self.scaled_pixmap = None
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # For panning
        self.panning = False
        self.last_pan_point = None
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
    def setPixmap(self, pixmap: QPixmap):
        """Set the pixmap and update display"""
        self.original_pixmap = pixmap
        self.update_display()
        
    def update_display(self):
        """Update the displayed pixmap with current zoom"""
        if self.original_pixmap and not self.original_pixmap.isNull():
            # Calculate new size
            new_width = int(self.original_pixmap.width() * self.zoom_factor)
            new_height = int(self.original_pixmap.height() * self.zoom_factor)
            
            # Scale the pixmap
            self.scaled_pixmap = self.original_pixmap.scaled(
                new_width, new_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            super().setPixmap(self.scaled_pixmap)
            self.zoom_changed.emit(self.zoom_factor)
            
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
        if self.original_pixmap and self.parent():
            parent = self.parent()
            while parent and not isinstance(parent, QScrollArea):
                parent = parent.parent()
            
            if parent and isinstance(parent, QScrollArea):
                view_width = parent.viewport().width()
                view_height = parent.viewport().height()
                
                # Calculate zoom factor to fit
                width_ratio = view_width / self.original_pixmap.width()
                height_ratio = view_height / self.original_pixmap.height()
                
                self.zoom_factor = min(width_ratio, height_ratio, 1.0)
                self.update_display()
            
    def zoom_actual(self):
        """Zoom to actual size"""
        self.zoom_factor = 1.0
        self.update_display()
        
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        if event.modifiers() == Qt.ControlModifier:
            # Zoom with Ctrl + wheel
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)
            
    def mousePressEvent(self, event):
        """Handle mouse press for panning"""
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.AltModifier:
            self.panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for panning"""
        if self.panning and self.last_pan_point:
            # Calculate delta
            delta = event.pos() - self.last_pan_point
            
            # Scroll the parent scroll area
            parent = self.parent()
            while parent and not isinstance(parent, QScrollArea):
                parent = parent.parent()
                
            if parent and isinstance(parent, QScrollArea):
                h_bar = parent.horizontalScrollBar()
                v_bar = parent.verticalScrollBar()
                
                h_bar.setValue(h_bar.value() - delta.x())
                v_bar.setValue(v_bar.value() - delta.y())
                
            self.last_pan_point = event.pos()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton and self.panning:
            self.panning = False
            self.last_pan_point = None
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)