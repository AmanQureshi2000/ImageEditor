"""
AI Image Generation Dialog — full-featured dialog for generating images
from text prompts using free AI APIs (Pollinations.ai).
"""
import random
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSlider, QGroupBox, QTextEdit,
    QScrollArea, QWidget, QCheckBox, QSpinBox, QSizePolicy,
    QApplication, QMessageBox, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor, QPainter, QPen
from PIL import Image
import io
import numpy as np

# Try to import the image gen model, with fallback
try:
    from models.image_gen_model import ImageGenModel
except ImportError:
    # Create a placeholder if the model doesn't exist yet
    class ImageGenModel:
        PROVIDERS = {"Pollinations.ai": "pollinations"}
        ASPECT_RATIOS = {"Square (1:1)": (1024, 1024), "Landscape (16:9)": (1216, 832), "Portrait (9:16)": (832, 1216)}
        STYLE_PRESETS = {"None": "", "Photorealistic": "photorealistic", "Anime": "anime", "Digital Art": "digital-art"}
        NEGATIVE_PRESETS = {"Default": "blurry, low quality, watermark, text", "Strict": "blurry, low quality, watermark, text, ugly, deformed, bad anatomy"}
        
        def generate(self, prompt, provider, width, height, seed=-1, style_preset="", negative_prompt="", progress_callback=None, status_callback=None):
            if progress_callback:
                for i in range(0, 101, 10):
                    progress_callback(i)
            if status_callback:
                status_callback("Generating placeholder image...")
            # Return a simple gradient image as placeholder
            img = Image.new('RGB', (width, height), color=(73, 109, 137))
            return img
            
        def cancel(self):
            pass


class GenerationWorker(QThread):
    """Worker thread for image generation."""

    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(object)    # PIL Image or None
    error = pyqtSignal(str)

    def __init__(self, model: ImageGenModel, params: dict):
        super().__init__()
        self.model = model
        self.params = params

    def run(self):
        try:
            img = self.model.generate(
                prompt=self.params['prompt'],
                provider=self.params['provider'],
                width=self.params['width'],
                height=self.params['height'],
                seed=self.params.get('seed', -1),
                style_preset=self.params.get('style_preset', ''),
                negative_prompt=self.params.get('negative_prompt', ''),
                progress_callback=lambda v: self.progress.emit(v),
                status_callback=lambda s: self.status.emit(s),
            )
            self.finished.emit(img)
        except RuntimeError as e:
            if 'cancelled' in str(e).lower():
                self.finished.emit(None)
            else:
                self.error.emit(str(e))
        except Exception as e:
            self.error.emit(str(e))


