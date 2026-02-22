"""
Histogram widget — displays RGB channel histograms for the currently loaded image.
Uses QPainter for rendering; no external plotting library required.
"""
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPolygon, QFont
from PIL import Image

class HistogramCanvas(QWidget):
    """Custom widget that paints RGB channel histograms."""

    CHANNEL_COLORS = {
        'R': QColor(239, 68, 68, 180),
        'G': QColor(34, 197, 94, 180),
        'B': QColor(59, 130, 246, 180),
        'L': QColor(200, 200, 200, 180),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setMaximumHeight(160)
        self._histograms = {}
        self._mode = 'RGB'
        self._show_channels = ['R', 'G', 'B']
        self._global_max = 1
        self.setObjectName("histogram_widget")
        self.setAttribute(Qt.WA_StyledBackground, True)

    def update_histogram(self, image):
        """Compute and store histogram data from a PIL Image."""
        if image is None:
            self._histograms = {}
            self._global_max = 1
            self.update()
            return

        try:
            # Convert PIL Image to numpy array
            if isinstance(image, Image.Image):
                arr = np.array(image)
                mode = image.mode
            else:
                # Assume it's already a numpy array
                arr = image
                mode = 'RGB' if len(arr.shape) == 3 else 'L'

            if mode == 'L' or len(arr.shape) == 2:
                self._mode = 'L'
                self._show_channels = ['L']
                hist, _ = np.histogram(arr.ravel(), bins=256, range=(0, 256))
                self._histograms = {'L': hist.astype(np.float32)}
            elif mode in ('RGB', 'RGBA') or (len(arr.shape) == 3 and arr.shape[2] >= 3):
                self._mode = 'RGB'
                self._show_channels = ['R', 'G', 'B']
                self._histograms = {}
                for i, ch in enumerate(['R', 'G', 'B']):
                    channel_data = arr[:, :, i].ravel()
                    hist, _ = np.histogram(channel_data, bins=256, range=(0, 256))
                    self._histograms[ch] = hist.astype(np.float32)
            else:
                # Convert to RGB if possible
                if isinstance(image, Image.Image):
                    rgb_image = image.convert('RGB')
                    arr = np.array(rgb_image)
                    self._mode = 'RGB'
                    self._show_channels = ['R', 'G', 'B']
                    self._histograms = {}
                    for i, ch in enumerate(['R', 'G', 'B']):
                        hist, _ = np.histogram(arr[:, :, i].ravel(), bins=256, range=(0, 256))
                        self._histograms[ch] = hist.astype(np.float32)
                else:
                    self._histograms = {}

            # Calculate global max for scaling (ignore extreme ends)
            self._global_max = 1
            for hist in self._histograms.values():
                if len(hist) > 10:
                    # Use 95th percentile to avoid spikes
                    p95 = np.percentile(hist[10:246], 95)
                    if p95 > self._global_max:
                        self._global_max = p95

            self.update()
        except Exception as e:
            print(f"Error updating histogram: {e}")
            self._histograms = {}
            self._global_max = 1
            self.update()

    def paintEvent(self, event):
        """Custom paint event for histogram rendering."""
        if not self._histograms:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QColor(100, 100, 120))
            painter.drawText(self.rect(), Qt.AlignCenter, "No image loaded")
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        pad = 8

        # Ensure we have valid dimensions
        if w <= 2 * pad or h <= 2 * pad:
            return

        draw_rect = QRect(pad, pad, w - 2 * pad, h - 2 * pad)

        # Background
        painter.fillRect(draw_rect, QColor(15, 17, 23, 200))

        # Grid lines
        grid_pen = QPen(QColor(50, 60, 80, 120))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        
        # Horizontal grid lines (4 divisions)
        for i in range(1, 4):
            y = draw_rect.top() + (draw_rect.height() * i) // 4
            painter.drawLine(draw_rect.left(), y, draw_rect.right(), y)
        
        # Vertical grid lines (8 divisions)
        for i in range(1, 8):
            x = draw_rect.left() + (draw_rect.width() * i) // 8
            painter.drawLine(x, draw_rect.top(), x, draw_rect.bottom())

        dw = draw_rect.width()
        dh = draw_rect.height()
        bin_w = dw / 256.0

        # Draw histograms for each channel
        for ch in self._show_channels:
            if ch not in self._histograms:
                continue
                
            hist = self._histograms[ch]
            color = self.CHANNEL_COLORS.get(ch, QColor(200, 200, 200, 150))
            
            # Create polygon for filled histogram
            points = []
            points.append(QPoint(draw_rect.left(), draw_rect.bottom()))
            
            for i in range(256):
                x = int(draw_rect.left() + i * bin_w)
                # Ensure x is within bounds
                x = max(draw_rect.left(), min(x, draw_rect.right()))
                
                # Get histogram value and scale
                val = hist[i] if i < len(hist) else 0
                if self._global_max > 0:
                    bar_h = int((val / self._global_max) * dh)
                else:
                    bar_h = 0
                    
                # Clamp bar height
                bar_h = min(bar_h, dh)
                y = draw_rect.bottom() - bar_h
                points.append(QPoint(x, y))
            
            points.append(QPoint(draw_rect.right(), draw_rect.bottom()))
            
            # Draw filled polygon
            polygon = QPolygon(points)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 1))
            painter.drawPolygon(polygon)

        # Draw border
        painter.setPen(QPen(QColor(60, 70, 90), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(draw_rect)

        # Draw channel indicators at the bottom
        painter.setPen(QPen(QColor(180, 180, 200), 1))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        x_pos = draw_rect.left() + 5
        for ch in self._show_channels:
            if ch in self.CHANNEL_COLORS:
                color = self.CHANNEL_COLORS[ch]
                painter.setPen(QPen(color, 1))
                painter.drawText(x_pos, draw_rect.bottom() + 15, ch)
                x_pos += 25

    def resizeEvent(self, event):
        """Handle resize event to force redraw."""
        self.update()
        super().resizeEvent(event)


class HistogramWidget(QWidget):
    """Full histogram panel with channel labels and live update."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header row
        header = QHBoxLayout()
        title = QLabel("Histogram")
        title.setObjectName("section_header")
        header.addWidget(title)
        header.addStretch()

        # Channel indicators with color squares
        colors = [
            ('R', '#ef4444', 'Red channel'),
            ('G', '#22c55e', 'Green channel'),
            ('B', '#3b82f6', 'Blue channel')
        ]
        
        for ch, hex_color, tooltip in colors:
            lbl = QLabel(f"■ {ch}")
            lbl.setStyleSheet(f"color: {hex_color}; font-size: 11px; font-weight: bold;")
            lbl.setToolTip(tooltip)
            header.addWidget(lbl)

        layout.addLayout(header)

        self.canvas = HistogramCanvas()
        layout.addWidget(self.canvas)

        # Stats row
        self.stats_label = QLabel("")
        self.stats_label.setObjectName("info_label")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setWordWrap(True)
        self.stats_label.setMinimumHeight(20)
        layout.addWidget(self.stats_label)

    def update_from_image(self, image):
        """Update histogram from a PIL Image."""
        if image is None:
            self.canvas.update_histogram(None)
            self.stats_label.setText("")
            return

        try:
            # Update histogram
            self.canvas.update_histogram(image)
            
            # Calculate and display statistics
            if isinstance(image, Image.Image):
                # Convert to RGB for statistics
                rgb_image = image.convert('RGB')
                arr = np.array(rgb_image)
                
                if len(arr.shape) == 3 and arr.shape[2] >= 3:
                    # Calculate statistics for each channel
                    means = []
                    stds = []
                    for i in range(3):
                        channel = arr[:, :, i].ravel()
                        means.append(np.mean(channel))
                        stds.append(np.std(channel))
                    
                    # Overall stats
                    overall_mean = np.mean(means)
                    overall_std = np.mean(stds)
                    
                    self.stats_label.setText(
                        f"R:{means[0]:.0f} G:{means[1]:.0f} B:{means[2]:.0f} | "
                        f"σ:{overall_std:.1f}"
                    )
                else:
                    # Grayscale image
                    arr = np.array(image)
                    mean_val = np.mean(arr)
                    std_val = np.std(arr)
                    self.stats_label.setText(f"Mean: {mean_val:.0f} | Std: {std_val:.1f}")
            else:
                self.stats_label.setText("")
                
        except Exception as e:
            print(f"Error updating histogram stats: {e}")
            self.stats_label.setText("")

    def clear(self):
        """Clear the histogram display."""
        self.canvas._histograms = {}
        self.canvas._global_max = 1
        self.stats_label.setText("")
        self.canvas.update()