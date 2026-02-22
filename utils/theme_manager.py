from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import json
import os

class ThemeManager:
    """Manage application themes (dark/light mode)"""
    
    THEMES = {
        'dark': {
            'name': 'Dark',
            'colors': {
                'window': '#2b2b2b',
                'window_text': '#ffffff',
                'base': '#3c3c3c',
                'alternate_base': '#4a4a4a',
                'text': '#ffffff',
                'button': '#3c3c3c',
                'button_text': '#ffffff',
                'bright_text': '#ffffff',
                'light': '#5a5a5a',
                'midlight': '#4a4a4a',
                'dark': '#1e1e1e',
                'mid': '#353535',
                'shadow': '#1a1a1a',
                'highlight': '#4CAF50',
                'highlighted_text': '#ffffff',
                'link': '#4CAF50',
                'link_visited': '#45a049',
                'tooltip_bg': '#4a4a4a',
                'tooltip_text': '#ffffff',
                'disabled_text': '#808080',
                'error': '#f44336',
                'success': '#4CAF50',
                'warning': '#ff9800',
                'info': '#2196F3'
            }
        },
        'light': {
            'name': 'Light',
            'colors': {
                'window': '#f0f0f0',
                'window_text': '#000000',
                'base': '#ffffff',
                'alternate_base': '#f5f5f5',
                'text': '#000000',
                'button': '#e0e0e0',
                'button_text': '#000000',
                'bright_text': '#ffffff',
                'light': '#ffffff',
                'midlight': '#f5f5f5',
                'dark': '#a0a0a0',
                'mid': '#c0c0c0',
                'shadow': '#808080',
                'highlight': '#2196F3',
                'highlighted_text': '#ffffff',
                'link': '#2196F3',
                'link_visited': '#1976D2',
                'tooltip_bg': '#ffffe1',
                'tooltip_text': '#000000',
                'disabled_text': '#808080',
                'error': '#f44336',
                'success': '#4CAF50',
                'warning': '#ff9800',
                'info': '#2196F3'
            }
        },
        'high_contrast': {
            'name': 'High Contrast',
            'colors': {
                'window': '#000000',
                'window_text': '#ffffff',
                'base': '#000000',
                'alternate_base': '#1a1a1a',
                'text': '#ffffff',
                'button': '#000000',
                'button_text': '#ffffff',
                'bright_text': '#ffff00',
                'light': '#333333',
                'midlight': '#262626',
                'dark': '#000000',
                'mid': '#1a1a1a',
                'shadow': '#000000',
                'highlight': '#ffff00',
                'highlighted_text': '#000000',
                'link': '#ffff00',
                'link_visited': '#ffaa00',
                'tooltip_bg': '#000000',
                'tooltip_text': '#ffffff',
                'disabled_text': '#666666',
                'error': '#ff0000',
                'success': '#00ff00',
                'warning': '#ffff00',
                'info': '#00ffff'
            }
        }
    }
    
    def __init__(self):
        self.current_theme = 'dark'
        self.config_file = 'theme_config.json'
        self.load_config()
        
    def load_config(self):
        """Load theme configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.current_theme = config.get('theme', 'dark')
            except:
                pass
    
    def save_config(self):
        """Save theme configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'theme': self.current_theme}, f)
        except:
            pass
    
    def apply_theme(self, app: QApplication, theme_name: str = None):
        """Apply theme to application"""
        if theme_name:
            self.current_theme = theme_name
        
        theme = self.THEMES.get(self.current_theme, self.THEMES['dark'])
        colors = theme['colors']
        
        # Create and apply palette
        palette = QPalette()
        
        # Window
        palette.setColor(QPalette.Window, QColor(colors['window']))
        palette.setColor(QPalette.WindowText, QColor(colors['window_text']))
        
        # Base
        palette.setColor(QPalette.Base, QColor(colors['base']))
        palette.setColor(QPalette.AlternateBase, QColor(colors['alternate_base']))
        
        # Text
        palette.setColor(QPalette.Text, QColor(colors['text']))
        palette.setColor(QPalette.BrightText, QColor(colors['bright_text']))
        
        # Buttons
        palette.setColor(QPalette.Button, QColor(colors['button']))
        palette.setColor(QPalette.ButtonText, QColor(colors['button_text']))
        
        # Light/Dark/Shadow
        palette.setColor(QPalette.Light, QColor(colors['light']))
        palette.setColor(QPalette.Midlight, QColor(colors['midlight']))
        palette.setColor(QPalette.Dark, QColor(colors['dark']))
        palette.setColor(QPalette.Mid, QColor(colors['mid']))
        palette.setColor(QPalette.Shadow, QColor(colors['shadow']))
        
        # Highlight
        palette.setColor(QPalette.Highlight, QColor(colors['highlight']))
        palette.setColor(QPalette.HighlightedText, QColor(colors['highlighted_text']))
        
        # Links
        palette.setColor(QPalette.Link, QColor(colors['link']))
        palette.setColor(QPalette.LinkVisited, QColor(colors['link_visited']))
        
        # Tooltips
        palette.setColor(QPalette.ToolTipBase, QColor(colors['tooltip_bg']))
        palette.setColor(QPalette.ToolTipText, QColor(colors['tooltip_text']))
        
        # Disabled
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(colors['disabled_text']))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(colors['disabled_text']))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(colors['disabled_text']))
        
        app.setPalette(palette)
        
        # Additional stylesheet for widgets that don't respect palette
        self.apply_stylesheet(app, theme)
        
        self.save_config()
        
    def apply_stylesheet(self, app: QApplication, theme):
        """Apply additional stylesheet for widgets"""
        colors = theme['colors']
        
        stylesheet = f"""
        QMainWindow {{
            background-color: {colors['window']};
        }}
        
        QWidget {{
            background-color: {colors['window']};
            color: {colors['window_text']};
        }}
        
        QMenuBar {{
            background-color: {colors['dark']};
            color: {colors['window_text']};
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['highlight']};
            color: {colors['highlighted_text']};
        }}
        
        QMenu {{
            background-color: {colors['base']};
            color: {colors['text']};
            border: 1px solid {colors['mid']};
        }}
        
        QMenu::item:selected {{
            background-color: {colors['highlight']};
            color: {colors['highlighted_text']};
        }}
        
        QToolBar {{
            background-color: {colors['dark']};
            border: none;
            spacing: 3px;
        }}
        
        QToolButton {{
            background-color: {colors['button']};
            color: {colors['button_text']};
            border: 1px solid {colors['mid']};
            border-radius: 3px;
            padding: 5px;
        }}
        
        QToolButton:hover {{
            background-color: {colors['highlight']};
            color: {colors['highlighted_text']};
        }}
        
        QPushButton {{
            background-color: {colors['button']};
            color: {colors['button_text']};
            border: 1px solid {colors['mid']};
            border-radius: 3px;
            padding: 5px 10px;
        }}
        
        QPushButton:hover {{
            background-color: {colors['highlight']};
            color: {colors['highlighted_text']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['dark']};
        }}
        
        QPushButton:disabled {{
            background-color: {colors['mid']};
            color: {colors['disabled_text']};
        }}
        
        QGroupBox {{
            border: 2px solid {colors['mid']};
            border-radius: 5px;
            margin-top: 1ex;
            font-weight: bold;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }}
        
        QSlider::groove:horizontal {{
            border: 1px solid {colors['mid']};
            height: 8px;
            background: {colors['base']};
            margin: 2px 0;
            border-radius: 4px;
        }}
        
        QSlider::handle:horizontal {{
            background: {colors['highlight']};
            border: 1px solid {colors['mid']};
            width: 18px;
            margin: -2px 0;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: {colors['link']};
        }}
        
        QComboBox {{
            background-color: {colors['base']};
            color: {colors['text']};
            border: 1px solid {colors['mid']};
            border-radius: 3px;
            padding: 5px;
        }}
        
        QComboBox:hover {{
            border-color: {colors['highlight']};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left-width: 1px;
            border-left-color: {colors['mid']};
            border-left-style: solid;
        }}
        
        QSpinBox, QDoubleSpinBox {{
            background-color: {colors['base']};
            color: {colors['text']};
            border: 1px solid {colors['mid']};
            border-radius: 3px;
            padding: 3px;
        }}
        
        QScrollArea {{
            border: 1px solid {colors['mid']};
            background-color: {colors['window']};
        }}
        
        QScrollBar:vertical {{
            border: none;
            background: {colors['dark']};
            width: 14px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {colors['mid']};
            min-height: 20px;
            border-radius: 7px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {colors['highlight']};
        }}
        
        QScrollBar:horizontal {{
            border: none;
            background: {colors['dark']};
            height: 14px;
            margin: 0px;
        }}
        
        QScrollBar::handle:horizontal {{
            background: {colors['mid']};
            min-width: 20px;
            border-radius: 7px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background: {colors['highlight']};
        }}
        
        QTabWidget::pane {{
            border: 1px solid {colors['mid']};
            background-color: {colors['window']};
        }}
        
        QTabBar::tab {{
            background-color: {colors['button']};
            color: {colors['button_text']};
            border: 1px solid {colors['mid']};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 5px 10px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['highlight']};
            color: {colors['highlighted_text']};
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors['light']};
        }}
        
        QStatusBar {{
            background-color: {colors['dark']};
            color: {colors['window_text']};
        }}
        
        QProgressBar {{
            border: 1px solid {colors['mid']};
            border-radius: 3px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {colors['highlight']};
            border-radius: 3px;
        }}
        
        QListWidget {{
            background-color: {colors['base']};
            color: {colors['text']};
            border: 1px solid {colors['mid']};
        }}
        
        QListWidget::item:selected {{
            background-color: {colors['highlight']};
            color: {colors['highlighted_text']};
        }}
        
        QCheckBox {{
            color: {colors['text']};
        }}
        
        QCheckBox::indicator {{
            width: 13px;
            height: 13px;
            border: 1px solid {colors['mid']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors['highlight']};
        }}
        
        QRadioButton {{
            color: {colors['text']};
        }}
        
        QRadioButton::indicator {{
            width: 13px;
            height: 13px;
            border: 1px solid {colors['mid']};
            border-radius: 7px;
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {colors['highlight']};
        }}
        
        QToolTip {{
            background-color: {colors['tooltip_bg']};
            color: {colors['tooltip_text']};
            border: 1px solid {colors['mid']};
            padding: 5px;
        }}
        """
        
        app.setStyleSheet(stylesheet)
    
    def get_available_themes(self):
        """Get list of available themes"""
        return list(self.THEMES.keys())
    
    def get_theme_names(self):
        """Get display names of themes"""
        return [theme['name'] for theme in self.THEMES.values()]