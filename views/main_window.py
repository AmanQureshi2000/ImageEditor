from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog,
    QToolBar, QAction, QStatusBar, QProgressBar,
    QGroupBox, QSpinBox, QDoubleSpinBox,
    QComboBox, QSplitter, QScrollArea, QMenuBar,
    QMenu, QMessageBox, QListWidget, QDialog, QCheckBox,
    QTabWidget, QRadioButton, QButtonGroup, QActionGroup,QApplication
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from PIL import Image
import io
import os

from views.image_view import ImageView
from controllers.image_controller import ImageController
from controllers.ai_controller import AIController
from views.crop_tool import CropTool
from views.comparison_view import ComparisonView
from views.export_dialog import ExportDialog
from controllers.batch_controller import BatchController
from views.layer_panel import LayerPanel

# UX Improvements imports
from utils.theme_manager import ThemeManager
from utils.workspace_manager import WorkspaceManager
from utils.shortcut_manager import ShortcutManager, ShortcutDialog
from utils.tooltip_manager import TooltipManager


class MainWindow(QMainWindow):
    """Main application window with all UX improvements integrated"""

    def init_ai_controller(self):
        """Initialize AI controller with signals"""
        if hasattr(self.controller, 'image_model'):
            self.ai_controller = AIController(self.controller.image_model)
            self.connect_ai_signals()

    # Add this method to connect AI signals
    def connect_ai_signals(self):
        """Connect AI controller signals"""
        if self.ai_controller:
            self.ai_controller.ai_processing_started.connect(self.on_ai_started)
            self.ai_controller.ai_processing_finished.connect(self.on_ai_finished)
            self.ai_controller.ai_progress_updated.connect(self.update_progress)
            self.ai_controller.ai_status_updated.connect(self.update_status)
            self.ai_controller.ai_error_occurred.connect(self.on_ai_error)
            self.ai_controller.ai_result_ready.connect(self.on_ai_result)
    
    def __init__(self):
        super().__init__()
        self.controller = ImageController()
        self.ai_controller = None
        self.batch_controller = None
        self.crop_tool = None
        self.comparison_view = None
        self.export_dialog = None
        self.batch_dialog = None
        self.layer_panel = None
        
        # UX Improvements
        self.theme_manager = ThemeManager()
        self.workspace_manager = WorkspaceManager()
        self.shortcut_manager = ShortcutManager()
        self.tooltip_manager = TooltipManager()
        self.recent_files = []
        self.max_recent_files = 10
        
        # UI Elements that need to be accessible
        self.batch_file_list = None
        self.recursive_check = None
        self.resize_check = None
        self.resize_width = None
        self.resize_height = None
        self.brightness_check = None
        self.brightness_factor = None
        self.contrast_check = None
        self.contrast_factor = None
        self.format_check = None
        self.format_combo = None
        self.output_dir_label = None
        self.batch_progress = None
        
        self.init_ui()
        self.connect_signals()
        self.init_ai_controller()
        self.load_initial_data()
        
    def init_ui(self):
        """Initialize the complete user interface"""
        self.setWindowTitle("AI Image Editor & Enhancer - Professional Edition")
        self.setGeometry(100, 100, 1600, 900)
        self.setObjectName("MainWindow")
        
        # Apply theme
        self.theme_manager.apply_theme(QApplication.instance())
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("main_splitter")
        main_layout.addWidget(splitter)
        
        # Left panel - Tools (with tabs for Basic and Advanced)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Center panel - Image view
        center_panel = self.create_image_panel()
        splitter.addWidget(center_panel)
        
        # Right panel - AI Tools and Layers (tabbed)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([350, 800, 350])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create tool bar
        self.create_tool_bar()
        
        # Create status bar
        self.create_status_bar()
        
        # Setup tooltips
        self.tooltip_manager.setup_tooltips(self)
        
        # Load recent files
        self.recent_files = self.workspace_manager.load_recent_files()
        self.update_recent_files_menu()
        
    def load_initial_data(self):
        """Load initial data after UI creation"""
        # Load workspace
        self.workspace_manager.load_workspace(self)
        
    def create_status_bar(self):
        """Create enhanced status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add progress bar to status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.hide()
        self.progress_bar.setObjectName("progress_bar")
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("status_label")
        self.status_bar.addWidget(self.status_label)
        
        # Layer mode toggle
        self.layer_mode_btn = QPushButton("🎨 Layer Mode")
        self.layer_mode_btn.setCheckable(True)
        self.layer_mode_btn.clicked.connect(self.toggle_layer_mode)
        self.layer_mode_btn.setObjectName("layer_mode_btn")
        self.status_bar.addPermanentWidget(self.layer_mode_btn)
        
        # Theme indicator
        self.theme_indicator = QLabel(f"🎨 {self.theme_manager.current_theme.title()}")
        self.theme_indicator.setObjectName("theme_indicator")
        self.status_bar.addPermanentWidget(self.theme_indicator)
        
    def create_left_panel(self) -> QWidget:
        """Create left panel with all tools"""
        panel = QWidget()
        panel.setObjectName("left_panel")
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Create tab widget for different tool categories
        tab_widget = QTabWidget()
        tab_widget.setObjectName("left_tab_widget")
        
        # Tab 1: Basic Tools
        basic_tab = self.create_basic_tools_tab()
        tab_widget.addTab(basic_tab, "Basic")
        
        # Tab 2: Adjustments
        adjust_tab = self.create_adjustments_tab()
        tab_widget.addTab(adjust_tab, "Adjustments")
        
        # Tab 3: Filters
        filters_tab = self.create_filters_tab()
        tab_widget.addTab(filters_tab, "Filters")
        
        # Tab 4: Transform
        transform_tab = self.create_transform_tab()
        tab_widget.addTab(transform_tab, "Transform")
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def create_basic_tools_tab(self) -> QWidget:
        """Create basic tools tab"""
        widget = QWidget()
        widget.setObjectName("basic_tools_tab")
        layout = QVBoxLayout(widget)
        
        # File Operations Group
        file_group = QGroupBox("File Operations")
        file_group.setObjectName("file_group")
        file_layout = QVBoxLayout()
        
        self.open_btn = QPushButton("📂 Open Image")
        self.open_btn.setObjectName("open_btn")
        self.open_btn.clicked.connect(self.open_image)
        file_layout.addWidget(self.open_btn)
        
        self.save_btn = QPushButton("💾 Save Image")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.clicked.connect(self.save_image)
        self.save_btn.setEnabled(False)
        file_layout.addWidget(self.save_btn)
        
        self.export_btn = QPushButton("📤 Export Options")
        self.export_btn.setObjectName("export_btn")
        self.export_btn.clicked.connect(self.show_export_dialog)
        self.export_btn.setEnabled(False)
        file_layout.addWidget(self.export_btn)
        
        self.batch_btn = QPushButton("🔄 Batch Process")
        self.batch_btn.setObjectName("batch_btn")
        self.batch_btn.clicked.connect(self.show_batch_dialog)
        file_layout.addWidget(self.batch_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # History Group
        history_group = QGroupBox("History")
        history_group.setObjectName("history_group")
        history_layout = QHBoxLayout()
        
        self.undo_btn = QPushButton("↩ Undo")
        self.undo_btn.setObjectName("undo_btn")
        self.undo_btn.clicked.connect(self.controller.undo)
        history_layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("↪ Redo")
        self.redo_btn.setObjectName("redo_btn")
        self.redo_btn.clicked.connect(self.controller.redo)
        history_layout.addWidget(self.redo_btn)
        
        self.reset_btn = QPushButton("⟲ Reset")
        self.reset_btn.setObjectName("reset_btn")
        self.reset_btn.clicked.connect(self.controller.reset_image)
        history_layout.addWidget(self.reset_btn)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        # Compare Group
        compare_group = QGroupBox("Comparison")
        compare_group.setObjectName("compare_group")
        compare_layout = QVBoxLayout()
        
        self.compare_btn = QPushButton("👁 Compare Before/After")
        self.compare_btn.setObjectName("compare_btn")
        self.compare_btn.clicked.connect(self.show_comparison)
        compare_layout.addWidget(self.compare_btn)
        
        compare_group.setLayout(compare_layout)
        layout.addWidget(compare_group)
        
        layout.addStretch()
        return widget
    
    def create_adjustments_tab(self) -> QWidget:
        """Create adjustments tab"""
        widget = QWidget()
        widget.setObjectName("adjustments_tab")
        layout = QVBoxLayout(widget)
        
        # Basic Adjustments Group
        adjust_group = QGroupBox("Color Adjustments")
        adjust_group.setObjectName("color_adjustments_group")
        adjust_layout = QVBoxLayout()
        
        # Brightness
        brightness_layout = QVBoxLayout()
        brightness_layout.addWidget(QLabel("Brightness:"))
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setObjectName("brightness_slider")
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.adjust_brightness)
        brightness_layout.addWidget(self.brightness_slider)
        adjust_layout.addLayout(brightness_layout)
        
        # Contrast
        contrast_layout = QVBoxLayout()
        contrast_layout.addWidget(QLabel("Contrast:"))
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setObjectName("contrast_slider")
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.valueChanged.connect(self.adjust_contrast)
        contrast_layout.addWidget(self.contrast_slider)
        adjust_layout.addLayout(contrast_layout)
        
        # Saturation
        saturation_layout = QVBoxLayout()
        saturation_layout.addWidget(QLabel("Saturation:"))
        self.saturation_slider = QSlider(Qt.Horizontal)
        self.saturation_slider.setObjectName("saturation_slider")
        self.saturation_slider.setRange(-100, 100)
        self.saturation_slider.setValue(0)
        self.saturation_slider.valueChanged.connect(self.adjust_saturation)
        saturation_layout.addWidget(self.saturation_slider)
        adjust_layout.addLayout(saturation_layout)
        
        # Sharpness
        sharpness_layout = QVBoxLayout()
        sharpness_layout.addWidget(QLabel("Sharpness:"))
        self.sharpness_slider = QSlider(Qt.Horizontal)
        self.sharpness_slider.setObjectName("sharpness_slider")
        self.sharpness_slider.setRange(-100, 100)
        self.sharpness_slider.setValue(0)
        self.sharpness_slider.valueChanged.connect(self.adjust_sharpness)
        sharpness_layout.addWidget(self.sharpness_slider)
        adjust_layout.addLayout(sharpness_layout)
        
        # Reset sliders button
        reset_sliders_btn = QPushButton("Reset All")
        reset_sliders_btn.setObjectName("reset_sliders_btn")
        reset_sliders_btn.clicked.connect(self.reset_sliders)
        adjust_layout.addWidget(reset_sliders_btn)
        
        adjust_group.setLayout(adjust_layout)
        layout.addWidget(adjust_group)
        
        # Advanced Color Group
        advanced_color_group = QGroupBox("Advanced Color")
        advanced_color_group.setObjectName("advanced_color_group")
        advanced_color_layout = QVBoxLayout()
        
        # Hue
        hue_layout = QHBoxLayout()
        hue_layout.addWidget(QLabel("Hue:"))
        self.hue_spin = QSpinBox()
        self.hue_spin.setObjectName("hue_spin")
        self.hue_spin.setRange(-180, 180)
        self.hue_spin.setValue(0)
        self.hue_spin.valueChanged.connect(self.adjust_hue)
        hue_layout.addWidget(self.hue_spin)
        advanced_color_layout.addLayout(hue_layout)
        
        # Gamma
        gamma_layout = QHBoxLayout()
        gamma_layout.addWidget(QLabel("Gamma:"))
        self.gamma_spin = QDoubleSpinBox()
        self.gamma_spin.setObjectName("gamma_spin")
        self.gamma_spin.setRange(0.1, 3.0)
        self.gamma_spin.setValue(1.0)
        self.gamma_spin.setSingleStep(0.1)
        self.gamma_spin.valueChanged.connect(self.adjust_gamma)
        gamma_layout.addWidget(self.gamma_spin)
        advanced_color_layout.addLayout(gamma_layout)
        
        # Auto Enhance button
        self.auto_enhance_btn = QPushButton("✨ Auto Enhance")
        self.auto_enhance_btn.setObjectName("auto_enhance_btn")
        self.auto_enhance_btn.clicked.connect(self.controller.ai_auto_enhance)
        advanced_color_layout.addWidget(self.auto_enhance_btn)
        
        advanced_color_group.setLayout(advanced_color_layout)
        layout.addWidget(advanced_color_group)
        
        layout.addStretch()
        return widget
    
    def create_filters_tab(self) -> QWidget:
        """Create filters tab"""
        widget = QWidget()
        widget.setObjectName("filters_tab")
        layout = QVBoxLayout(widget)
        
        # Basic Filters Group
        basic_filters_group = QGroupBox("Basic Filters")
        basic_filters_group.setObjectName("basic_filters_group")
        basic_filters_layout = QVBoxLayout()
        
        self.blur_btn = QPushButton("🌀 Blur")
        self.blur_btn.setObjectName("blur_btn")
        self.blur_btn.clicked.connect(self.apply_blur)
        basic_filters_layout.addWidget(self.blur_btn)
        
        self.edge_enhance_btn = QPushButton("✏️ Edge Enhance")
        self.edge_enhance_btn.setObjectName("edge_enhance_btn")
        self.edge_enhance_btn.clicked.connect(self.controller.apply_edge_enhance)
        basic_filters_layout.addWidget(self.edge_enhance_btn)
        
        basic_filters_group.setLayout(basic_filters_layout)
        layout.addWidget(basic_filters_group)
        
        # AI Filters Group
        ai_filters_group = QGroupBox("AI Filters")
        ai_filters_group.setObjectName("ai_filters_group")
        ai_filters_layout = QVBoxLayout()
        
        self.ai_denoise_btn = QPushButton("🔇 Denoise")
        self.ai_denoise_btn.setObjectName("ai_denoise_btn")
        self.ai_denoise_btn.clicked.connect(self.ai_denoise)
        ai_filters_layout.addWidget(self.ai_denoise_btn)
        
        self.ai_resolution_btn = QPushButton("🔍 Super Resolution")
        self.ai_resolution_btn.setObjectName("ai_resolution_btn")
        self.ai_resolution_btn.clicked.connect(self.ai_enhance_resolution)
        ai_filters_layout.addWidget(self.ai_resolution_btn)
        
        ai_filters_group.setLayout(ai_filters_layout)
        layout.addWidget(ai_filters_group)
        
        layout.addStretch()
        return widget
    
    def create_transform_tab(self) -> QWidget:
        """Create transform tab"""
        widget = QWidget()
        widget.setObjectName("transform_tab")
        layout = QVBoxLayout(widget)
        
        # Rotation Group
        rotate_group = QGroupBox("Rotation")
        rotate_group.setObjectName("rotate_group")
        rotate_layout = QHBoxLayout()
        
        self.rotate_left_btn = QPushButton("↺ 90°")
        self.rotate_left_btn.setObjectName("rotate_left_btn")
        self.rotate_left_btn.clicked.connect(lambda: self.rotate_image(-90))
        rotate_layout.addWidget(self.rotate_left_btn)
        
        self.rotate_right_btn = QPushButton("↻ 90°")
        self.rotate_right_btn.setObjectName("rotate_right_btn")
        self.rotate_right_btn.clicked.connect(lambda: self.rotate_image(90))
        rotate_layout.addWidget(self.rotate_right_btn)
        
        rotate_group.setLayout(rotate_layout)
        layout.addWidget(rotate_group)
        
        # Flip Group
        flip_group = QGroupBox("Flip")
        flip_group.setObjectName("flip_group")
        flip_layout = QHBoxLayout()
        
        self.flip_h_btn = QPushButton("↔ Horizontal")
        self.flip_h_btn.setObjectName("flip_h_btn")
        self.flip_h_btn.clicked.connect(self.controller.flip_horizontal)
        flip_layout.addWidget(self.flip_h_btn)
        
        self.flip_v_btn = QPushButton("↕ Vertical")
        self.flip_v_btn.setObjectName("flip_v_btn")
        self.flip_v_btn.clicked.connect(self.controller.flip_vertical)
        flip_layout.addWidget(self.flip_v_btn)
        
        flip_group.setLayout(flip_layout)
        layout.addWidget(flip_group)
        
        # Crop Group
        crop_group = QGroupBox("Crop")
        crop_group.setObjectName("crop_group")
        crop_layout = QVBoxLayout()
        
        self.crop_btn = QPushButton("✂ Crop Tool")
        self.crop_btn.setObjectName("crop_btn")
        self.crop_btn.clicked.connect(self.show_crop_tool)
        crop_layout.addWidget(self.crop_btn)
        
        crop_group.setLayout(crop_layout)
        layout.addWidget(crop_group)
        
        # Resize Group
        resize_group = QGroupBox("Resize")
        resize_group.setObjectName("resize_group")
        resize_layout = QVBoxLayout()
        
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Width:"))
        self.resize_width_spin = QSpinBox()
        self.resize_width_spin.setObjectName("resize_width_spin")
        self.resize_width_spin.setRange(1, 10000)
        self.resize_width_spin.setValue(800)
        width_layout.addWidget(self.resize_width_spin)
        resize_layout.addLayout(width_layout)
        
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Height:"))
        self.resize_height_spin = QSpinBox()
        self.resize_height_spin.setObjectName("resize_height_spin")
        self.resize_height_spin.setRange(1, 10000)
        self.resize_height_spin.setValue(600)
        height_layout.addWidget(self.resize_height_spin)
        resize_layout.addLayout(height_layout)
        
        self.resize_apply_btn = QPushButton("Apply Resize")
        self.resize_apply_btn.setObjectName("resize_apply_btn")
        self.resize_apply_btn.clicked.connect(self.apply_resize)
        resize_layout.addWidget(self.resize_apply_btn)
        
        resize_group.setLayout(resize_layout)
        layout.addWidget(resize_group)
        
        layout.addStretch()
        return widget
        
    def create_image_panel(self) -> QWidget:
        """Create the center panel with image view and info"""
        panel = QWidget()
        panel.setObjectName("image_panel")
        layout = QVBoxLayout(panel)
        
        # Image view with scroll area
        scroll_area = QScrollArea()
        scroll_area.setObjectName("image_scroll_area")
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)
        scroll_area.setStyleSheet("QScrollArea { background-color: #2b2b2b; border: none; }")
        
        self.image_view = ImageView()
        self.image_view.setObjectName("image_view")
        scroll_area.setWidget(self.image_view)
        
        layout.addWidget(scroll_area)
        
        # Image info bar
        info_bar = QHBoxLayout()
        
        self.info_label = QLabel("No image loaded")
        self.info_label.setObjectName("info_label")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("QLabel { color: #888; padding: 5px; }")
        info_bar.addWidget(self.info_label)
        
        # Zoom controls
        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setObjectName("zoom_out_btn")
        zoom_out_btn.setFixedSize(30, 30)
        zoom_out_btn.clicked.connect(self.image_view.zoom_out)
        info_bar.addWidget(zoom_out_btn)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setObjectName("zoom_label")
        self.zoom_label.setFixedWidth(50)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        info_bar.addWidget(self.zoom_label)
        
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setObjectName("zoom_in_btn")
        zoom_in_btn.setFixedSize(30, 30)
        zoom_in_btn.clicked.connect(self.image_view.zoom_in)
        info_bar.addWidget(zoom_in_btn)
        
        fit_btn = QPushButton("Fit")
        fit_btn.setObjectName("fit_btn")
        fit_btn.setFixedSize(50, 30)
        fit_btn.clicked.connect(self.image_view.zoom_to_fit)
        info_bar.addWidget(fit_btn)
        
        actual_btn = QPushButton("100%")
        actual_btn.setObjectName("actual_btn")
        actual_btn.setFixedSize(50, 30)
        actual_btn.clicked.connect(self.image_view.zoom_actual)
        info_bar.addWidget(actual_btn)
        
        layout.addLayout(info_bar)
        
        # Connect zoom signal
        self.image_view.zoom_changed.connect(self.update_zoom_label)
        
        return panel
        
    def create_right_panel(self) -> QWidget:
        """Create the right panel with AI tools and layers"""
        panel = QWidget()
        panel.setObjectName("right_panel")
        layout = QVBoxLayout(panel)
        
        # Create tab widget
        tab_widget = QTabWidget()
        tab_widget.setObjectName("right_tab_widget")
        
        # AI Tools Tab
        ai_tab = self.create_ai_tools_tab()
        tab_widget.addTab(ai_tab, "AI Tools")
        
        # Style Transfer Tab
        style_tab = self.create_style_tab()
        tab_widget.addTab(style_tab, "Style Transfer")
        
        # Advanced AI Tab
        advanced_tab = self.create_advanced_ai_tab()
        tab_widget.addTab(advanced_tab, "Advanced AI")
        
        # Layers Tab
        self.layer_panel = LayerPanel()
        self.layer_panel.setObjectName("layer_panel")
        self.layer_panel.layer_selected.connect(self.on_layer_selected)
        self.layer_panel.layer_added.connect(self.on_layer_added)
        self.layer_panel.layer_removed.connect(self.on_layer_removed)
        self.layer_panel.layer_merged.connect(self.on_layers_merged)
        self.layer_panel.layer_flattened.connect(self.on_layers_flattened)
        self.layer_panel.layer_opacity_changed.connect(self.on_layer_opacity_changed)
        self.layer_panel.layer_blend_changed.connect(self.on_layer_blend_changed)
        self.layer_panel.layer_visibility_changed.connect(self.on_layer_visibility_changed)
        tab_widget.addTab(self.layer_panel, "Layers")
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def create_ai_tools_tab(self) -> QWidget:
        """Create AI tools tab"""
        widget = QWidget()
        widget.setObjectName("ai_tools_tab")
        layout = QVBoxLayout(widget)
        
        # AI Enhancements Group
        ai_group = QGroupBox("AI Enhancements")
        ai_group.setObjectName("ai_group")
        ai_layout = QVBoxLayout()
        
        self.ai_enhance_btn = QPushButton("✨ Auto Enhance")
        self.ai_enhance_btn.setObjectName("ai_enhance_btn")
        self.ai_enhance_btn.clicked.connect(self.controller.ai_auto_enhance)
        ai_layout.addWidget(self.ai_enhance_btn)
        
        self.ai_denoise_btn = QPushButton("🔇 Denoise")
        self.ai_denoise_btn.setObjectName("ai_denoise_btn")
        self.ai_denoise_btn.clicked.connect(self.ai_denoise)
        ai_layout.addWidget(self.ai_denoise_btn)
        
        self.ai_resolution_btn = QPushButton("🔍 Super Resolution")
        self.ai_resolution_btn.setObjectName("ai_resolution_btn")
        self.ai_resolution_btn.clicked.connect(self.ai_enhance_resolution)
        ai_layout.addWidget(self.ai_resolution_btn)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        # Face Enhancement Group
        face_group = QGroupBox("Face Processing")
        face_group.setObjectName("face_group")
        face_layout = QVBoxLayout()
        
        self.ai_facial_btn = QPushButton("👤 Enhance Facial Features")
        self.ai_facial_btn.setObjectName("ai_facial_btn")
        self.ai_facial_btn.clicked.connect(self.controller.ai_enhance_facial)
        face_layout.addWidget(self.ai_facial_btn)
        
        face_group.setLayout(face_layout)
        layout.addWidget(face_group)
        
        layout.addStretch()
        return widget
    
    def create_style_tab(self) -> QWidget:
        """Create style transfer tab"""
        widget = QWidget()
        widget.setObjectName("style_tab")
        layout = QVBoxLayout(widget)
        
        # Style Transfer Group
        style_group = QGroupBox("Artistic Styles")
        style_group.setObjectName("style_group")
        style_layout = QVBoxLayout()
        
        self.style_combo = QComboBox()
        self.style_combo.setObjectName("style_combo")
        self.style_combo.addItems([
            "Cartoon", "Pencil Sketch", "Oil Painting", 
            "Watercolor", "Comic", "Vintage"
        ])
        style_layout.addWidget(self.style_combo)
        
        self.apply_style_btn = QPushButton("🎨 Apply Style")
        self.apply_style_btn.setObjectName("apply_style_btn")
        self.apply_style_btn.clicked.connect(self.apply_style_transfer)
        style_layout.addWidget(self.apply_style_btn)
        
        style_group.setLayout(style_layout)
        layout.addWidget(style_group)
        
        layout.addStretch()
        return widget
    
    def create_advanced_ai_tab(self) -> QWidget:
        """Create advanced AI tab"""
        widget = QWidget()
        widget.setObjectName("advanced_ai_tab")
        layout = QVBoxLayout(widget)
        
        # Background Removal Group
        bg_group = QGroupBox("Background")
        bg_group.setObjectName("bg_group")
        bg_layout = QVBoxLayout()
        
        self.ai_background_btn = QPushButton("🎭 Remove Background")
        self.ai_background_btn.setObjectName("ai_background_btn")
        self.ai_background_btn.clicked.connect(self.controller.ai_remove_background)
        bg_layout.addWidget(self.ai_background_btn)
        
        bg_group.setLayout(bg_layout)
        layout.addWidget(bg_group)
        
        # Colorization Group
        color_group = QGroupBox("Colorization")
        color_group.setObjectName("color_group")
        color_layout = QVBoxLayout()
        
        self.colorize_btn = QPushButton("🎨 Colorize B&W")
        self.colorize_btn.setObjectName("colorize_btn")
        self.colorize_btn.clicked.connect(self.colorize_image)
        color_layout.addWidget(self.colorize_btn)
        
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        layout.addStretch()
        return widget
        
    def create_menu_bar(self):
        """Create the complete menu bar with UX improvements"""
        menubar = self.menuBar()
        menubar.setObjectName("main_menu_bar")
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.setObjectName("file_menu")
        
        open_action = QAction("📂 Open...", self)
        open_action.setObjectName("open_action")
        open_action.setShortcut(self.shortcut_manager.get_shortcut('file_open'))
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        
        # Recent files submenu
        self.create_recent_files_menu(file_menu)
        
        file_menu.addSeparator()
        
        save_action = QAction("💾 Save", self)
        save_action.setObjectName("save_action")
        save_action.setShortcut(self.shortcut_manager.get_shortcut('file_save'))
        save_action.triggered.connect(self.save_image)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("💾 Save As...", self)
        save_as_action.setObjectName("save_as_action")
        save_as_action.setShortcut(self.shortcut_manager.get_shortcut('file_save_as'))
        save_as_action.triggered.connect(self.save_image_as)
        file_menu.addAction(save_as_action)
        
        export_action = QAction("📤 Export...", self)
        export_action.setObjectName("export_action")
        export_action.setShortcut(self.shortcut_manager.get_shortcut('file_export'))
        export_action.triggered.connect(self.show_export_dialog)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        batch_action = QAction("🔄 Batch Process...", self)
        batch_action.setObjectName("batch_action")
        batch_action.triggered.connect(self.show_batch_dialog)
        file_menu.addAction(batch_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("❌ Exit", self)
        exit_action.setObjectName("exit_action")
        exit_action.setShortcut(self.shortcut_manager.get_shortcut('file_exit'))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.setObjectName("edit_menu")
        
        undo_action = QAction("↩ Undo", self)
        undo_action.setObjectName("undo_action")
        undo_action.setShortcut(self.shortcut_manager.get_shortcut('edit_undo'))
        undo_action.triggered.connect(self.controller.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("↪ Redo", self)
        redo_action.setObjectName("redo_action")
        redo_action.setShortcut(self.shortcut_manager.get_shortcut('edit_redo'))
        redo_action.triggered.connect(self.controller.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        reset_action = QAction("⟲ Reset to Original", self)
        reset_action.setObjectName("reset_action")
        reset_action.setShortcut(self.shortcut_manager.get_shortcut('edit_reset'))
        reset_action.triggered.connect(self.controller.reset_image)
        edit_menu.addAction(reset_action)
        
        # Image menu
        image_menu = menubar.addMenu("&Image")
        image_menu.setObjectName("image_menu")
        
        crop_action = QAction("✂ Crop", self)
        crop_action.setObjectName("crop_action")
        crop_action.setShortcut(self.shortcut_manager.get_shortcut('image_crop'))
        crop_action.triggered.connect(self.show_crop_tool)
        image_menu.addAction(crop_action)
        
        resize_action = QAction("📏 Resize", self)
        resize_action.setObjectName("resize_action")
        resize_action.setShortcut(self.shortcut_manager.get_shortcut('image_resize'))
        resize_action.triggered.connect(self.show_resize_dialog)
        image_menu.addAction(resize_action)
        
        rotate_menu = image_menu.addMenu("↻ Rotate")
        rotate_menu.setObjectName("rotate_menu")
        
        rotate_90_action = QAction("90° Right", self)
        rotate_90_action.setObjectName("rotate_90_action")
        rotate_90_action.setShortcut(self.shortcut_manager.get_shortcut('image_rotate_right'))
        rotate_90_action.triggered.connect(lambda: self.rotate_image(90))
        rotate_menu.addAction(rotate_90_action)
        
        rotate_270_action = QAction("90° Left", self)
        rotate_270_action.setObjectName("rotate_270_action")
        rotate_270_action.setShortcut(self.shortcut_manager.get_shortcut('image_rotate_left'))
        rotate_270_action.triggered.connect(lambda: self.rotate_image(-90))
        rotate_menu.addAction(rotate_270_action)
        
        rotate_180_action = QAction("180°", self)
        rotate_180_action.setObjectName("rotate_180_action")
        rotate_180_action.triggered.connect(lambda: self.rotate_image(180))
        rotate_menu.addAction(rotate_180_action)
        
        flip_menu = image_menu.addMenu("🔄 Flip")
        flip_menu.setObjectName("flip_menu")
        
        flip_h_action = QAction("Horizontal", self)
        flip_h_action.setObjectName("flip_h_action")
        flip_h_action.setShortcut(self.shortcut_manager.get_shortcut('image_flip_h'))
        flip_h_action.triggered.connect(self.controller.flip_horizontal)
        flip_menu.addAction(flip_h_action)
        
        flip_v_action = QAction("Vertical", self)
        flip_v_action.setObjectName("flip_v_action")
        flip_v_action.setShortcut(self.shortcut_manager.get_shortcut('image_flip_v'))
        flip_v_action.triggered.connect(self.controller.flip_vertical)
        flip_menu.addAction(flip_v_action)
        
        # Filter menu
        filter_menu = menubar.addMenu("&Filter")
        filter_menu.setObjectName("filter_menu")
        
        blur_action = QAction("🌀 Blur", self)
        blur_action.setObjectName("blur_action")
        blur_action.triggered.connect(self.apply_blur)
        filter_menu.addAction(blur_action)
        
        edge_action = QAction("✏️ Edge Enhance", self)
        edge_action.setObjectName("edge_action")
        edge_action.triggered.connect(self.controller.apply_edge_enhance)
        filter_menu.addAction(edge_action)
        
        filter_menu.addSeparator()
        
        denoise_action = QAction("🔇 AI Denoise", self)
        denoise_action.setObjectName("denoise_action")
        denoise_action.setShortcut(self.shortcut_manager.get_shortcut('ai_denoise'))
        denoise_action.triggered.connect(self.ai_denoise)
        filter_menu.addAction(denoise_action)
        
        # AI menu
        ai_menu = menubar.addMenu("&AI")
        ai_menu.setObjectName("ai_menu")
        
        auto_enhance_action = QAction("✨ Auto Enhance", self)
        auto_enhance_action.setObjectName("auto_enhance_action")
        auto_enhance_action.setShortcut(self.shortcut_manager.get_shortcut('ai_auto_enhance'))
        auto_enhance_action.triggered.connect(self.controller.ai_auto_enhance)
        ai_menu.addAction(auto_enhance_action)
        
        super_res_action = QAction("🔍 Super Resolution", self)
        super_res_action.setObjectName("super_res_action")
        super_res_action.setShortcut(self.shortcut_manager.get_shortcut('ai_super_res'))
        super_res_action.triggered.connect(self.ai_enhance_resolution)
        ai_menu.addAction(super_res_action)
        
        remove_bg_action = QAction("🎭 Remove Background", self)
        remove_bg_action.setObjectName("remove_bg_action")
        remove_bg_action.setShortcut(self.shortcut_manager.get_shortcut('ai_remove_bg'))
        remove_bg_action.triggered.connect(self.controller.ai_remove_background)
        ai_menu.addAction(remove_bg_action)
        
        facial_action = QAction("👤 Enhance Facial Features", self)
        facial_action.setObjectName("facial_action")
        facial_action.setShortcut(self.shortcut_manager.get_shortcut('ai_facial'))
        facial_action.triggered.connect(self.controller.ai_enhance_facial)
        ai_menu.addAction(facial_action)
        
        colorize_action = QAction("🎨 Colorize B&W", self)
        colorize_action.setObjectName("colorize_action")
        colorize_action.triggered.connect(self.colorize_image)
        ai_menu.addAction(colorize_action)
        
        style_menu = ai_menu.addMenu("🎨 Style Transfer")
        style_menu.setObjectName("style_menu")
        
        for style in ["Cartoon", "Pencil Sketch", "Oil Painting", "Watercolor", "Comic", "Vintage"]:
            style_action = QAction(style, self)
            style_action.setObjectName(f"style_{style.lower().replace(' ', '_')}_action")
            style_action.triggered.connect(lambda checked, s=style: self.apply_style(s))
            style_menu.addAction(style_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.setObjectName("view_menu")
        
        compare_action = QAction("👁 Compare Before/After", self)
        compare_action.setObjectName("compare_action")
        compare_action.setShortcut(self.shortcut_manager.get_shortcut('view_compare'))
        compare_action.triggered.connect(self.show_comparison)
        view_menu.addAction(compare_action)
        
        view_menu.addSeparator()
        
        zoom_in_action = QAction("🔍 Zoom In", self)
        zoom_in_action.setObjectName("zoom_in_action")
        zoom_in_action.setShortcut(self.shortcut_manager.get_shortcut('view_zoom_in'))
        zoom_in_action.triggered.connect(self.image_view.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("🔍 Zoom Out", self)
        zoom_out_action.setObjectName("zoom_out_action")
        zoom_out_action.setShortcut(self.shortcut_manager.get_shortcut('view_zoom_out'))
        zoom_out_action.triggered.connect(self.image_view.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        fit_action = QAction("📐 Fit to Window", self)
        fit_action.setObjectName("fit_action")
        fit_action.setShortcut(self.shortcut_manager.get_shortcut('view_fit'))
        fit_action.triggered.connect(self.image_view.zoom_to_fit)
        view_menu.addAction(fit_action)
        
        actual_action = QAction("🔍 Actual Size", self)
        actual_action.setObjectName("actual_action")
        actual_action.setShortcut(self.shortcut_manager.get_shortcut('view_actual'))
        actual_action.triggered.connect(self.image_view.zoom_actual)
        view_menu.addAction(actual_action)
        
        # Layer menu
        layer_menu = menubar.addMenu("&Layer")
        layer_menu.setObjectName("layer_menu")
        
        new_layer_action = QAction("➕ New Layer", self)
        new_layer_action.setObjectName("new_layer_action")
        new_layer_action.setShortcut(self.shortcut_manager.get_shortcut('layer_new'))
        new_layer_action.triggered.connect(lambda: self.on_layer_added())
        layer_menu.addAction(new_layer_action)
        
        duplicate_layer_action = QAction("📋 Duplicate Layer", self)
        duplicate_layer_action.setObjectName("duplicate_layer_action")
        duplicate_layer_action.setShortcut(self.shortcut_manager.get_shortcut('layer_duplicate'))
        duplicate_layer_action.triggered.connect(self.duplicate_current_layer)
        layer_menu.addAction(duplicate_layer_action)
        
        delete_layer_action = QAction("🗑 Delete Layer", self)
        delete_layer_action.setObjectName("delete_layer_action")
        delete_layer_action.setShortcut(self.shortcut_manager.get_shortcut('layer_delete'))
        delete_layer_action.triggered.connect(self.delete_current_layer)
        layer_menu.addAction(delete_layer_action)
        
        layer_menu.addSeparator()
        
        merge_down_action = QAction("⬇ Merge Down", self)
        merge_down_action.setObjectName("merge_down_action")
        merge_down_action.setShortcut(self.shortcut_manager.get_shortcut('layer_merge'))
        merge_down_action.triggered.connect(self.merge_down)
        layer_menu.addAction(merge_down_action)
        
        flatten_action = QAction("📦 Flatten Image", self)
        flatten_action.setObjectName("flatten_action")
        flatten_action.setShortcut(self.shortcut_manager.get_shortcut('layer_flatten'))
        flatten_action.triggered.connect(self.on_layers_flattened)
        layer_menu.addAction(flatten_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.setObjectName("tools_menu")
        
        preferences_action = QAction("⚙ Preferences", self)
        preferences_action.setObjectName("preferences_action")
        preferences_action.triggered.connect(self.show_preferences)
        tools_menu.addAction(preferences_action)
        
        tools_menu.addSeparator()
        
        customize_shortcuts_action = QAction("⌨ Customize Shortcuts", self)
        customize_shortcuts_action.setObjectName("customize_shortcuts_action")
        customize_shortcuts_action.triggered.connect(self.customize_shortcuts)
        tools_menu.addAction(customize_shortcuts_action)
        
        # Theme submenu
        theme_menu = tools_menu.addMenu("🎨 Theme")
        theme_menu.setObjectName("theme_menu")
        
        theme_group = QActionGroup(self)
        theme_group.setObjectName("theme_group")
        for theme_id, theme in self.theme_manager.THEMES.items():
            theme_action = QAction(theme['name'], self)
            theme_action.setObjectName(f"theme_{theme_id}_action")
            theme_action.setCheckable(True)
            theme_action.setChecked(theme_id == self.theme_manager.current_theme)
            theme_action.triggered.connect(lambda checked, t=theme_id: self.switch_theme(t))
            theme_group.addAction(theme_action)
            theme_menu.addAction(theme_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.setObjectName("help_menu")
        
        about_action = QAction("ℹ️ About", self)
        about_action.setObjectName("about_action")
        about_action.setShortcut(self.shortcut_manager.get_shortcut('help_about'))
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_recent_files_menu(self, menu):
        """Create recent files submenu"""
        recent_menu = menu.addMenu("Recent Files")
        recent_menu.setObjectName("recent_menu")
        
        for i, filepath in enumerate(self.recent_files[:self.max_recent_files]):
            if os.path.exists(filepath):
                action = QAction(os.path.basename(filepath), self)
                # Use index for unique object name
                action.setObjectName(f"recent_action_{i}")
                action.setData(filepath)
                action.triggered.connect(lambda checked, f=filepath: self.open_recent_file(f))
                recent_menu.addAction(action)
        
        if not self.recent_files:
            action = QAction("No recent files", self)
            action.setObjectName("no_recent_files_action")
            action.setEnabled(False)
            recent_menu.addAction(action)
        
        recent_menu.addSeparator()
        
        clear_action = QAction("Clear Recent Files", self)
        clear_action.setObjectName("clear_recent_action")
        clear_action.triggered.connect(self.clear_recent_files)
        recent_menu.addAction(clear_action)

    def update_recent_files_menu(self):
        """Update recent files menu"""
        for menu in self.menuBar().findChildren(QMenu):
            if menu.objectName() == "recent_menu":
                menu.clear()
                for i, filepath in enumerate(self.recent_files[:self.max_recent_files]):
                    if os.path.exists(filepath):
                        action = QAction(os.path.basename(filepath), self)
                        action.setObjectName(f"recent_action_{i}")
                        action.setData(filepath)
                        action.triggered.connect(lambda checked, f=filepath: self.open_recent_file(f))
                        menu.addAction(action)
                
                if not self.recent_files:
                    action = QAction("No recent files", self)
                    action.setObjectName("no_recent_files_action")
                    action.setEnabled(False)
                    menu.addAction(action)
                
                menu.addSeparator()
                
                clear_action = QAction("Clear Recent Files", self)
                clear_action.setObjectName("clear_recent_action")
                clear_action.triggered.connect(self.clear_recent_files)
                menu.addAction(clear_action)
                break

    def add_to_recent_files(self, filepath):
        """Add file to recent files list"""
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        self.recent_files = self.recent_files[:self.max_recent_files]
        self.workspace_manager.save_recent_files(self.recent_files)
        self.update_recent_files_menu()

    def clear_recent_files(self):
        """Clear recent files list"""
        self.recent_files = []
        self.workspace_manager.save_recent_files(self.recent_files)
        self.update_recent_files_menu()

    def open_recent_file(self, filepath):
        """Open file from recent list"""
        if os.path.exists(filepath):
            self.open_image(filepath)
        else:
            QMessageBox.warning(self, "File Not Found", f"The file '{filepath}' no longer exists.")
            self.recent_files.remove(filepath)
            self.update_recent_files_menu()

    def customize_shortcuts(self):
        """Open shortcut customization dialog"""
        dialog = ShortcutDialog(self.shortcut_manager, self)
        if dialog.exec_():
            # Reapply shortcuts to all actions
            self.apply_shortcuts()

    def apply_shortcuts(self):
        """Apply keyboard shortcuts to all actions"""
        # Update all action shortcuts
        for action in self.findChildren(QAction):
            if action.objectName():
                # Extract action ID from object name
                action_id = action.objectName().replace('_action', '')
                if hasattr(self.shortcut_manager, 'get_shortcut'):
                    shortcut = self.shortcut_manager.get_shortcut(action_id)
                    if shortcut:
                        action.setShortcut(shortcut)
        
        # Update tooltips
        self.tooltip_manager.setup_tooltips(self)

    def switch_theme(self, theme_name):
        """Switch application theme"""
        self.theme_manager.apply_theme(QApplication.instance(), theme_name)
        self.theme_indicator.setText(f"🎨 {theme_name.title()}")
        self.tooltip_manager.setup_tooltips(self)  # Update tooltips for new theme

    def show_preferences(self):
        """Show preferences dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Preferences")
        dialog.setGeometry(200, 200, 500, 400)
        dialog.setModal(True)
        dialog.setObjectName("preferences_dialog")
        
        layout = QVBoxLayout(dialog)
        
        # Theme selection
        theme_group = QGroupBox("Appearance")
        theme_group.setObjectName("prefs_theme_group")
        theme_layout = QVBoxLayout()
        
        theme_combo = QComboBox()
        theme_combo.setObjectName("prefs_theme_combo")
        theme_names = [self.theme_manager.THEMES[t]['name'] for t in self.theme_manager.THEMES]
        theme_combo.addItems(theme_names)
        
        # Find current theme index
        current_index = 0
        for i, theme_id in enumerate(self.theme_manager.THEMES.keys()):
            if theme_id == self.theme_manager.current_theme:
                current_index = i
                break
        theme_combo.setCurrentIndex(current_index)
        
        theme_layout.addWidget(QLabel("Theme:"))
        theme_layout.addWidget(theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Recent files settings
        recent_group = QGroupBox("Recent Files")
        recent_group.setObjectName("prefs_recent_group")
        recent_layout = QVBoxLayout()
        
        max_recent_spin = QSpinBox()
        max_recent_spin.setObjectName("prefs_max_recent_spin")
        max_recent_spin.setRange(5, 20)
        max_recent_spin.setValue(self.max_recent_files)
        recent_layout.addWidget(QLabel("Maximum recent files:"))
        recent_layout.addWidget(max_recent_spin)
        
        recent_group.setLayout(recent_layout)
        layout.addWidget(recent_group)
        
        # Auto-save settings
        autosave_group = QGroupBox("Auto-Save")
        autosave_group.setObjectName("prefs_autosave_group")
        autosave_layout = QVBoxLayout()
        
        self.autosave_check = QCheckBox("Enable auto-save")
        self.autosave_check.setObjectName("autosave_check")
        self.autosave_check.setChecked(True)
        autosave_layout.addWidget(self.autosave_check)
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Interval (minutes):"))
        self.autosave_interval = QSpinBox()
        self.autosave_interval.setObjectName("autosave_interval")
        self.autosave_interval.setRange(1, 30)
        self.autosave_interval.setValue(5)
        interval_layout.addWidget(self.autosave_interval)
        autosave_layout.addLayout(interval_layout)
        
        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)
        
        # Tooltip settings
        tooltip_group = QGroupBox("Tooltips")
        tooltip_group.setObjectName("prefs_tooltip_group")
        tooltip_layout = QVBoxLayout()
        
        self.tooltips_check = QCheckBox("Show tooltips")
        self.tooltips_check.setObjectName("tooltips_check")
        self.tooltips_check.setChecked(True)
        tooltip_layout.addWidget(self.tooltips_check)
        
        tooltip_group.setLayout(tooltip_layout)
        layout.addWidget(tooltip_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        shortcut_btn = QPushButton("Customize Shortcuts...")
        shortcut_btn.setObjectName("prefs_shortcut_btn")
        shortcut_btn.clicked.connect(self.customize_shortcuts)
        button_layout.addWidget(shortcut_btn)
        
        button_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("prefs_ok_btn")
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("prefs_cancel_btn")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        if dialog.exec_():
            # Apply theme
            selected_theme_name = theme_combo.currentText()
            for theme_id, theme in self.theme_manager.THEMES.items():
                if theme['name'] == selected_theme_name:
                    self.switch_theme(theme_id)
                    break
            
            # Update max recent files
            self.max_recent_files = max_recent_spin.value()
            self.update_recent_files_menu()
            
            # Save preferences
            prefs = {
                'autosave': self.autosave_check.isChecked(),
                'autosave_interval': self.autosave_interval.value(),
                'show_tooltips': self.tooltips_check.isChecked()
            }
            self.workspace_manager.save_preferences(prefs)
        
    def create_tool_bar(self):
        """Create the main toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("main_toolbar")
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(True)
        self.addToolBar(toolbar)
        
        # File operations
        open_action = QAction("📂 Open", self)
        open_action.setObjectName("toolbar_open")
        open_action.setShortcut(self.shortcut_manager.get_shortcut('file_open'))
        open_action.triggered.connect(self.open_image)
        toolbar.addAction(open_action)
        
        save_action = QAction("💾 Save", self)
        save_action.setObjectName("toolbar_save")
        save_action.setShortcut(self.shortcut_manager.get_shortcut('file_save'))
        save_action.triggered.connect(self.save_image)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Edit operations
        undo_action = QAction("↩ Undo", self)
        undo_action.setObjectName("toolbar_undo")
        undo_action.setShortcut(self.shortcut_manager.get_shortcut('edit_undo'))
        undo_action.triggered.connect(self.controller.undo)
        toolbar.addAction(undo_action)
        
        redo_action = QAction("↪ Redo", self)
        redo_action.setObjectName("toolbar_redo")
        redo_action.setShortcut(self.shortcut_manager.get_shortcut('edit_redo'))
        redo_action.triggered.connect(self.controller.redo)
        toolbar.addAction(redo_action)
        
        toolbar.addSeparator()
        
        # Transform operations
        crop_action = QAction("✂ Crop", self)
        crop_action.setObjectName("toolbar_crop")
        crop_action.setShortcut(self.shortcut_manager.get_shortcut('image_crop'))
        crop_action.triggered.connect(self.show_crop_tool)
        toolbar.addAction(crop_action)
        
        rotate_action = QAction("↻ Rotate", self)
        rotate_action.setObjectName("toolbar_rotate")
        rotate_action.triggered.connect(lambda: self.rotate_image(90))
        toolbar.addAction(rotate_action)
        
        toolbar.addSeparator()
        
        # AI operations
        auto_action = QAction("✨ Auto Enhance", self)
        auto_action.setObjectName("toolbar_auto")
        auto_action.setShortcut(self.shortcut_manager.get_shortcut('ai_auto_enhance'))
        auto_action.triggered.connect(self.controller.ai_auto_enhance)
        toolbar.addAction(auto_action)
        
        denoise_action = QAction("🔇 Denoise", self)
        denoise_action.setObjectName("toolbar_denoise")
        denoise_action.setShortcut(self.shortcut_manager.get_shortcut('ai_denoise'))
        denoise_action.triggered.connect(self.ai_denoise)
        toolbar.addAction(denoise_action)
        
        style_action = QAction("🎨 Style", self)
        style_action.setObjectName("toolbar_style")
        style_action.triggered.connect(self.apply_style_transfer)
        toolbar.addAction(style_action)
        
        toolbar.addSeparator()
        
        # View operations
        compare_action = QAction("👁 Compare", self)
        compare_action.setObjectName("toolbar_compare")
        compare_action.setShortcut(self.shortcut_manager.get_shortcut('view_compare'))
        compare_action.triggered.connect(self.show_comparison)
        toolbar.addAction(compare_action)
        
        layer_action = QAction("🎨 Layers", self)
        layer_action.setObjectName("toolbar_layers")
        layer_action.setCheckable(True)
        layer_action.toggled.connect(self.toggle_layer_mode)
        toolbar.addAction(layer_action)
        
    def connect_signals(self):
        """Connect all controller signals to UI"""
        self.controller.image_updated.connect(self.update_image_display)
        self.controller.status_updated.connect(self.update_status)
        self.controller.progress_updated.connect(self.update_progress)
        
    # ========== Image Operations ==========
    
    def open_image(self, filepath=None):
        """Open image file dialog"""
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(
                self,
                "Open Image",
                "",
                "All Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;"
                "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;All Files (*.*)"
            )
        
        if filepath:
            try:
                self.controller.load_image(filepath)
                self.save_btn.setEnabled(True)
                self.export_btn.setEnabled(True)
                
                # Add to recent files
                self.add_to_recent_files(filepath)
                
                # Update resize spin boxes with image dimensions
                if self.controller.image_model.current_image:
                    self.resize_width_spin.setValue(self.controller.image_model.current_image.width)
                    self.resize_height_spin.setValue(self.controller.image_model.current_image.height)
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")
            
    def save_image(self):
        """Save image file dialog"""
        if not self.controller.image_model.current_image:
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            "",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;All Files (*.*)"
        )
        
        if filepath:
            try:
                self.controller.save_image(filepath)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save image: {str(e)}")
    
    def save_image_as(self):
        """Save image with different format/options"""
        self.show_export_dialog()
            
    def update_image_display(self):
        """Update the image view with current image"""
        pixmap = self.controller.get_current_pixmap()
        if pixmap:
            self.image_view.setPixmap(pixmap)
            self.update_image_info()
            self.update_layer_panel()
            
    def update_image_info(self):
        """Update image information display"""
        if self.controller.image_model.image_data:
            data = self.controller.image_model.image_data
            size_kb = data.size / 1024
            info = f"{data.name} | {data.width} x {data.height} | {data.mode} | {size_kb:.1f} KB"
            self.info_label.setText(info)
            
    def update_zoom_label(self, zoom):
        """Update zoom label"""
        self.zoom_label.setText(f"{int(zoom * 100)}%")
            
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_label.setText(message)
        
    def update_progress(self, value: int):
        """Update progress bar"""
        if value >= 100:
            self.progress_bar.hide()
        else:
            self.progress_bar.show()
            self.progress_bar.setValue(value)
            
    def reset_sliders(self):
        """Reset all adjustment sliders to zero"""
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)
        self.saturation_slider.setValue(0)
        self.sharpness_slider.setValue(0)
            
    # ========== Adjustment Methods ==========
    
    def adjust_brightness(self, value: int):
        """Handle brightness adjustment"""
        self.controller.adjust_brightness(value)
        
    def adjust_contrast(self, value: int):
        """Handle contrast adjustment"""
        self.controller.adjust_contrast(value)
        
    def adjust_saturation(self, value: int):
        """Handle saturation adjustment"""
        self.controller.adjust_saturation(value)
        
    def adjust_sharpness(self, value: int):
        """Handle sharpness adjustment"""
        self.controller.adjust_sharpness(value)
        
    def adjust_hue(self, value: int):
        """Handle hue adjustment"""
        # This would need to be implemented in the controller
        self.update_status(f"Hue adjusted: {value}")
        
    def adjust_gamma(self, value: float):
        """Handle gamma adjustment"""
        # This would need to be implemented in the controller
        self.update_status(f"Gamma adjusted: {value}")
        
    # ========== Transform Methods ==========
    
    def rotate_image(self, angle: float):
        """Rotate image by given angle"""
        self.controller.rotate(angle)
        
    def apply_resize(self):
        """Apply resize to image"""
        if self.controller.image_model.current_image:
            width = self.resize_width_spin.value()
            height = self.resize_height_spin.value()
            self.controller.image_model.resize(width, height)
            self.controller.image_updated.emit()
            self.update_status(f"Resized to {width} x {height}")
        
    def show_resize_dialog(self):
        """Show resize dialog"""
        if self.controller.image_model.current_image:
            # Switch to transform tab and highlight resize
            pass
            
    # ========== Filter Methods ==========
    
    def apply_blur(self):
        """Apply blur effect"""
        self.controller.apply_blur(radius=2)
        
    # ========== AI Methods ==========
    
    def ai_denoise(self):
        """Apply AI denoising"""
        self.controller.ai_denoise(strength=0.1)
        
    def ai_enhance_resolution(self):
        """Apply AI super resolution"""
        self.controller.ai_enhance_resolution(scale=2)
        
    def apply_style_transfer(self):
        """Apply selected style transfer"""
        style = self.style_combo.currentText().lower().replace(" ", "_")
        self.controller.ai_style_transfer(style)
        
    def apply_style(self, style_name):
        """Apply specific style"""
        style = style_name.lower().replace(" ", "_")
        self.controller.ai_style_transfer(style)
        
    def colorize_image(self):
        """Apply colorization"""
        self.update_status("Colorizing image...")
        # This would need to be implemented in the controller
        QMessageBox.information(self, "Coming Soon", "Colorization feature will be available in the next update!")
        
    # ========== Crop Tool ==========
    
    def show_crop_tool(self):
        """Show crop tool dialog"""
        if self.controller.image_model.current_image:
            pixmap = self.controller.get_current_pixmap()
            self.crop_tool = CropTool(pixmap, self)
            self.crop_tool.crop_completed.connect(self.apply_crop)
            self.crop_tool.crop_cancelled.connect(self.on_crop_cancelled)
            self.crop_tool.show()

    def apply_crop(self, crop_rect):
        """Apply crop to image"""
        try:
            self.controller.image_model.crop((
                crop_rect.x(),
                crop_rect.y(),
                crop_rect.x() + crop_rect.width(),
                crop_rect.y() + crop_rect.height()
            ))
            self.controller.image_updated.emit()
            self.controller.status_updated.emit("Image cropped successfully")
        except Exception as e:
            QMessageBox.critical(self, "Crop Error", f"Failed to crop image: {str(e)}")

    def on_crop_cancelled(self):
        """Handle crop cancellation"""
        self.controller.status_updated.emit("Crop cancelled")

    # ========== Comparison View ==========
    
    def show_comparison(self):
        """Show before/after comparison view"""
        if (self.controller.image_model.original_image and 
            self.controller.image_model.current_image):
            
            # Get before and after pixmaps
            original = self.controller.image_model.original_image
            current = self.controller.image_model.current_image
            
            # Convert PIL to QPixmap
            byte_array = io.BytesIO()
            original.save(byte_array, format='PNG')
            before_pixmap = QPixmap()
            before_pixmap.loadFromData(byte_array.getvalue())
            
            byte_array = io.BytesIO()
            current.save(byte_array, format='PNG')
            after_pixmap = QPixmap()
            after_pixmap.loadFromData(byte_array.getvalue())
            
            self.comparison_view = ComparisonView(before_pixmap, after_pixmap, self)
            self.comparison_view.show()

    # ========== Export Dialog ==========
    
    def show_export_dialog(self):
        """Show export options dialog"""
        if self.controller.image_model.current_image:
            pixmap = self.controller.get_current_pixmap()
            self.export_dialog = ExportDialog(pixmap, self)
            self.export_dialog.export_requested.connect(self.export_image)
            self.export_dialog.show()

    def export_image(self, filepath, options):
        """Export image with specified options"""
        try:
            img = self.controller.image_model.current_image
            
            # Apply size adjustments
            if 'scale' in options:
                new_size = (int(img.width * options['scale']), 
                          int(img.height * options['scale']))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            elif 'width' in options and 'height' in options:
                img = img.resize((options['width'], options['height']), 
                               Image.Resampling.LANCZOS)
            
            # Save with format-specific options
            format = options['format'].lower()
            save_kwargs = {}
            
            if format in ['jpeg', 'jpg'] and options.get('quality'):
                save_kwargs['quality'] = options['quality']
                save_kwargs['optimize'] = True
            
            if options.get('strip_metadata'):
                # Create new image without metadata
                img = Image.new(img.mode, img.size)
                img.putdata(list(self.controller.image_model.current_image.getdata()))
            
            img.save(filepath, format=format, **save_kwargs)
            
            self.controller.status_updated.emit(f"Image exported to {filepath}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export image: {str(e)}")

    # ========== Batch Processing ==========
    
    def show_batch_dialog(self):
        """Show batch processing dialog"""
        self.batch_dialog = QDialog(self)
        self.batch_dialog.setWindowTitle("Batch Processing")
        self.batch_dialog.setGeometry(200, 200, 600, 500)
        self.batch_dialog.setObjectName("batch_dialog")
        
        layout = QVBoxLayout(self.batch_dialog)
        
        # File selection
        file_group = QGroupBox("Input Files")
        file_group.setObjectName("batch_file_group")
        file_layout = QVBoxLayout()
        
        self.batch_file_list = QListWidget()
        self.batch_file_list.setObjectName("batch_file_list")
        file_layout.addWidget(self.batch_file_list)
        
        file_btn_layout = QHBoxLayout()
        add_files_btn = QPushButton("Add Files")
        add_files_btn.setObjectName("batch_add_files_btn")
        add_files_btn.clicked.connect(lambda: self.add_batch_files(self.batch_dialog))
        file_btn_layout.addWidget(add_files_btn)
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.setObjectName("batch_add_folder_btn")
        add_folder_btn.clicked.connect(lambda: self.add_batch_folder(self.batch_dialog))
        file_btn_layout.addWidget(add_folder_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("batch_clear_btn")
        clear_btn.clicked.connect(self.batch_file_list.clear)
        file_btn_layout.addWidget(clear_btn)
        
        file_layout.addLayout(file_btn_layout)
        
        # Recursive checkbox
        self.recursive_check = QCheckBox("Include subfolders")
        self.recursive_check.setObjectName("batch_recursive_check")
        file_layout.addWidget(self.recursive_check)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Operations
        ops_group = QGroupBox("Operations")
        ops_group.setObjectName("batch_ops_group")
        ops_layout = QVBoxLayout()
        
        # Resize
        resize_layout = QHBoxLayout()
        self.resize_check = QCheckBox("Resize")
        self.resize_check.setObjectName("batch_resize_check")
        resize_layout.addWidget(self.resize_check)
        
        resize_layout.addWidget(QLabel("Width:"))
        self.resize_width = QSpinBox()
        self.resize_width.setObjectName("batch_resize_width")
        self.resize_width.setRange(1, 10000)
        self.resize_width.setValue(800)
        self.resize_width.setEnabled(False)
        resize_layout.addWidget(self.resize_width)
        
        resize_layout.addWidget(QLabel("Height:"))
        self.resize_height = QSpinBox()
        self.resize_height.setObjectName("batch_resize_height")
        self.resize_height.setRange(1, 10000)
        self.resize_height.setValue(600)
        self.resize_height.setEnabled(False)
        resize_layout.addWidget(self.resize_height)
        
        self.resize_check.toggled.connect(self.resize_width.setEnabled)
        self.resize_check.toggled.connect(self.resize_height.setEnabled)
        
        ops_layout.addLayout(resize_layout)
        
        # Brightness
        brightness_layout = QHBoxLayout()
        self.brightness_check = QCheckBox("Brightness")
        self.brightness_check.setObjectName("batch_brightness_check")
        brightness_layout.addWidget(self.brightness_check)
        
        brightness_layout.addWidget(QLabel("Factor:"))
        self.brightness_factor = QDoubleSpinBox()
        self.brightness_factor.setObjectName("batch_brightness_factor")
        self.brightness_factor.setRange(0.1, 3.0)
        self.brightness_factor.setValue(1.0)
        self.brightness_factor.setSingleStep(0.1)
        self.brightness_factor.setEnabled(False)
        brightness_layout.addWidget(self.brightness_factor)
        
        self.brightness_check.toggled.connect(self.brightness_factor.setEnabled)
        
        ops_layout.addLayout(brightness_layout)
        
        # Contrast
        contrast_layout = QHBoxLayout()
        self.contrast_check = QCheckBox("Contrast")
        self.contrast_check.setObjectName("batch_contrast_check")
        contrast_layout.addWidget(self.contrast_check)
        
        contrast_layout.addWidget(QLabel("Factor:"))
        self.contrast_factor = QDoubleSpinBox()
        self.contrast_factor.setObjectName("batch_contrast_factor")
        self.contrast_factor.setRange(0.1, 3.0)
        self.contrast_factor.setValue(1.0)
        self.contrast_factor.setSingleStep(0.1)
        self.contrast_factor.setEnabled(False)
        contrast_layout.addWidget(self.contrast_factor)
        
        self.contrast_check.toggled.connect(self.contrast_factor.setEnabled)
        
        ops_layout.addLayout(contrast_layout)
        
        # Convert format
        format_layout = QHBoxLayout()
        self.format_check = QCheckBox("Convert to")
        self.format_check.setObjectName("batch_format_check")
        format_layout.addWidget(self.format_check)
        
        self.format_combo = QComboBox()
        self.format_combo.setObjectName("batch_format_combo")
        self.format_combo.addItems(["JPEG", "PNG", "WEBP", "TIFF", "BMP"])
        self.format_combo.setEnabled(False)
        format_layout.addWidget(self.format_combo)
        
        self.format_check.toggled.connect(self.format_combo.setEnabled)
        
        ops_layout.addLayout(format_layout)
        
        ops_group.setLayout(ops_layout)
        layout.addWidget(ops_group)
        
        # Output directory
        output_group = QGroupBox("Output")
        output_group.setObjectName("batch_output_group")
        output_layout = QHBoxLayout()
        
        self.output_dir_label = QLabel("Not selected")
        self.output_dir_label.setObjectName("batch_output_label")
        output_layout.addWidget(self.output_dir_label)
        
        browse_output_btn = QPushButton("Browse...")
        browse_output_btn.setObjectName("batch_browse_btn")
        browse_output_btn.clicked.connect(lambda: self.select_output_dir(self.batch_dialog))
        output_layout.addWidget(browse_output_btn)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Progress
        self.batch_progress = QProgressBar()
        self.batch_progress.setObjectName("batch_progress")
        self.batch_progress.hide()
        layout.addWidget(self.batch_progress)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        start_btn = QPushButton("Start Processing")
        start_btn.setObjectName("batch_start_btn")
        start_btn.clicked.connect(lambda: self.start_batch_processing(self.batch_dialog))
        start_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        btn_layout.addWidget(start_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("batch_cancel_btn")
        cancel_btn.clicked.connect(self.batch_dialog.reject)
        cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Initialize batch controller
        self.batch_controller = BatchController()
        self.batch_controller.batch_started.connect(self.on_batch_started)
        self.batch_controller.batch_progress.connect(self.on_batch_progress)
        self.batch_controller.batch_file_completed.connect(self.on_batch_file_completed)
        self.batch_controller.batch_error.connect(self.on_batch_error)
        self.batch_controller.batch_finished.connect(self.on_batch_finished)
        self.batch_controller.batch_status.connect(self.update_status)
        
        self.batch_dialog.exec_()

    def add_batch_files(self, dialog):
        """Add files to batch list"""
        files, _ = QFileDialog.getOpenFileNames(
            dialog,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp)"
        )
        
        for file in files:
            self.batch_file_list.addItem(file)

    def add_batch_folder(self, dialog):
        """Add folder to batch list"""
        folder = QFileDialog.getExistingDirectory(dialog, "Select Folder")
        if folder:
            files = self.batch_controller.collect_files([folder], self.recursive_check.isChecked())
            for file in files:
                self.batch_file_list.addItem(file)

    def select_output_dir(self, dialog):
        """Select output directory for batch processing"""
        folder = QFileDialog.getExistingDirectory(dialog, "Select Output Directory")
        if folder:
            self.output_dir_label.setText(folder)

    def start_batch_processing(self, dialog):
        """Start batch processing"""
        # Collect files
        files = [self.batch_file_list.item(i).text() for i in range(self.batch_file_list.count())]
        
        if not files:
            QMessageBox.warning(dialog, "No Files", "Please add files to process")
            return
        
        output_dir = self.output_dir_label.text()
        if output_dir == "Not selected":
            QMessageBox.warning(dialog, "No Output Directory", "Please select output directory")
            return
        
        # Build operations list
        operations = []
        
        if self.resize_check.isChecked():
            operations.append(('resize', {
                'width': self.resize_width.value(),
                'height': self.resize_height.value()
            }))
        
        if self.brightness_check.isChecked():
            operations.append(('brightness', {
                'factor': self.brightness_factor.value()
            }))
        
        if self.contrast_check.isChecked():
            operations.append(('contrast', {
                'factor': self.contrast_factor.value()
            }))
        
        if self.format_check.isChecked():
            operations.append(('convert_format', {
                'format': self.format_combo.currentText()
            }))
        
        if not operations:
            operations.append(('copy', {}))  # Just copy without changes
        
        # Start processing
        self.batch_controller.process_batch(files, output_dir, operations)
        dialog.accept()

    def on_batch_started(self):
        """Handle batch processing start"""
        self.batch_progress.show()
        self.batch_progress.setValue(0)
        self.update_status("Batch processing started...")

    def on_batch_progress(self, current, total):
        """Update batch progress"""
        self.batch_progress.setMaximum(total)
        self.batch_progress.setValue(current)

    def on_batch_file_completed(self, filename):
        """Handle file completion"""
        self.update_status(f"Processed: {filename}")

    def on_batch_error(self, filename, error):
        """Handle batch error"""
        QMessageBox.warning(
            self,
            "Batch Error",
            f"Error processing {filename}:\n{error}"
        )

    def on_batch_finished(self):
        """Handle batch completion"""
        if self.batch_progress:
            try:
                self.batch_progress.hide()
            except RuntimeError:
                pass
        self.update_status("Batch processing completed")
        QMessageBox.information(self, "Batch Complete", "All files have been processed successfully!")

    # ========== Layer Methods ==========
    
    def toggle_layer_mode(self, enabled):
        """Toggle layer mode on/off"""
        self.controller.toggle_layer_mode(enabled)
        if enabled:
            self.update_layer_panel()
            self.status_label.setText("Layer mode enabled")
        else:
            self.status_label.setText("Layer mode disabled")
    
    def on_layer_selected(self, index):
        """Handle layer selection"""
        if hasattr(self.controller, 'layer_manager'):
            self.controller.layer_manager.set_active_layer(index)
    
    def on_layer_added(self):
        """Handle add layer request"""
        self.controller.add_layer()
        self.update_layer_panel()
    
    def on_layer_removed(self, index):
        """Handle remove layer request"""
        self.controller.remove_layer(index)
        self.update_layer_panel()
    
    def duplicate_current_layer(self):
        """Duplicate the current layer"""
        if hasattr(self.controller, 'layer_manager') and self.controller.layer_manager.get_active_layer():
            index = self.controller.layer_manager.active_layer_index
            self.controller.duplicate_layer(index)
            self.update_layer_panel()
    
    def delete_current_layer(self):
        """Delete the current layer"""
        if hasattr(self.controller, 'layer_manager') and self.controller.layer_manager.get_active_layer():
            index = self.controller.layer_manager.active_layer_index
            self.controller.remove_layer(index)
            self.update_layer_panel()
    
    def merge_down(self):
        """Merge current layer with the one below"""
        if hasattr(self.controller, 'layer_manager'):
            active = self.controller.layer_manager.active_layer_index
            if active > 0:
                self.controller.merge_layers([active - 1, active])
                self.update_layer_panel()
    
    def on_layers_merged(self, indices):
        """Handle merge layers request"""
        self.controller.merge_layers(indices)
        self.update_layer_panel()
    
    def on_layers_flattened(self):
        """Handle flatten layers request"""
        self.controller.flatten_layers()
        self.update_layer_panel()
        self.image_view.setPixmap(self.controller.get_current_pixmap())
    
    def on_layer_opacity_changed(self, index, opacity):
        """Handle layer opacity change"""
        self.controller.set_layer_opacity(index, opacity)
        self.update_layer_panel()
    
    def on_layer_blend_changed(self, index, mode):
        """Handle layer blend mode change"""
        self.controller.set_layer_blend_mode(index, mode)
        self.update_layer_panel()
    
    def on_layer_visibility_changed(self, index, visible):
        """Handle layer visibility change"""
        self.controller.set_layer_visibility(index, visible)
        self.update_layer_panel()
    
    def update_layer_panel(self):
        """Update layer panel with current layer info"""
        if hasattr(self, 'layer_panel') and self.layer_panel:
            if hasattr(self.controller, 'use_layers') and self.controller.use_layers:
                info = self.controller.get_layer_info()
                if info:
                    self.layer_panel.update_layer_list(
                        info['names'],
                        info['thumbnails'],
                        info['opacities'],
                        info['blend_modes'],
                        info['visibilities']
                    )

    # ========== AI Processing Handlers ==========
    
    def on_ai_started(self):
        """Handle AI processing start"""
        self.set_ui_enabled(False)
        self.progress_bar.show()
        self.status_label.setText("AI Processing...")
        
    def on_ai_finished(self):
        """Handle AI processing finish"""
        self.set_ui_enabled(True)
        self.progress_bar.hide()
        
    def on_ai_error(self, error_msg):
        """Handle AI processing errors"""
        self.set_ui_enabled(True)
        self.progress_bar.hide()
        QMessageBox.critical(self, "AI Processing Error", error_msg)
        self.status_label.setText(f"Error: {error_msg}")
        
    def on_ai_result(self, result):
        """Handle AI processing result"""
        self.update_image_display()
        self.status_label.setText("AI processing completed")
        
    def set_ui_enabled(self, enabled: bool):
        """Enable or disable UI controls during processing"""
        # File operations
        self.open_btn.setEnabled(enabled)
        self.save_btn.setEnabled(enabled and self.controller.image_model.current_image is not None)
        self.export_btn.setEnabled(enabled and self.controller.image_model.current_image is not None)
        self.batch_btn.setEnabled(enabled)
        
        # Basic adjustments
        self.brightness_slider.setEnabled(enabled)
        self.contrast_slider.setEnabled(enabled)
        self.saturation_slider.setEnabled(enabled)
        self.sharpness_slider.setEnabled(enabled)
        
        # Transformations
        self.rotate_left_btn.setEnabled(enabled)
        self.rotate_right_btn.setEnabled(enabled)
        self.flip_h_btn.setEnabled(enabled)
        self.flip_v_btn.setEnabled(enabled)
        self.crop_btn.setEnabled(enabled)
        self.resize_apply_btn.setEnabled(enabled)
        
        # Filters
        self.blur_btn.setEnabled(enabled)
        self.edge_enhance_btn.setEnabled(enabled)
        
        # History
        self.undo_btn.setEnabled(enabled)
        self.redo_btn.setEnabled(enabled)
        self.reset_btn.setEnabled(enabled)
        self.compare_btn.setEnabled(enabled)
        
        # AI buttons
        self.ai_enhance_btn.setEnabled(enabled)
        self.ai_denoise_btn.setEnabled(enabled)
        self.ai_resolution_btn.setEnabled(enabled)
        self.apply_style_btn.setEnabled(enabled)
        self.ai_background_btn.setEnabled(enabled)
        self.ai_facial_btn.setEnabled(enabled)
        self.colorize_btn.setEnabled(enabled)
        
        # Layer panel buttons
        if self.layer_panel:
            self.layer_panel.setEnabled(enabled)
        
    def closeEvent(self, event):
        """Handle application close event - save workspace and cleanup"""
        # Save workspace
        self.workspace_manager.save_workspace(self)
        
        # Disconnect all signals to prevent memory leaks
        try:
            self.controller.image_updated.disconnect()
            self.controller.status_updated.disconnect()
            self.controller.progress_updated.disconnect()
        except:
            pass
        
        # Check if processing is ongoing
        processing = False
        message = ""
        
        if self.ai_controller and self.ai_controller.is_processing:
            processing = True
            message = "AI processing is still running."
        elif self.batch_controller and self.batch_controller.is_processing:
            processing = True
            message = "Batch processing is still running."
        
        if processing:
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                f"{message} Exit anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.ai_controller:
                    self.ai_controller.cancel_processing()
                if self.batch_controller:
                    self.batch_controller.cancel_batch()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
            
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About AI Image Editor",
            """<h2>AI Image Editor & Enhancer</h2>
            <p><b>Version 2.0</b></p>
            <p>A professional image editor with AI-powered enhancement features.</p>
            
            <h3>Features:</h3>
            <ul>
                <li>Basic image editing tools (crop, rotate, flip, resize)</li>
                <li>Color adjustments (brightness, contrast, saturation, sharpness)</li>
                <li>Filters and effects (blur, edge enhance)</li>
                <li>AI-based enhancements (auto enhance, denoise, super resolution)</li>
                <li>Style transfer (cartoon, sketch, oil painting, watercolor, comic, vintage)</li>
                <li>Background removal with AI</li>
                <li>Facial feature enhancement</li>
                <li>Black & white colorization</li>
                <li>Layer support with blend modes</li>
                <li>Batch processing</li>
                <li>Before/after comparison</li>
                <li>Advanced export options</li>
            </ul>
            
            <h3>UX Improvements:</h3>
            <ul>
                <li>Customizable themes (Dark, Light, High Contrast)</li>
                <li>Workspace persistence</li>
                <li>Keyboard shortcut customization</li>
                <li>Comprehensive tooltips</li>
                <li>Recent files menu</li>
                <li>Preferences dialog</li>
            </ul>
            
            <p><i>Built with PyQt5 and OpenCV</i></p>"""
        )