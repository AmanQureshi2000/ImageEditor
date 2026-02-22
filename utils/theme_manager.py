"""
Theme manager with 2026-style premium design system: deep surfaces, vibrant
accents, smooth gradients, refined typography and consistent spacing.
Supports Modern Dark (default), Classic Dark, Light, High Contrast, and
Midnight Purple themes.
"""
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import json
import os

# Design system constants
RADIUS_SM = "4px"
RADIUS_MD = "8px"
RADIUS_LG = "12px"
RADIUS_XL = "16px"
SPACING = "8px"
FONT_FAMILY = '"Segoe UI", "SF Pro Display", "Roboto", Arial, sans-serif'
FONT_SIZE_SM = "11px"
FONT_SIZE_MD = "12px"
FONT_SIZE_LG = "13px"
FONT_SIZE_XL = "14px"

class ThemeManager:
    """Manage application themes with modern 2026 premium design system."""

    THEMES = {
        'modern_dark': {
            'name': 'Neon Dark',
            'colors': {
                'window':           '#0f1117',
                'window_text':      '#e2e8f0',
                'base':             '#1a1f2e',
                'alternate_base':   '#1e2536',
                'text':             '#e2e8f0',
                'button':           '#1e2536',
                'button_text':      '#e2e8f0',
                'bright_text':      '#ffffff',
                'light':            '#2d3748',
                'midlight':         '#252d3d',
                'dark':             '#0a0d14',
                'mid':              '#2a3347',
                'shadow':           '#050810',
                'highlight':        '#6366f1',
                'highlight2':       '#8b5cf6',
                'highlighted_text': '#ffffff',
                'link':             '#6366f1',
                'link_visited':     '#8b5cf6',
                'tooltip_bg':       '#1e2536',
                'tooltip_text':     '#e2e8f0',
                'disabled_text':    '#4a5568',
                'error':            '#f56565',
                'success':          '#48bb78',
                'warning':          '#ed8936',
                'info':             '#63b3ed',
                'canvas_bg':        '#0f1117',
                'canvas_border':    '#2a3347',
                'surface':          '#1a1f2e',
                'surface_hover':    '#252d3d',
                'accent_glow':      'rgba(99,102,241,0.3)',
                'card_bg':          '#1a1f2e',
                'border':           '#2a3347',
                'input_bg':         '#141824',
                'scrollbar':        '#2a3347',
                'scrollbar_hover':  '#6366f1',
                'tab_active':       '#6366f1',
                'tab_inactive':     '#1e2536',
                'group_border':     '#2a3347',
                'menu_bg':          '#1a1f2e',
                'toolbar_bg':       '#0d1020',
                'statusbar_bg':     '#0a0d14',
            }
        },
        'dark': {
            'name': 'Classic Dark',
            'colors': {
                'window':           '#1e1e2e',
                'window_text':      '#cdd6f4',
                'base':             '#252535',
                'alternate_base':   '#2a2a3e',
                'text':             '#cdd6f4',
                'button':           '#2a2a3e',
                'button_text':      '#cdd6f4',
                'bright_text':      '#ffffff',
                'light':            '#3d3d5c',
                'midlight':         '#313149',
                'dark':             '#161622',
                'mid':              '#2d2d44',
                'shadow':           '#0f0f1a',
                'highlight':        '#89b4fa',
                'highlight2':       '#cba6f7',
                'highlighted_text': '#1e1e2e',
                'link':             '#89b4fa',
                'link_visited':     '#cba6f7',
                'tooltip_bg':       '#2a2a3e',
                'tooltip_text':     '#cdd6f4',
                'disabled_text':    '#585b70',
                'error':            '#f38ba8',
                'success':          '#a6e3a1',
                'warning':          '#f9e2af',
                'info':             '#89dceb',
                'canvas_bg':        '#1e1e2e',
                'canvas_border':    '#2d2d44',
                'surface':          '#252535',
                'surface_hover':    '#2d2d44',
                'accent_glow':      'rgba(137,180,250,0.2)',
                'card_bg':          '#252535',
                'border':           '#2d2d44',
                'input_bg':         '#1a1a28',
                'scrollbar':        '#2d2d44',
                'scrollbar_hover':  '#89b4fa',
                'tab_active':       '#89b4fa',
                'tab_inactive':     '#2a2a3e',
                'group_border':     '#2d2d44',
                'menu_bg':          '#252535',
                'toolbar_bg':       '#181826',
                'statusbar_bg':     '#161622',
            }
        },
        'light': {
            'name': 'Light',
            'colors': {
                'window':           '#f8fafc',
                'window_text':      '#0f172a',
                'base':             '#ffffff',
                'alternate_base':   '#f1f5f9',
                'text':             '#1e293b',
                'button':           '#e2e8f0',
                'button_text':      '#1e293b',
                'bright_text':      '#ffffff',
                'light':            '#ffffff',
                'midlight':         '#f8fafc',
                'dark':             '#cbd5e1',
                'mid':              '#e2e8f0',
                'shadow':           '#94a3b8',
                'highlight':        '#6366f1',
                'highlight2':       '#8b5cf6',
                'highlighted_text': '#ffffff',
                'link':             '#6366f1',
                'link_visited':     '#8b5cf6',
                'tooltip_bg':       '#1e293b',
                'tooltip_text':     '#f8fafc',
                'disabled_text':    '#94a3b8',
                'error':            '#ef4444',
                'success':          '#22c55e',
                'warning':          '#f59e0b',
                'info':             '#3b82f6',
                'canvas_bg':        '#e2e8f0',
                'canvas_border':    '#cbd5e1',
                'surface':          '#ffffff',
                'surface_hover':    '#f1f5f9',
                'accent_glow':      'rgba(99,102,241,0.15)',
                'card_bg':          '#ffffff',
                'border':           '#e2e8f0',
                'input_bg':         '#ffffff',
                'scrollbar':        '#e2e8f0',
                'scrollbar_hover':  '#6366f1',
                'tab_active':       '#6366f1',
                'tab_inactive':     '#e2e8f0',
                'group_border':     '#e2e8f0',
                'menu_bg':          '#ffffff',
                'toolbar_bg':       '#f1f5f9',
                'statusbar_bg':     '#e2e8f0',
            }
        },
        'high_contrast': {
            'name': 'High Contrast',
            'colors': {
                'window':           '#000000',
                'window_text':      '#ffffff',
                'base':             '#000000',
                'alternate_base':   '#111111',
                'text':             '#ffffff',
                'button':           '#111111',
                'button_text':      '#ffffff',
                'bright_text':      '#ffff00',
                'light':            '#333333',
                'midlight':         '#222222',
                'dark':             '#000000',
                'mid':              '#1a1a1a',
                'shadow':           '#000000',
                'highlight':        '#ffff00',
                'highlight2':       '#00ffff',
                'highlighted_text': '#000000',
                'link':             '#ffff00',
                'link_visited':     '#00ffff',
                'tooltip_bg':       '#111111',
                'tooltip_text':     '#ffffff',
                'disabled_text':    '#555555',
                'error':            '#ff0000',
                'success':          '#00ff00',
                'warning':          '#ffaa00',
                'info':             '#00ffff',
                'canvas_bg':        '#050505',
                'canvas_border':    '#444444',
                'surface':          '#111111',
                'surface_hover':    '#222222',
                'accent_glow':      'rgba(255,255,0,0.2)',
                'card_bg':          '#111111',
                'border':           '#555555',
                'input_bg':         '#111111',
                'scrollbar':        '#333333',
                'scrollbar_hover':  '#ffff00',
                'tab_active':       '#ffff00',
                'tab_inactive':     '#111111',
                'group_border':     '#555555',
                'menu_bg':          '#111111',
                'toolbar_bg':       '#000000',
                'statusbar_bg':     '#000000',
            }
        },
        'midnight': {
            'name': 'Midnight Purple',
            'colors': {
                'window':           '#120d1e',
                'window_text':      '#e8d5ff',
                'base':             '#1a1228',
                'alternate_base':   '#1e1530',
                'text':             '#e8d5ff',
                'button':           '#1e1530',
                'button_text':      '#e8d5ff',
                'bright_text':      '#ffffff',
                'light':            '#2d2040',
                'midlight':         '#261a38',
                'dark':             '#0b0914',
                'mid':              '#251a38',
                'shadow':           '#07050e',
                'highlight':        '#a855f7',
                'highlight2':       '#ec4899',
                'highlighted_text': '#ffffff',
                'link':             '#a855f7',
                'link_visited':     '#ec4899',
                'tooltip_bg':       '#1e1530',
                'tooltip_text':     '#e8d5ff',
                'disabled_text':    '#4a3666',
                'error':            '#f87171',
                'success':          '#4ade80',
                'warning':          '#fbbf24',
                'info':             '#60a5fa',
                'canvas_bg':        '#120d1e',
                'canvas_border':    '#251a38',
                'surface':          '#1a1228',
                'surface_hover':    '#251a38',
                'accent_glow':      'rgba(168,85,247,0.3)',
                'card_bg':          '#1a1228',
                'border':           '#251a38',
                'input_bg':         '#10091a',
                'scrollbar':        '#251a38',
                'scrollbar_hover':  '#a855f7',
                'tab_active':       '#a855f7',
                'tab_inactive':     '#1e1530',
                'group_border':     '#251a38',
                'menu_bg':          '#1a1228',
                'toolbar_bg':       '#0e0a1a',
                'statusbar_bg':     '#0b0914',
            }
        },
    }

    def __init__(self):
        self.current_theme = 'modern_dark'
        self.config_file = 'theme_config.json'
        self.load_config()

    def load_config(self):
        """Load theme configuration from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    theme = config.get('theme', 'modern_dark')
                    if theme in self.THEMES:
                        self.current_theme = theme
            except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
                print(f"Error loading theme config: {e}")

    def save_config(self):
        """Save theme configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'theme': self.current_theme}, f, indent=2)
        except (IOError, UnicodeEncodeError) as e:
            print(f"Error saving theme config: {e}")

    def get_colors(self):
        """Return current theme colors dict for dynamic styling."""
        theme = self.THEMES.get(self.current_theme, self.THEMES['modern_dark'])
        return theme['colors'].copy()

    def apply_theme(self, app: QApplication, theme_name: str = None):
        """Apply theme to the entire application."""
        if theme_name and theme_name in self.THEMES:
            self.current_theme = theme_name

        theme = self.THEMES.get(self.current_theme, self.THEMES['modern_dark'])
        colors = theme['colors']

        # Create and apply palette
        palette = QPalette()
        
        # Set all palette colors with error handling
        try:
            palette.setColor(QPalette.Window, QColor(colors['window']))
            palette.setColor(QPalette.WindowText, QColor(colors['window_text']))
            palette.setColor(QPalette.Base, QColor(colors['base']))
            palette.setColor(QPalette.AlternateBase, QColor(colors['alternate_base']))
            palette.setColor(QPalette.Text, QColor(colors['text']))
            palette.setColor(QPalette.BrightText, QColor(colors['bright_text']))
            palette.setColor(QPalette.Button, QColor(colors['button']))
            palette.setColor(QPalette.ButtonText, QColor(colors['button_text']))
            palette.setColor(QPalette.Light, QColor(colors['light']))
            palette.setColor(QPalette.Midlight, QColor(colors['midlight']))
            palette.setColor(QPalette.Dark, QColor(colors['dark']))
            palette.setColor(QPalette.Mid, QColor(colors['mid']))
            palette.setColor(QPalette.Shadow, QColor(colors['shadow']))
            palette.setColor(QPalette.Highlight, QColor(colors['highlight']))
            palette.setColor(QPalette.HighlightedText, QColor(colors['highlighted_text']))
            palette.setColor(QPalette.Link, QColor(colors['link']))
            palette.setColor(QPalette.LinkVisited, QColor(colors['link_visited']))
            palette.setColor(QPalette.ToolTipBase, QColor(colors['tooltip_bg']))
            palette.setColor(QPalette.ToolTipText, QColor(colors['tooltip_text']))
            
            # Disabled colors
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(colors['disabled_text']))
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(colors['disabled_text']))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(colors['disabled_text']))
        except KeyError as e:
            print(f"Missing color key in theme: {e}")
            # Fallback to modern_dark if colors are missing
            fallback_colors = self.THEMES['modern_dark']['colors']
            self._apply_fallback_palette(palette, fallback_colors)

        app.setPalette(palette)
        self.apply_stylesheet(app, theme)
        self.save_config()

    def _apply_fallback_palette(self, palette, colors):
        """Apply fallback palette with error handling."""
        try:
            palette.setColor(QPalette.Window, QColor(colors.get('window', '#0f1117')))
            palette.setColor(QPalette.WindowText, QColor(colors.get('window_text', '#e2e8f0')))
            palette.setColor(QPalette.Base, QColor(colors.get('base', '#1a1f2e')))
            palette.setColor(QPalette.Text, QColor(colors.get('text', '#e2e8f0')))
            palette.setColor(QPalette.Button, QColor(colors.get('button', '#1e2536')))
            palette.setColor(QPalette.ButtonText, QColor(colors.get('button_text', '#e2e8f0')))
            palette.setColor(QPalette.Highlight, QColor(colors.get('highlight', '#6366f1')))
            palette.setColor(QPalette.HighlightedText, QColor(colors.get('highlighted_text', '#ffffff')))
        except Exception as e:
            print(f"Error applying fallback palette: {e}")

    def apply_stylesheet(self, app: QApplication, theme):
        """Apply premium 2026-style global stylesheet."""
        colors = theme['colors']
        
        # Create a safe copy of colors with defaults for any missing keys
        safe_colors = {}
        default_colors = self.THEMES['modern_dark']['colors']
        for key in default_colors.keys():
            safe_colors[key] = colors.get(key, default_colors[key])

        stylesheet = f"""
        /* ── Global Reset ─────────────────────────────────── */
        * {{
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_MD};
        }}
        
        QWidget {{
            background-color: {safe_colors['window']};
            color: {safe_colors['window_text']};
        }}

        QMainWindow {{
            background-color: {safe_colors['window']};
        }}

        /* ── Menu Bar ─────────────────────────────────────── */
        QMenuBar {{
            background-color: {safe_colors['toolbar_bg']};
            color: {safe_colors['window_text']};
            padding: 2px 4px;
            border-bottom: 1px solid {safe_colors['border']};
            spacing: 2px;
        }}
        QMenuBar::item {{
            background: transparent;
            padding: 5px 12px;
            border-radius: {RADIUS_SM};
        }}
        QMenuBar::item:selected {{
            background-color: {safe_colors['highlight']};
            color: #ffffff;
        }}
        QMenuBar::item:pressed {{
            background-color: {safe_colors['highlight']};
            color: #ffffff;
        }}

        /* ── Dropdown Menu ────────────────────────────────── */
        QMenu {{
            background-color: {safe_colors['menu_bg']};
            color: {safe_colors['text']};
            border: 1px solid {safe_colors['border']};
            border-radius: {RADIUS_MD};
            padding: 6px 4px;
        }}
        QMenu::item {{
            padding: 7px 28px 7px 16px;
            border-radius: {RADIUS_SM};
            margin: 1px 4px;
        }}
        QMenu::item:selected {{
            background-color: {safe_colors['highlight']};
            color: #ffffff;
        }}
        QMenu::separator {{
            height: 1px;
            background: {safe_colors['border']};
            margin: 4px 8px;
        }}

        /* ── Toolbar ─────────────────────────────────────── */
        QToolBar {{
            background-color: {safe_colors['toolbar_bg']};
            border: none;
            border-bottom: 2px solid {safe_colors['highlight']};
            spacing: 4px;
            padding: 5px 8px;
        }}
        QToolBar::separator {{
            background: {safe_colors['border']};
            width: 1px;
            margin: 4px 6px;
        }}
        QToolButton {{
            background-color: {safe_colors['surface']};
            color: {safe_colors['window_text']};
            border: 1px solid {safe_colors['border']};
            border-radius: {RADIUS_SM};
            padding: 6px 12px;
            font-size: {FONT_SIZE_SM};
            font-weight: 500;
        }}
        QToolButton:hover {{
            background-color: {safe_colors['highlight']};
            border-color: {safe_colors['highlight']};
            color: #ffffff;
        }}
        QToolButton:pressed {{
            background-color: {safe_colors['highlight2']};
            border-color: {safe_colors['highlight2']};
            color: #ffffff;
        }}
        QToolButton:checked {{
            background-color: {safe_colors['highlight']};
            color: #ffffff;
            border-color: {safe_colors['highlight']};
        }}

        /* ── Push Buttons ───────────────────────────────── */
        QPushButton {{
            background-color: {safe_colors['surface']};
            color: {safe_colors['window_text']};
            border: 1px solid {safe_colors['border']};
            border-radius: {RADIUS_MD};
            padding: 8px 16px;
            min-height: 26px;
            font-weight: 500;
            font-size: {FONT_SIZE_MD};
        }}
        QPushButton:hover {{
            background-color: {safe_colors['highlight']};
            border-color: {safe_colors['highlight']};
            color: #ffffff;
        }}
        QPushButton:pressed {{
            background-color: {safe_colors['highlight2']};
            border-color: {safe_colors['highlight2']};
            color: #ffffff;
        }}
        QPushButton:disabled {{
            background-color: {safe_colors['mid']};
            border-color: {safe_colors['border']};
            color: {safe_colors['disabled_text']};
        }}
        QPushButton:checked {{
            background-color: {safe_colors['highlight']};
            border-color: {safe_colors['highlight']};
            color: #ffffff;
        }}

        /* Primary action button */
        QPushButton#generate_btn,
        QPushButton#ai_generate_btn,
        QPushButton[class="primary"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {safe_colors['highlight']}, stop:1 {safe_colors['highlight2']});
            border: none;
            color: #ffffff;
            font-weight: 600;
            font-size: {FONT_SIZE_MD};
            border-radius: {RADIUS_MD};
        }}
        QPushButton#generate_btn:hover,
        QPushButton#ai_generate_btn:hover,
        QPushButton[class="primary"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {safe_colors['highlight2']}, stop:1 {safe_colors['highlight']});
        }}
        QPushButton#generate_btn:disabled,
        QPushButton#ai_generate_btn:disabled,
        QPushButton[class="primary"]:disabled {{
            background: {safe_colors['mid']};
            color: {safe_colors['disabled_text']};
        }}

        /* Danger button */
        QPushButton[class="danger"],
        QPushButton#danger_btn {{
            background-color: {safe_colors['error']};
            border-color: {safe_colors['error']};
            color: #ffffff;
        }}
        QPushButton[class="danger"]:hover,
        QPushButton#danger_btn:hover {{
            background-color: #e53e3e;
        }}

        /* Success button */
        QPushButton[class="success"] {{
            background-color: {safe_colors['success']};
            border-color: {safe_colors['success']};
            color: #ffffff;
        }}

        /* ── Group Boxes ────────────────────────────────── */
        QGroupBox {{
            background-color: {safe_colors['card_bg']};
            border: 1px solid {safe_colors['group_border']};
            border-radius: {RADIUS_MD};
            margin-top: 16px;
            padding: 16px 10px 10px 10px;
            font-weight: 600;
            font-size: {FONT_SIZE_SM};
            color: {safe_colors['window_text']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 2px 10px;
            color: #ffffff;
            background-color: {safe_colors['highlight']};
            border-radius: 4px;
            font-weight: 700;
            font-size: {FONT_SIZE_SM};
        }}

        /* ── Tab Widget ─────────────────────────────────── */
        QTabWidget::pane {{
            border: 1px solid {safe_colors['border']};
            border-radius: 0 0 {RADIUS_MD} {RADIUS_MD};
            background-color: {safe_colors['surface']};
            top: -1px;
        }}
        QTabBar::tab {{
            background-color: {safe_colors['tab_inactive']};
            color: {safe_colors['window_text']};
            border: 1px solid {safe_colors['border']};
            border-bottom: none;
            border-top-left-radius: {RADIUS_MD};
            border-top-right-radius: {RADIUS_MD};
            padding: 8px 12px;
            margin-right: 2px;
            font-weight: 500;
            min-width: 70px;
        }}
        QTabBar::tab:selected {{
            background-color: {safe_colors['tab_active']};
            color: #ffffff;
            border-color: {safe_colors['tab_active']};
            font-weight: 600;
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {safe_colors['surface_hover']};
            color: #ffffff;
            border-color: {safe_colors['highlight']};
        }}

        /* ── Sliders ────────────────────────────────────── */
        QSlider::groove:horizontal {{
            border: none;
            height: 5px;
            background: {safe_colors['mid']};
            margin: 2px 0;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {safe_colors['highlight']};
            border: 2px solid {safe_colors['highlight']};
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {safe_colors['highlight2']};
            border-color: {safe_colors['highlight2']};
            width: 18px;
            height: 18px;
            margin: -7px 0;
            border-radius: 9px;
        }}
        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {safe_colors['highlight']}, stop:1 {safe_colors['highlight2']});
            border-radius: 3px;
        }}

        /* ── Combo Box ──────────────────────────────────── */
        QComboBox {{
            background-color: {safe_colors['input_bg']};
            color: {safe_colors['text']};
            border: 1px solid {safe_colors['border']};
            border-radius: {RADIUS_SM};
            padding: 6px 10px;
            min-height: 22px;
        }}
        QComboBox:hover {{
            border-color: {safe_colors['highlight']};
        }}
        QComboBox:focus {{
            border-color: {safe_colors['highlight']};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 26px;
            border-left: 1px solid {safe_colors['border']};
        }}
        QComboBox QAbstractItemView {{
            background-color: {safe_colors['menu_bg']};
            color: {safe_colors['text']};
            border: 1px solid {safe_colors['border']};
            border-radius: {RADIUS_MD};
            padding: 4px;
            selection-background-color: {safe_colors['highlight']};
            selection-color: #ffffff;
            outline: none;
        }}

        /* ── Spin Boxes ─────────────────────────────────── */
        QSpinBox, QDoubleSpinBox {{
            background-color: {safe_colors['input_bg']};
            color: {safe_colors['text']};
            border: 1px solid {safe_colors['border']};
            border-radius: {RADIUS_SM};
            padding: 5px 8px;
            min-height: 22px;
        }}
        QSpinBox:hover, QDoubleSpinBox:hover {{
            border-color: {safe_colors['highlight']};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {safe_colors['highlight']};
        }}

        /* ── Line Edit ──────────────────────────────────── */
        QLineEdit {{
            background-color: {safe_colors['input_bg']};
            color: {safe_colors['text']};
            border: 1px solid {safe_colors['border']};
            border-radius: {RADIUS_SM};
            padding: 6px 10px;
            min-height: 22px;
        }}
        QLineEdit:hover {{
            border-color: {safe_colors['highlight']};
        }}
        QLineEdit:focus {{
            border: 2px solid {safe_colors['highlight']};
            padding: 5px 9px;
        }}
        QLineEdit:disabled {{
            background-color: {safe_colors['mid']};
            color: {safe_colors['disabled_text']};
        }}

        /* ── Scroll Areas ───────────────────────────────── */
        QScrollArea {{
            border: 1px solid {safe_colors['border']};
            border-radius: {RADIUS_SM};
            background-color: {safe_colors['window']};
        }}
        QScrollArea#image_scroll_area {{
            background-color: {safe_colors['canvas_bg']};
            border: none;
        }}

        /* ── Scroll Bars ────────────────────────────────── */
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 8px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {safe_colors['scrollbar']};
            min-height: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {safe_colors['scrollbar_hover']};
        }}
        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 8px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {safe_colors['scrollbar']};
            min-width: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {safe_colors['scrollbar_hover']};
        }}

        /* ── Splitter ───────────────────────────────────── */
        QSplitter::handle {{
            background: {safe_colors['border']};
            border-radius: 2px;
        }}
        QSplitter::handle:horizontal {{
            width: 4px;
        }}
        QSplitter::handle:vertical {{
            height: 4px;
        }}
        QSplitter::handle:hover {{
            background: {safe_colors['highlight']};
        }}

        /* ── Status Bar ─────────────────────────────────── */
        QStatusBar {{
            background-color: {safe_colors['statusbar_bg']};
            color: {safe_colors['window_text']};
            border-top: 2px solid {safe_colors['highlight']};
            padding: 2px 8px;
            font-size: {FONT_SIZE_SM};
            font-weight: 500;
        }}
        QStatusBar QLabel {{
            color: {safe_colors['window_text']};
            font-size: {FONT_SIZE_SM};
        }}
        QStatusBar QPushButton {{
            background-color: {safe_colors['surface']};
            color: {safe_colors['window_text']};
            border: 1px solid {safe_colors['border']};
            border-radius: {RADIUS_SM};
            padding: 3px 10px;
            font-size: {FONT_SIZE_SM};
            min-height: 20px;
        }}
        QStatusBar QPushButton:hover {{
            background-color: {safe_colors['highlight']};
            color: #ffffff;
            border-color: {safe_colors['highlight']};
        }}

        /* ── Progress Bar ───────────────────────────────── */
        QProgressBar {{
            border: none;
            border-radius: {RADIUS_SM};
            text-align: center;
            background: {safe_colors['mid']};
            height: 8px;
            font-size: {FONT_SIZE_SM};
            color: {safe_colors['window_text']};
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {safe_colors['highlight']}, stop:1 {safe_colors['highlight2']});
            border-radius: {RADIUS_SM};
        }}

        /* ── List Widget ────────────────────────────────── */
        QListWidget {{
            background-color: {safe_colors['base']};
            color: {safe_colors['text']};
            border: 1px solid {safe_colors['border']};
            border-radius: {RADIUS_SM};
            outline: none;
            padding: 2px;
        }}
        QListWidget::item {{
            padding: 5px 8px;
            border-radius: {RADIUS_SM};
            margin: 1px 2px;
        }}
        QListWidget::item:selected {{
            background-color: {safe_colors['highlight']};
            color: #ffffff;
        }}
        QListWidget::item:hover:!selected {{
            background-color: {safe_colors['surface_hover']};
        }}

        /* ── Table Widget ───────────────────────────────── */
        QTableWidget {{
            background-color: {safe_colors['base']};
            color: {safe_colors['text']};
            border: 1px solid {safe_colors['border']};
            border-radius: {RADIUS_SM};
            gridline-color: {safe_colors['border']};
            outline: none;
        }}
        QTableWidget::item:selected {{
            background-color: {safe_colors['highlight']};
            color: #ffffff;
        }}
        QHeaderView::section {{
            background-color: {safe_colors['surface']};
            color: {safe_colors['text']};
            border: none;
            border-bottom: 1px solid {safe_colors['border']};
            border-right: 1px solid {safe_colors['border']};
            padding: 6px 10px;
            font-weight: 600;
        }}

        /* ── Check Box ──────────────────────────────────── */
        QCheckBox {{
            color: {safe_colors['text']};
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {safe_colors['border']};
            border-radius: 5px;
            background: {safe_colors['input_bg']};
        }}
        QCheckBox::indicator:hover {{
            border-color: {safe_colors['highlight']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {safe_colors['highlight']};
            border-color: {safe_colors['highlight']};
        }}

        /* ── Radio Button ───────────────────────────────── */
        QRadioButton {{
            color: {safe_colors['text']};
            spacing: 8px;
        }}
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {safe_colors['border']};
            border-radius: 9px;
            background: {safe_colors['input_bg']};
        }}
        QRadioButton::indicator:hover {{
            border-color: {safe_colors['highlight']};
        }}
        QRadioButton::indicator:checked {{
            background-color: {safe_colors['highlight']};
            border-color: {safe_colors['highlight']};
        }}

        /* ── Tooltip ────────────────────────────────────── */
        QToolTip {{
            background-color: {safe_colors['tooltip_bg']};
            color: {safe_colors['tooltip_text']};
            border: 1px solid {safe_colors['highlight']};
            border-radius: {RADIUS_SM};
            padding: 6px 10px;
            font-size: {FONT_SIZE_SM};
        }}

        /* ── Dialog ─────────────────────────────────────── */
        QDialog {{
            background-color: {safe_colors['window']};
            border: 1px solid {safe_colors['border']};
            border-radius: {RADIUS_LG};
        }}

        /* ── Labels ─────────────────────────────────────── */
        QLabel {{
            color: {safe_colors['window_text']};
        }}
        QLabel#info_label {{
            color: {safe_colors['window_text']};
            font-size: {FONT_SIZE_SM};
        }}
        QLabel#image_view {{
            background-color: {safe_colors['canvas_bg']};
            border: 1px solid {safe_colors['canvas_border']};
            border-radius: {RADIUS_SM};
        }}
        QLabel#section_header {{
            color: {safe_colors['highlight']};
            font-weight: 700;
            font-size: {FONT_SIZE_MD};
            padding: 4px 0;
        }}
        QLabel#status_label {{
            color: {safe_colors['window_text']};
            font-size: {FONT_SIZE_SM};
            padding: 0 4px;
        }}
        QLabel#zoom_label {{
            color: {safe_colors['window_text']};
            font-weight: 600;
        }}

        /* ── Specific panels ────────────────────────────── */
        QWidget#left_panel,
        QWidget#right_panel {{
            background-color: {safe_colors['surface']};
            border-radius: {RADIUS_MD};
        }}

        QWidget#image_panel {{
            background-color: {safe_colors['canvas_bg']};
        }}
        """

        app.setStyleSheet(stylesheet)

    def get_available_themes(self):
        """Return list of theme keys."""
        return list(self.THEMES.keys())

    def get_theme_names(self):
        """Return display names of themes."""
        return [t['name'] for t in self.THEMES.values()]
    
    def get_current_theme_name(self):
        """Return display name of current theme."""
        return self.THEMES[self.current_theme]['name']
    
    def get_theme_colors(self, theme_name=None):
        """Get colors for a specific theme or current theme."""
        if theme_name and theme_name in self.THEMES:
            return self.THEMES[theme_name]['colors'].copy()
        return self.get_colors()