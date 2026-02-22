from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint, QEvent
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPixmap, QRegion, QCursor
from utils.cache_manager import CacheManager

class ComparisonView(QWidget):
    """Split view for before/after image comparison with caching"""
    
    closed = pyqtSignal()
    
    def __init__(self, before_pixmap: QPixmap, after_pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.original_before = before_pixmap
        self.original_after = after_pixmap
        self.cached_before = None
        self.cached_after = None
        self.split_position = 0.5  # 0 to 1, percentage from left
        self.split_position_x = 0.5  # For swipe mode x position
        self.split_position_y = 0.5  # For swipe mode y position
        self.mode = 'vertical'  # 'vertical', 'horizontal', or 'swipe'
        self.dragging = False
        self.drag_start = QPoint()
        self.image_rect = None  # Will store the actual image display rectangle
        
        # Cache for scaled versions
        self.cache = CacheManager(max_size_mb=100, max_items=10)
        self.last_size = None
        self.last_before = None
        self.last_after = None
        
        self.setWindowTitle("Before/After Comparison")
        self.setGeometry(150, 150, 900, 600)
        self.setWindowFlags(Qt.Window)
        
        # Set minimum size
        self.setMinimumSize(400, 300)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize comparison view UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Toolbar layout
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)
        
        # Mode selection buttons
        self.vertical_btn = QPushButton("Vertical Split")
        self.vertical_btn.setObjectName("primary_btn")
        self.vertical_btn.clicked.connect(lambda: self.set_mode('vertical'))
        self.vertical_btn.setFixedHeight(30)
        toolbar.addWidget(self.vertical_btn)

        self.horizontal_btn = QPushButton("Horizontal Split")
        self.horizontal_btn.setObjectName("")
        self.horizontal_btn.clicked.connect(lambda: self.set_mode('horizontal'))
        self.horizontal_btn.setFixedHeight(30)
        toolbar.addWidget(self.horizontal_btn)

        self.swipe_btn = QPushButton("Swipe Mode")
        self.swipe_btn.setObjectName("")
        self.swipe_btn.clicked.connect(lambda: self.set_mode('swipe'))
        self.swipe_btn.setFixedHeight(30)
        toolbar.addWidget(self.swipe_btn)
        
        toolbar.addStretch()
        
        # Split position control
        toolbar.addWidget(QLabel("Split:"))
        self.split_slider = QSlider(Qt.Horizontal)
        self.split_slider.setRange(0, 100)
        self.split_slider.setValue(50)
        self.split_slider.setFixedWidth(150)
        self.split_slider.valueChanged.connect(self.on_slider_changed)
        toolbar.addWidget(self.split_slider)
        
        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("danger_btn")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setFixedHeight(30)
        self.close_btn.setFixedWidth(80)
        toolbar.addWidget(self.close_btn)
        
        main_layout.addLayout(toolbar)
        
        # Info label
        self.info_label = QLabel("Drag the slider or split line to compare before/after")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setFixedHeight(25)
        main_layout.addWidget(self.info_label)
        
        # Add stretch to push everything to the top
        main_layout.addStretch()
        
    def set_mode(self, mode):
        """Set comparison mode"""
        self.mode = mode
        
        # Update button styling
        self.vertical_btn.setObjectName("primary_btn" if mode == 'vertical' else "")
        self.horizontal_btn.setObjectName("primary_btn" if mode == 'horizontal' else "")
        self.swipe_btn.setObjectName("primary_btn" if mode == 'swipe' else "")
        
        # Force style refresh
        app = QApplication.instance()
        if app:
            for btn in [self.vertical_btn, self.horizontal_btn, self.swipe_btn]:
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                btn.update()
        
        self.update()
    
    def on_slider_changed(self, value):
        """Handle slider value change"""
        self.split_position = value / 100.0
        # Update both x and y positions for swipe mode
        self.split_position_x = self.split_position
        self.split_position_y = self.split_position
        self.update()
    
    def _get_scaled_pixmaps(self, available_rect):
        """Get scaled pixmaps with caching"""
        # Check if we already have cached versions for this size
        current_size = (available_rect.width(), available_rect.height())
        if (self.last_size == current_size and 
            self.last_before is not None and 
            self.last_after is not None):
            return self.last_before, self.last_after
        
        # Check cache
        size_key = f"{available_rect.width()}x{available_rect.height()}"
        cached = self.cache.get(size_key)
        if cached and isinstance(cached, dict):
            self.last_before = cached.get('before', self.original_before)
            self.last_after = cached.get('after', self.original_after)
            self.last_size = current_size
            return self.last_before, self.last_after
        
        # Scale pixmaps to fit available space while maintaining aspect ratio
        if not self.original_before.isNull():
            scaled_before = self.original_before.scaled(
                available_rect.width(),
                available_rect.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            scaled_before = QPixmap()
            
        if not self.original_after.isNull():
            scaled_after = self.original_after.scaled(
                available_rect.width(),
                available_rect.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            scaled_after = QPixmap()
        
        # Cache results
        if not scaled_before.isNull() and not scaled_after.isNull():
            self.cache.put(size_key, {
                'before': scaled_before,
                'after': scaled_after
            })
        
        self.last_before = scaled_before
        self.last_after = scaled_after
        self.last_size = current_size
        
        return scaled_before, scaled_after
    
    def paintEvent(self, event):
        """Custom paint event with caching"""
        if self.original_before.isNull() or self.original_after.isNull():
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(40, 40, 40))
            painter.setPen(Qt.white)
            painter.drawText(self.rect(), Qt.AlignCenter, "No images to compare")
            return
        
        # Calculate available space for images (excluding toolbar and info label)
        toolbar_height = 70  # Fixed height for toolbar + info label
        
        # Ensure toolbar_height doesn't exceed widget height
        if toolbar_height > self.height() - 20:
            toolbar_height = max(20, self.height() - 40)
        
        # Available rectangle for image display
        available_rect = QRect(
            10,  # left margin
            toolbar_height,  # top margin
            max(1, self.width() - 20),  # width minus margins
            max(1, self.height() - toolbar_height - 10)  # height minus margins
        )
        
        # Get scaled pixmaps
        scaled_before, scaled_after = self._get_scaled_pixmaps(available_rect)
        
        # Check if scaling was successful
        if scaled_before.isNull() or scaled_after.isNull():
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(40, 40, 40))
            painter.setPen(Qt.white)
            painter.drawText(self.rect(), Qt.AlignCenter, "Error loading images")
            return
        
        # Calculate position to center images in available space
        x = available_rect.x() + (available_rect.width() - scaled_before.width()) // 2
        y = available_rect.y() + (available_rect.height() - scaled_before.height()) // 2
        
        # Store image rectangle for mouse interaction
        self.image_rect = QRect(x, y, scaled_before.width(), scaled_before.height())
        
        # Start painting
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Clear the area with dark background
        painter.fillRect(available_rect, QColor(40, 40, 40))
        
        if self.mode == 'vertical':
            # Vertical split
            split_x = x + int(scaled_before.width() * self.split_position)
            split_x = max(x, min(split_x, x + scaled_before.width()))
            
            # Draw before image (left side)
            painter.drawPixmap(x, y, scaled_before)
            
            # Draw after image (right side) with clipping
            painter.save()
            painter.setClipRect(split_x, y, scaled_before.width() - (split_x - x), scaled_before.height())
            painter.drawPixmap(x, y, scaled_after)
            painter.restore()
            
            # Draw split line
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.drawLine(split_x, y, split_x, y + scaled_before.height())
            
            # Draw handle
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(split_x - 10, y + scaled_before.height()//2 - 10, 20, 20)
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.drawEllipse(split_x - 5, y + scaled_before.height()//2 - 5, 10, 10)
            
        elif self.mode == 'horizontal':
            # Horizontal split
            split_y = y + int(scaled_before.height() * self.split_position)
            split_y = max(y, min(split_y, y + scaled_before.height()))
            
            # Draw before image (top)
            painter.drawPixmap(x, y, scaled_before)
            
            # Draw after image (bottom) with clipping
            painter.save()
            painter.setClipRect(x, split_y, scaled_before.width(), scaled_before.height() - (split_y - y))
            painter.drawPixmap(x, y, scaled_after)
            painter.restore()
            
            # Draw split line
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.drawLine(x, split_y, x + scaled_before.width(), split_y)
            
            # Draw handle
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(x + scaled_before.width()//2 - 10, split_y - 10, 20, 20)
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.drawEllipse(x + scaled_before.width()//2 - 5, split_y - 5, 10, 10)
            
        else:  # swipe mode
            # Draw before image (full)
            painter.drawPixmap(x, y, scaled_before)
            
            # Calculate circle position
            center_x = x + int(scaled_before.width() * self.split_position_x)
            center_y = y + int(scaled_before.height() * self.split_position_y)
            center_x = max(x, min(center_x, x + scaled_before.width()))
            center_y = max(y, min(center_y, y + scaled_before.height()))
            
            radius = int(min(scaled_before.width(), scaled_before.height()) * 0.2)
            radius = max(10, min(radius, 200))  # Limit radius size
            
            # Draw after image with circular clipping
            painter.save()
            
            # Create circular region
            circle_rect = QRect(center_x - radius, center_y - radius, radius * 2, radius * 2)
            region = QRegion(circle_rect, QRegion.Ellipse)
            painter.setClipRegion(region)
            
            painter.drawPixmap(x, y, scaled_after)
            painter.restore()
            
            # Draw circle border
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
            
            # Draw center handle
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center_x - 8, center_y - 8, 16, 16)
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.drawEllipse(center_x - 4, center_y - 4, 8, 8)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging split line"""
        if event.button() == Qt.LeftButton and self.image_rect:
            # Check if click is within image area
            if self.image_rect.contains(event.pos()):
                self.dragging = True
                self.drag_start = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                self.update_split_from_pos(event.pos())
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging split line"""
        if self.dragging and self.image_rect:
            self.update_split_from_pos(event.pos())
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if self.dragging:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)
    
    def update_split_from_pos(self, pos):
        """Update split position based on mouse position"""
        if not self.image_rect:
            return
        
        # Constrain position to image bounds
        if self.image_rect.contains(pos):
            if self.mode == 'vertical':
                # Calculate percentage from left within image
                x = max(self.image_rect.left(), min(pos.x(), self.image_rect.right()))
                self.split_position = (x - self.image_rect.left()) / self.image_rect.width()
                
            elif self.mode == 'horizontal':
                # Calculate percentage from top within image
                y = max(self.image_rect.top(), min(pos.y(), self.image_rect.bottom()))
                self.split_position = (y - self.image_rect.top()) / self.image_rect.height()
                
            else:  # swipe mode
                # Calculate relative position for center
                x = max(self.image_rect.left(), min(pos.x(), self.image_rect.right()))
                y = max(self.image_rect.top(), min(pos.y(), self.image_rect.bottom()))
                self.split_position_x = (x - self.image_rect.left()) / self.image_rect.width()
                self.split_position_y = (y - self.image_rect.top()) / self.image_rect.height()
                # Average for slider (just for visual feedback)
                self.split_position = (self.split_position_x + self.split_position_y) / 2
            
            # Update slider without triggering valueChanged
            self.split_slider.blockSignals(True)
            self.split_slider.setValue(int(self.split_position * 100))
            self.split_slider.blockSignals(False)
            
            self.update()
    
    def resizeEvent(self, event):
        """Handle resize event to clear cache"""
        self.cache.clear()  # Clear cache on resize
        self.image_rect = None  # Reset image rectangle
        self.last_size = None  # Reset cached size
        self.last_before = None
        self.last_after = None
        super().resizeEvent(event)
    
    def closeEvent(self, event):
        """Handle close event"""
        self.closed.emit()
        super().closeEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)