class SpinnerWidget(QLabel):
    """Animated spinner label."""

    FRAMES = ["◐", "◓", "◑", "◒"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._frame = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.setAlignment(Qt.AlignCenter)
        self.setObjectName("spinner_label")
        font = QFont()
        font.setPointSize(24)
        self.setFont(font)
        self.hide()

    def start(self):
        self._frame = 0
        self.setText(self.FRAMES[0])
        self.show()
        self._timer.start(150)

    def stop(self):
        self._timer.stop()
        self.hide()

    def _tick(self):
        self._frame = (self._frame + 1) % len(self.FRAMES)
        self.setText(self.FRAMES[self._frame])


class ImagePreviewLabel(QLabel):
    """Zoomable image preview label inside the dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._pil_image = None
        self.setObjectName("gen_preview")
        self.setStyleSheet("QLabel#gen_preview { background-color: #1a1f2e; border: 1px solid #2a3347; border-radius: 8px; }")
        self._draw_placeholder()

    def _draw_placeholder(self):
        w, h = 400, 400
        pixmap = QPixmap(w, h)
        pixmap.fill(QColor(26, 31, 46))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw dashed border
        pen = QPen(QColor(60, 70, 100))
        pen.setStyle(Qt.DashLine)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRoundedRect(20, 20, w - 40, h - 40, 12, 12)
        
        # Draw text
        painter.setPen(QColor(80, 90, 120))
        font = QFont("Segoe UI", 14)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "✨\n\nGenerated image\nwill appear here")
        painter.end()
        self.setPixmap(pixmap)

    def set_pil_image(self, pil_img: Image.Image):
        self._pil_image = pil_img
        self._update_pixmap()

    def get_pil_image(self) -> Image.Image:
        return self._pil_image

    def _update_pixmap(self):
        if self._pil_image is None:
            self._draw_placeholder()
            return
        
        # Convert PIL to QImage
        img = self._pil_image.convert("RGB")
        data = img.tobytes("raw", "RGB")
        qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
        
        # Create pixmap and scale
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(
            self.size().width() - 20, 
            self.size().height() - 20,
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pil_image:
            self._update_pixmap()


class ImageGenDialog(QDialog):
    """
    Full-featured AI image generation dialog.
    Emits image_generated(PIL.Image) when the user accepts.
    """

    image_generated = pyqtSignal(object)

    PROMPT_EXAMPLES = [
        "A majestic snow-capped mountain at golden hour, photorealistic",
        "A cyberpunk city at night with neon lights reflecting on rain-soaked streets",
        "A serene Japanese garden with cherry blossoms in spring",
        "A cozy coffee shop interior with warm lighting and books",
        "An astronaut floating in space with a colorful nebula behind them",
        "A fantasy dragon flying over a medieval castle at sunset",
        "A minimalist abstract art piece with geometric shapes in pastel colors",
        "An underwater scene with bioluminescent jellyfish and coral reefs",
        "A retro-futuristic cityscape from the 1980s, synthwave style",
        "A cute fox sitting in an autumn forest surrounded by fallen leaves",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Image Generation")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.resize(1100, 720)
        self.setMinimumSize(900, 600)
        self.setModal(True)

        self.gen_model = ImageGenModel()
        self.worker = None
        self._generated_image = None
        self.negative_preset_combo = None  # Will be initialized in UI

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Left: controls
        controls_widget = QWidget()
        controls_widget.setMaximumWidth(420)
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setSpacing(12)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title_label = QLabel("✨ AI Image Generation")
        title_label.setObjectName("gen_title")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        controls_layout.addWidget(title_label)

        sub_label = QLabel("Powered by Pollinations.ai — Free & No API key required")
        sub_label.setObjectName("gen_subtitle")
        sub_font = QFont()
        sub_font.setPointSize(10)
        sub_label.setFont(sub_font)
        controls_layout.addWidget(sub_label)

        controls_layout.addWidget(self._make_separator())

        # Prompt group
        prompt_group = QGroupBox("Prompt")
        prompt_layout = QVBoxLayout(prompt_group)
        prompt_layout.setSpacing(6)

        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText(
            "Describe the image you want to generate...\n"
            "Be specific and detailed for best results."
        )
        self.prompt_edit.setMinimumHeight(90)
        self.prompt_edit.setMaximumHeight(130)
        prompt_layout.addWidget(self.prompt_edit)

        # Example prompts button
        example_row = QHBoxLayout()
        example_btn = QPushButton("💡 Random Example")
        example_btn.clicked.connect(self._load_random_example)
        example_btn.setToolTip("Load a random example prompt")
        example_row.addWidget(example_btn)

        clear_btn = QPushButton("✕ Clear")
        clear_btn.clicked.connect(self.prompt_edit.clear)
        example_row.addWidget(clear_btn)
        prompt_layout.addLayout(example_row)

        controls_layout.addWidget(prompt_group)

        # Style group
        style_group = QGroupBox("Style & Negative Prompt")
        style_layout = QVBoxLayout(style_group)
        style_layout.setSpacing(6)

        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style Preset:"))
        self.style_combo = QComboBox()
        # Get style presets from model or use defaults
        style_presets = list(getattr(ImageGenModel, 'STYLE_PRESETS', {"None": ""}).keys())
        self.style_combo.addItems(style_presets if style_presets else ["None"])
        style_row.addWidget(self.style_combo)
        style_layout.addLayout(style_row)

        style_layout.addWidget(QLabel("Negative Prompt (what to avoid):"))
        self.negative_edit = QTextEdit()
        self.negative_edit.setPlaceholderText("e.g. blurry, low quality, watermark...")
        self.negative_edit.setMaximumHeight(60)
        
        # Set default negative prompt
        default_negative = getattr(ImageGenModel, 'NEGATIVE_PRESETS', {}).get("Default", 
            "blurry, low quality, watermark, text, ugly, deformed")
        self.negative_edit.setText(default_negative)
        
        # Add negative preset selector
        negative_preset_layout = self._make_negative_preset_row()
        if negative_preset_layout:
            style_layout.addLayout(negative_preset_layout)
        
        style_layout.addWidget(self.negative_edit)

        controls_layout.addWidget(style_group)

        # Settings group
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(8)

        # Provider
        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel("Model:"))
        self.provider_combo = QComboBox()
        providers = list(getattr(ImageGenModel, 'PROVIDERS', {"Pollinations.ai": "pollinations"}).keys())
        self.provider_combo.addItems(providers)
        provider_row.addWidget(self.provider_combo)
        settings_layout.addLayout(provider_row)

        # Aspect ratio
        aspect_row = QHBoxLayout()
        aspect_row.addWidget(QLabel("Size:"))
        self.aspect_combo = QComboBox()
        aspect_ratios = list(getattr(ImageGenModel, 'ASPECT_RATIOS', 
            {"Square (1:1)": (1024, 1024)}).keys())
        self.aspect_combo.addItems(aspect_ratios)
        aspect_row.addWidget(self.aspect_combo)
        settings_layout.addLayout(aspect_row)

        # Seed
        seed_row = QHBoxLayout()
        seed_row.addWidget(QLabel("Seed:"))
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(-1, 2147483647)
        self.seed_spin.setValue(-1)
        self.seed_spin.setSpecialValueText("Random")
        self.seed_spin.setToolTip("Set -1 for random seed each time")
        seed_row.addWidget(self.seed_spin)
        random_seed_btn = QPushButton("🎲")
        random_seed_btn.setFixedWidth(36)
        random_seed_btn.setToolTip("Generate random seed")
        random_seed_btn.clicked.connect(lambda: self.seed_spin.setValue(random.randint(1, 999999)))
        seed_row.addWidget(random_seed_btn)
        settings_layout.addLayout(seed_row)

        controls_layout.addWidget(settings_group)

        # Action buttons
        btn_layout = QVBoxLayout()
        self.generate_btn = QPushButton("🚀 Generate Image")
        self.generate_btn.setObjectName("generate_btn")
        self.generate_btn.setMinimumHeight(42)
        self.generate_btn.clicked.connect(self._start_generation)
        btn_layout.addWidget(self.generate_btn)

        self.cancel_btn = QPushButton("⏹ Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_generation)
        btn_layout.addWidget(self.cancel_btn)

        controls_layout.addLayout(btn_layout)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        controls_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setObjectName("info_label")
        self.status_label.setWordWrap(True)
        controls_layout.addWidget(self.status_label)

        controls_layout.addStretch()

        # Accept / use image buttons at bottom
        accept_layout = QHBoxLayout()
        self.use_btn = QPushButton("✓ Use This Image")
        self.use_btn.setObjectName("generate_btn")
        self.use_btn.setEnabled(False)
        self.use_btn.setMinimumHeight(36)
        self.use_btn.clicked.connect(self._accept_image)
        accept_layout.addWidget(self.use_btn)

        close_btn = QPushButton("✕ Close")
        close_btn.setMinimumHeight(36)
        close_btn.clicked.connect(self.reject)
        accept_layout.addWidget(close_btn)

        controls_layout.addLayout(accept_layout)

        main_layout.addWidget(controls_widget)

        # Right: preview
        preview_frame = QFrame()
        preview_frame.setObjectName("gen_card")
        preview_frame.setStyleSheet("QFrame#gen_card { background-color: #1a1f2e; border-radius: 12px; }")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        preview_layout.setSpacing(8)

        preview_header = QHBoxLayout()
        preview_title = QLabel("Preview")
        preview_title.setObjectName("section_header")
        preview_title_font = QFont()
        preview_title_font.setPointSize(14)
        preview_title_font.setBold(True)
        preview_title.setFont(preview_title_font)
        preview_header.addWidget(preview_title)
        preview_header.addStretch()

        self.spinner = SpinnerWidget()
        self.spinner.setFixedSize(48, 48)
        preview_header.addWidget(self.spinner)

        preview_layout.addLayout(preview_header)

        # Scroll area for preview (to handle large images)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.preview_label = ImagePreviewLabel()
        scroll_area.setWidget(self.preview_label)
        preview_layout.addWidget(scroll_area)

        # Generation info
        self.gen_info_label = QLabel("")
        self.gen_info_label.setObjectName("info_label")
        self.gen_info_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.gen_info_label)

        main_layout.addWidget(preview_frame, stretch=1)

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("QFrame { background-color: #2a3347; max-height: 1px; }")
        return line

    def _make_negative_preset_row(self):
        """Create negative prompt preset selector if presets exist."""
        negative_presets = getattr(ImageGenModel, 'NEGATIVE_PRESETS', {})
        if not negative_presets:
            return None
            
        row = QHBoxLayout()
        row.addWidget(QLabel("Preset:"))
        self.negative_preset_combo = QComboBox()
        self.negative_preset_combo.addItems(list(negative_presets.keys()))
        self.negative_preset_combo.currentTextChanged.connect(
            lambda t: self.negative_edit.setText(negative_presets.get(t, ""))
        )
        row.addWidget(self.negative_preset_combo)
        return row

    def _load_random_example(self):
        example = random.choice(self.PROMPT_EXAMPLES)
        self.prompt_edit.setPlainText(example)

    def _start_generation(self):
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Empty Prompt", "Please enter a description for the image.")
            return

        provider_name = self.provider_combo.currentText()
        providers_dict = getattr(ImageGenModel, 'PROVIDERS', {"Pollinations.ai": "pollinations"})
        provider_key = providers_dict.get(provider_name, "pollinations")

        aspect_name = self.aspect_combo.currentText()
        aspect_dict = getattr(ImageGenModel, 'ASPECT_RATIOS', {"Square (1:1)": (1024, 1024)})
        w, h = aspect_dict.get(aspect_name, (1024, 1024))

        style_name = self.style_combo.currentText()
        style_dict = getattr(ImageGenModel, 'STYLE_PRESETS', {"None": ""})
        style_preset = style_dict.get(style_name, "")

        negative_prompt = self.negative_edit.toPlainText().strip()
        seed = self.seed_spin.value()

        params = {
            'prompt': prompt,
            'provider': provider_key,
            'width': w,
            'height': h,
            'seed': seed,
            'style_preset': style_preset,
            'negative_prompt': negative_prompt,
        }

        self._set_generating_state(True)
        self.status_label.setText("Initializing...")
        self.progress_bar.setValue(0)

        self.worker = GenerationWorker(self.gen_model, params)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.status_label.setText)
        self.worker.finished.connect(self._on_generation_finished)
        self.worker.error.connect(self._on_generation_error)
        self.worker.start()

    def _cancel_generation(self):
        if self.worker and self.worker.isRunning():
            self.gen_model.cancel()
            self.status_label.setText("Cancelling...")
            self.cancel_btn.setEnabled(False)

    def _on_generation_finished(self, img):
        self._set_generating_state(False)
        if img is None:
            self.status_label.setText("Generation cancelled.")
            return
        self._generated_image = img
        self.preview_label.set_pil_image(img)
        self.use_btn.setEnabled(True)
        self.gen_info_label.setText(
            f"Generated: {img.width} × {img.height} px"
        )
        self.status_label.setText("Image ready! Click 'Use This Image' to apply.")
        self.progress_bar.setValue(100)

    def _on_generation_error(self, error_msg):
        self._set_generating_state(False)
        self.status_label.setText(f"Error: {error_msg[:120]}")
        self.progress_bar.setValue(0)
        QMessageBox.critical(
            self, "Generation Failed",
            f"Image generation failed:\n\n{error_msg}\n\n"
            "Tips:\n• Check your internet connection\n"
            "• Try a simpler prompt\n"
            "• Try a different model"
        )

    def _set_generating_state(self, generating: bool):
        self.generate_btn.setEnabled(not generating)
        self.cancel_btn.setEnabled(generating)
        self.progress_bar.setVisible(generating)
        if generating:
            self.spinner.start()
            self.use_btn.setEnabled(False)
        else:
            self.spinner.stop()

    def _accept_image(self):
        if self._generated_image is not None:
            self.image_generated.emit(self._generated_image)
            self.accept()

    def get_generated_image(self) -> Image.Image:
        return self._generated_image

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.gen_model.cancel()
            self.worker.wait(3000)
        super().closeEvent(event)