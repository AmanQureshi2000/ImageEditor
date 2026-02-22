from PyQt5.QtWidgets import QWidget, QRubberBand, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QApplication
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QEvent
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPixmap, QCursor

class CropTool(QWidget):
    """Visual crop tool with rubber band selection"""
    
    crop_completed = pyqtSignal(QRect)
    crop_cancelled = pyqtSignal()
    
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.original_pixmap = pixmap
        self.pixmap = pixmap.copy() if not pixmap.isNull() else QPixmap()
        self.setWindowTitle("Crop Image")
        self.setGeometry(100, 100, 800, 600)
        
        self.rubber_band = None
        self.origin = QPoint()
        self.selection_rect = None
        self.aspect_ratio = None  # None = free form, (w, h) = fixed ratio
        self.dragging = False
        self.resizing = False
        self.resize_handle = None
        self.handle_size = 8
        self.drag_start = QPoint()
        self.initial_rect = QRect()
        self.image_rect = QRect()  # Initialize image_rect
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize crop tool UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)
        
        # Aspect ratio controls
        toolbar.addWidget(QLabel("Aspect Ratio:"))
        
        self.free_btn = QPushButton("Free")
        self.free_btn.setObjectName("primary_btn")
        self.free_btn.clicked.connect(lambda: self.set_aspect_ratio(None))
        self.free_btn.setFixedHeight(30)
        toolbar.addWidget(self.free_btn)
        
        self.square_btn = QPushButton("1:1")
        self.square_btn.setObjectName("")
        self.square_btn.clicked.connect(lambda: self.set_aspect_ratio((1, 1)))
        self.square_btn.setFixedHeight(30)
        toolbar.addWidget(self.square_btn)
        
        self.ratio_4_3_btn = QPushButton("4:3")
        self.ratio_4_3_btn.setObjectName("")
        self.ratio_4_3_btn.clicked.connect(lambda: self.set_aspect_ratio((4, 3)))
        self.ratio_4_3_btn.setFixedHeight(30)
        toolbar.addWidget(self.ratio_4_3_btn)
        
        self.ratio_16_9_btn = QPushButton("16:9")
        self.ratio_16_9_btn.setObjectName("")
        self.ratio_16_9_btn.clicked.connect(lambda: self.set_aspect_ratio((16, 9)))
        self.ratio_16_9_btn.setFixedHeight(30)
        toolbar.addWidget(self.ratio_16_9_btn)
        
        toolbar.addStretch()
        
        # Custom ratio
        toolbar.addWidget(QLabel("Custom:"))
        self.ratio_w = QSpinBox()
        self.ratio_w.setRange(1, 100)
        self.ratio_w.setValue(2)
        self.ratio_w.setFixedWidth(60)
        toolbar.addWidget(self.ratio_w)
        
        toolbar.addWidget(QLabel(":"))
        
        self.ratio_h = QSpinBox()
        self.ratio_h.setRange(1, 100)
        self.ratio_h.setValue(3)
        self.ratio_h.setFixedWidth(60)
        toolbar.addWidget(self.ratio_h)
        
        self.set_custom_btn = QPushButton("Set")
        self.set_custom_btn.setObjectName("")
        self.set_custom_btn.clicked.connect(self.set_custom_aspect_ratio)
        self.set_custom_btn.setFixedHeight(30)
        toolbar.addWidget(self.set_custom_btn)
        
        layout.addLayout(toolbar)
        
        # Action buttons
        action_bar = QHBoxLayout()
        action_bar.setSpacing(5)
        
        self.crop_btn = QPushButton("Crop")
        self.crop_btn.setObjectName("primary_btn")
        self.crop_btn.clicked.connect(self.apply_crop)
        self.crop_btn.setEnabled(False)
        self.crop_btn.setFixedHeight(30)
        action_bar.addWidget(self.crop_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("danger_btn")
        self.cancel_btn.clicked.connect(self.cancel_crop)
        self.cancel_btn.setFixedHeight(30)
        action_bar.addWidget(self.cancel_btn)
        
        action_bar.addStretch()
        
        # Selection info
        self.info_label = QLabel("Click and drag to select crop area")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setFixedHeight(25)
        action_bar.addWidget(self.info_label)
        
        layout.addLayout(action_bar)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        # Set minimum size
        self.setMinimumSize(400, 300)
        
    def paintEvent(self, event):
        """Custom paint event for crop overlay"""
        if self.pixmap.isNull():
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(40, 40, 40))
            painter.setPen(Qt.white)
            painter.drawText(self.rect(), Qt.AlignCenter, "No image to crop")
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the image centered
        if not self.pixmap.isNull():
            # Scale pixmap to fit widget while maintaining aspect ratio
            scaled_pixmap = self.pixmap.scaled(
                self.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # Calculate position to center the image
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            
            # Store image rectangle for coordinate mapping
            self.image_rect = QRect(x, y, scaled_pixmap.width(), scaled_pixmap.height())
            
            # Draw the image
            painter.drawPixmap(x, y, scaled_pixmap)
            
            # Draw semi-transparent overlay
            painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
            painter.setPen(Qt.NoPen)
            
            if self.selection_rect and self.selection_rect.isValid():
                # Darken outside selection
                painter.drawRect(self.image_rect)
                
                # Clear the selection area
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.drawRect(self.selection_rect)
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                
                # Draw selection border
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(self.selection_rect)
                
                # Draw resize handles
                painter.setPen(QPen(QColor(0, 255, 0), 1))
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                self._draw_handles(painter, self.selection_rect)
                
                # Update info
                crop_w = self.selection_rect.width()
                crop_h = self.selection_rect.height()
                aspect = crop_w / crop_h if crop_h > 0 else 0
                self.info_label.setText(f"Selection: {crop_w} x {crop_h} (Aspect: {aspect:.2f})")
            else:
                # Darken the whole image
                painter.drawRect(self.image_rect)
                self.info_label.setText("Click and drag to select crop area")
    
    def _draw_handles(self, painter, rect):
        """Draw resize handles on selection rectangle"""
        handle_positions = [
            (rect.left(), rect.top()),  # Top-left
            (rect.right(), rect.top()),  # Top-right
            (rect.left(), rect.bottom()),  # Bottom-left
            (rect.right(), rect.bottom()),  # Bottom-right
            (rect.center().x(), rect.top()),  # Top-middle
            (rect.center().x(), rect.bottom()),  # Bottom-middle
            (rect.left(), rect.center().y()),  # Left-middle
            (rect.right(), rect.center().y()),  # Right-middle
        ]
        
        for x, y in handle_positions:
            painter.drawEllipse(x - self.handle_size//2, y - self.handle_size//2, 
                              self.handle_size, self.handle_size)
    
    def mousePressEvent(self, event):
        """Handle mouse press for starting selection"""
        if event.button() == Qt.LeftButton and self.image_rect.isValid():
            # Check if click is within image area
            if self.image_rect.contains(event.pos()):
                # Check if clicking on a resize handle
                if self.selection_rect and self.selection_rect.isValid():
                    handle = self._get_handle_at_pos(event.pos())
                    if handle:
                        self.resizing = True
                        self.resize_handle = handle
                        self.drag_start = event.pos()
                        self.initial_rect = QRect(self.selection_rect)
                        self.setCursor(Qt.ClosedHandCursor)
                        return
                
                # Start new selection
                self.origin = event.pos()
                if not self.rubber_band:
                    self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
                self.rubber_band.setGeometry(QRect(self.origin, self.origin))
                self.rubber_band.show()
                self.dragging = True
                self.setCursor(Qt.CrossCursor)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for selection/resize"""
        if self.dragging and self.rubber_band:
            # Update rubber band
            rect = QRect(self.origin, event.pos()).normalized()
            
            # Apply aspect ratio constraint
            if self.aspect_ratio:
                rect = self._apply_aspect_ratio(rect)
            
            # Constrain to image bounds
            rect = rect.intersected(self.image_rect)
            
            self.rubber_band.setGeometry(rect)
        elif self.resizing and self.selection_rect:
            # Handle resizing
            new_rect = QRect(self.selection_rect)
            delta = event.pos() - self.drag_start
            
            # Apply resize based on handle
            if self.resize_handle == 'top-left':
                new_rect.setTopLeft(self.initial_rect.topLeft() + delta)
            elif self.resize_handle == 'top-right':
                new_rect.setTopRight(self.initial_rect.topRight() + delta)
            elif self.resize_handle == 'bottom-left':
                new_rect.setBottomLeft(self.initial_rect.bottomLeft() + delta)
            elif self.resize_handle == 'bottom-right':
                new_rect.setBottomRight(self.initial_rect.bottomRight() + delta)
            elif self.resize_handle == 'top':
                new_rect.setTop(self.initial_rect.top() + delta.y())
            elif self.resize_handle == 'bottom':
                new_rect.setBottom(self.initial_rect.bottom() + delta.y())
            elif self.resize_handle == 'left':
                new_rect.setLeft(self.initial_rect.left() + delta.x())
            elif self.resize_handle == 'right':
                new_rect.setRight(self.initial_rect.right() + delta.x())
            
            # Apply aspect ratio if set
            if self.aspect_ratio:
                new_rect = self._apply_aspect_ratio(new_rect)
            
            # Constrain to image bounds
            new_rect = new_rect.intersected(self.image_rect)
            
            if new_rect.width() > 10 and new_rect.height() > 10:
                self.selection_rect = new_rect
                self.drag_start = event.pos()
                self.initial_rect = QRect(self.selection_rect)
                self.update()
        
        # Update cursor
        self._update_cursor(event.pos())
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if self.dragging and self.rubber_band:
            self.dragging = False
            self.selection_rect = self.rubber_band.geometry()
            self.rubber_band.hide()
            self.crop_btn.setEnabled(True)
            self.update()
        elif self.resizing:
            self.resizing = False
            self.resize_handle = None
            self.update()
        
        self.setCursor(Qt.ArrowCursor)
    
    def _get_handle_at_pos(self, pos):
        """Get resize handle at position"""
        if not self.selection_rect or not self.selection_rect.isValid():
            return None
        
        rect = self.selection_rect
        handle_positions = [
            (rect.topLeft(), 'top-left'),
            (rect.topRight(), 'top-right'),
            (rect.bottomLeft(), 'bottom-left'),
            (rect.bottomRight(), 'bottom-right'),
            (QPoint(rect.center().x(), rect.top()), 'top'),
            (QPoint(rect.center().x(), rect.bottom()), 'bottom'),
            (QPoint(rect.left(), rect.center().y()), 'left'),
            (QPoint(rect.right(), rect.center().y()), 'right'),
        ]
        
        for handle_pos, handle_name in handle_positions:
            if (abs(pos.x() - handle_pos.x()) <= self.handle_size and 
                abs(pos.y() - handle_pos.y()) <= self.handle_size):
                return handle_name
        return None
    
    def _update_cursor(self, pos):
        """Update cursor based on position"""
        handle = self._get_handle_at_pos(pos)
        if handle:
            if handle in ['top-left', 'bottom-right']:
                self.setCursor(Qt.SizeFDiagCursor)
            elif handle in ['top-right', 'bottom-left']:
                self.setCursor(Qt.SizeBDiagCursor)
            elif handle in ['top', 'bottom']:
                self.setCursor(Qt.SizeVerCursor)
            elif handle in ['left', 'right']:
                self.setCursor(Qt.SizeHorCursor)
        elif self.image_rect.contains(pos):
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
    
    def _apply_aspect_ratio(self, rect):
        """Apply aspect ratio constraint to rectangle"""
        if not self.aspect_ratio:
            return rect
        
        # Ensure positive dimensions
        rect = rect.normalized()
        
        target_ratio = self.aspect_ratio[0] / self.aspect_ratio[1]
        current_ratio = rect.width() / rect.height() if rect.height() > 0 else 0
        
        if abs(current_ratio - target_ratio) > 0.01:
            if current_ratio > target_ratio:
                # Too wide, adjust height
                new_height = int(rect.width() / target_ratio)
                rect.setHeight(new_height)
            else:
                # Too tall, adjust width
                new_width = int(rect.height() * target_ratio)
                rect.setWidth(new_width)
        
        return rect
    
    def set_aspect_ratio(self, ratio):
        """Set fixed aspect ratio for cropping"""
        self.aspect_ratio = ratio
        
        # Update primary state (active = primary_btn objectName for selected ratio)
        self.free_btn.setObjectName("primary_btn" if ratio is None else "")
        self.square_btn.setObjectName("primary_btn" if ratio == (1, 1) else "")
        self.ratio_4_3_btn.setObjectName("primary_btn" if ratio == (4, 3) else "")
        self.ratio_16_9_btn.setObjectName("primary_btn" if ratio == (16, 9) else "")
        
        # Re-apply style by refreshing
        app = QApplication.instance()
        if app:
            for btn in [self.free_btn, self.square_btn, self.ratio_4_3_btn, self.ratio_16_9_btn]:
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                btn.update()
        
        # Update current selection if exists
        if self.selection_rect and self.selection_rect.isValid() and self.aspect_ratio:
            self.selection_rect = self._apply_aspect_ratio(self.selection_rect)
            self.update()
    
    def set_custom_aspect_ratio(self):
        """Set custom aspect ratio from spin boxes"""
        w = self.ratio_w.value()
        h = self.ratio_h.value()
        self.set_aspect_ratio((w, h))
    
    def apply_crop(self):
        """Apply crop and emit result"""
        if self.selection_rect and self.selection_rect.isValid() and self.image_rect.isValid():
            # Convert screen coordinates to image coordinates
            scale_x = self.original_pixmap.width() / self.image_rect.width()
            scale_y = self.original_pixmap.height() / self.image_rect.height()
            
            image_x = int((self.selection_rect.x() - self.image_rect.x()) * scale_x)
            image_y = int((self.selection_rect.y() - self.image_rect.y()) * scale_y)
            image_w = int(self.selection_rect.width() * scale_x)
            image_h = int(self.selection_rect.height() * scale_y)
            
            # Ensure crop rectangle is within image bounds
            image_x = max(0, min(image_x, self.original_pixmap.width()))
            image_y = max(0, min(image_y, self.original_pixmap.height()))
            image_w = min(image_w, self.original_pixmap.width() - image_x)
            image_h = min(image_h, self.original_pixmap.height() - image_y)
            
            if image_w > 0 and image_h > 0:
                crop_rect = QRect(image_x, image_y, image_w, image_h)
                self.crop_completed.emit(crop_rect)
                self.close()
    
    def cancel_crop(self):
        """Cancel cropping"""
        self.crop_cancelled.emit()
        self.close()
    
    def resizeEvent(self, event):
        """Handle resize event"""
        self.update()
        super().resizeEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.cancel_crop()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.crop_btn.isEnabled():
                self.apply_crop()
        else:
            super().keyPressEvent(event)