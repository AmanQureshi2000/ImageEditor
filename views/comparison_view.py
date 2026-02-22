from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPixmap
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
        self.mode = 'vertical'  # 'vertical' or 'horizontal'
        self.dragging = False
        
        # Cache for scaled versions
        self.cache = CacheManager(max_size_mb=100, max_items=10)
        self.last_size = None
        
        self.setWindowTitle("Before/After Comparison")
        self.setGeometry(150, 150, 900, 600)
        self.setWindowFlags(Qt.Window)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize comparison view UI"""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Mode selection
        self.vertical_btn = QPushButton("Vertical Split")
        self.vertical_btn.clicked.connect(lambda: self.set_mode('vertical'))
        self.vertical_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        toolbar.addWidget(self.vertical_btn)
        
        self.horizontal_btn = QPushButton("Horizontal Split")
        self.horizontal_btn.clicked.connect(lambda: self.set_mode('horizontal'))
        toolbar.addWidget(self.horizontal_btn)
        
        self.swipe_btn = QPushButton("Swipe Mode")
        self.swipe_btn.clicked.connect(lambda: self.set_mode('swipe'))
        toolbar.addWidget(self.swipe_btn)
        
        toolbar.addStretch()
        
        # Split position control
        toolbar.addWidget(QLabel("Split:"))
        self.split_slider = QSlider(Qt.Horizontal)
        self.split_slider.setRange(0, 100)
        self.split_slider.setValue(50)
        self.split_slider.valueChanged.connect(self.on_slider_changed)
        toolbar.addWidget(self.split_slider)
        
        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("background-color: #f44336; color: white;")
        toolbar.addWidget(self.close_btn)
        
        layout.addLayout(toolbar)
        
        # Info label
        self.info_label = QLabel("Drag the slider or split line to compare before/after")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
    def set_mode(self, mode):
        """Set comparison mode"""
        self.mode = mode
        
        # Update button styles
        for btn in [self.vertical_btn, self.horizontal_btn, self.swipe_btn]:
            btn.setStyleSheet("")
        
        if mode == 'vertical':
            self.vertical_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        elif mode == 'horizontal':
            self.horizontal_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        else:
            self.swipe_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.update()
    
    def on_slider_changed(self, value):
        """Handle slider value change"""
        self.split_position = value / 100.0
        self.update()
    
    def _get_scaled_pixmaps(self, display_rect):
        """Get scaled pixmaps with caching"""
        size_key = f"{display_rect.width()}x{display_rect.height()}"
        
        # Check cache
        cached = self.cache.get(size_key)
        if cached:
            return cached['before'], cached['after']
        
        # Scale pixmaps
        scaled_before = self.original_before.scaled(
            display_rect.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        scaled_after = self.original_after.scaled(
            display_rect.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        # Cache results
        self.cache.put(size_key, {
            'before': scaled_before,
            'after': scaled_after
        })
        
        return scaled_before, scaled_after
    
    def paintEvent(self, event):
        """Custom paint event with caching"""
        if self.original_before.isNull() or self.original_after.isNull():
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate area for image display (exclude toolbar)
        toolbar_height = 80
        display_rect = QRect(0, toolbar_height, self.width(), self.height() - toolbar_height)
        
        # Get scaled pixmaps from cache
        scaled_before, scaled_after = self._get_scaled_pixmaps(display_rect)
        
        # Calculate position to center images
        x = display_rect.x() + (display_rect.width() - scaled_before.width()) // 2
        y = display_rect.y() + (display_rect.height() - scaled_before.height()) // 2
        
        if self.mode == 'vertical':
            # Vertical split
            split_x = x + int(scaled_before.width() * self.split_position)
            
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
            
            # Draw handles
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(split_x - 10, y + scaled_before.height()//2 - 10, 20, 20)
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.drawEllipse(split_x - 5, y + scaled_before.height()//2 - 5, 10, 10)
            
        elif self.mode == 'horizontal':
            # Horizontal split
            split_y = y + int(scaled_before.height() * self.split_position)
            
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
            
            # Draw handles
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(x + scaled_before.width()//2 - 10, split_y - 10, 20, 20)
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.drawEllipse(x + scaled_before.width()//2 - 5, split_y - 5, 10, 10)
            
        else:  # swipe mode
            # Show before image
            painter.drawPixmap(x, y, scaled_before)
            
            # Draw after image with circular reveal
            center_x = x + int(scaled_before.width() * self.split_position)
            center_y = y + int(scaled_before.height() * self.split_position)
            radius = int(min(scaled_before.width(), scaled_before.height()) * 0.3)
            
            painter.save()
            
            # Create circular clip
            path = painter.clipRegion()
            painter.setClipRect(display_rect)
            painter.setClipRect(QRect(center_x - radius, center_y - radius, radius*2, radius*2))
            
            painter.drawPixmap(x, y, scaled_after)
            painter.restore()
            
            # Draw circle border
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center_x - radius, center_y - radius, radius*2, radius*2)
            
            # Draw handles
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center_x - 10, center_y - 10, 20, 20)
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.drawEllipse(center_x - 5, center_y - 5, 10, 10)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging split line"""
        if event.button() == Qt.LeftButton and event.y() > 80:  # Below toolbar
            self.dragging = True
            self.update_split_from_pos(event.pos())
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging split line"""
        if self.dragging:
            self.update_split_from_pos(event.pos())
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.dragging = False
    
    def update_split_from_pos(self, pos):
        """Update split position based on mouse position"""
        display_rect = QRect(0, 80, self.width(), self.height() - 80)
        
        if display_rect.contains(pos):
            if self.mode == 'vertical':
                # Calculate percentage from left
                x = max(display_rect.left(), min(pos.x(), display_rect.right()))
                self.split_position = (x - display_rect.left()) / display_rect.width()
            elif self.mode == 'horizontal':
                # Calculate percentage from top
                y = max(display_rect.top(), min(pos.y(), display_rect.bottom()))
                self.split_position = (y - display_rect.top()) / display_rect.height()
            else:  # swipe mode
                # Calculate relative position for center
                x = max(display_rect.left(), min(pos.x(), display_rect.right()))
                y = max(display_rect.top(), min(pos.y(), display_rect.bottom()))
                self.split_position_x = (x - display_rect.left()) / display_rect.width()
                self.split_position_y = (y - display_rect.top()) / display_rect.height()
            
            # Update slider without triggering valueChanged
            self.split_slider.blockSignals(True)
            self.split_slider.setValue(int(self.split_position * 100))
            self.split_slider.blockSignals(False)
            
            self.update()
    
    def resizeEvent(self, event):
        """Handle resize event to clear cache"""
        self.cache.clear()  # Clear cache on resize
        super().resizeEvent(event)