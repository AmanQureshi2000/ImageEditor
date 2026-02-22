"""
AI Image Editor — Professional image editing with AI-powered enhancements.
Modern 2026 UI, themes, layers, batch processing, and export options.
"""
import sys
import traceback
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from views.main_window import MainWindow

APP_NAME = "AI Image Editor"
APP_VERSION = "4.0"
COMPANY_NAME = "AI Image Editor"


def setup_logging():
    """Setup logging configuration"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except:
            log_dir = "."
    
    return os.path.join(log_dir, "error.log")


def global_exception_handler(exctype, value, tb):
    """
    Global exception handler for uncaught exceptions.
    Logs the error and shows a dialog to the user.
    """
    # Format the error message
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    
    # Log to file
    log_file = setup_logging()
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Timestamp: {__import__('datetime').datetime.now()}\n")
            f.write(f"Exception Type: {exctype.__name__}\n")
            f.write(f"Exception Value: {value}\n")
            f.write(f"{'='*60}\n")
            f.write(error_msg)
            f.write(f"\n{'='*60}\n\n")
    except Exception as e:
        print(f"Failed to write to log file: {e}")
    
    # Show error dialog if QApplication exists
    app = QApplication.instance()
    if app:
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Unexpected Error")
        error_dialog.setText("An unexpected error occurred. The application will attempt to continue running.")
        error_dialog.setInformativeText(f"Error: {str(value)}")
        error_dialog.setDetailedText(error_msg)
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.setDefaultButton(QMessageBox.Ok)
        error_dialog.exec_()
    
    # Call the default exception handler
    sys.__excepthook__(exctype, value, tb)


def check_dependencies():
    """Check if critical dependencies are available"""
    missing = []
    
    # Check critical imports
    try:
        import PIL
    except ImportError:
        missing.append("Pillow")
    
    try:
        import numpy
    except ImportError:
        missing.append("NumPy")
    
    try:
        import cv2
    except ImportError:
        missing.append("OpenCV")
    
    if missing:
        msg = "Missing critical dependencies:\n\n"
        for m in missing:
            msg += f"• {m}\n"
        msg += "\nPlease install them using:\npip install -r requirements.txt"
        
        # Try to show message box
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Missing Dependencies", msg)
        return False
    
    return True


def main():
    """Main application entry point"""
    
    # Set global exception handler
    sys.excepthook = global_exception_handler
    
    try:
        # Enable High-DPI scaling for crisp UI on modern displays
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setOrganizationName(COMPANY_NAME)
        app.setApplicationVersion(APP_VERSION)
        
        # Set application style
        app.setStyle("Fusion")
        
        # Set application icon if available
        icon_paths = [
            "assets/icon.ico",
            "assets/icon.png",
            "icon.ico",
            "icon.png"
        ]
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
                break
        
        # Check critical dependencies
        if not check_dependencies():
            sys.exit(1)
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Run application
        sys.exit(app.exec_())
        
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        sys.exit(0)
        
    except Exception as e:
        error_msg = f"Failed to start application: {str(e)}\n{traceback.format_exc()}"
        
        # Log to file
        log_file = setup_logging()
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(error_msg)
        except:
            pass
        
        # Show error dialog
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "Application Error",
            f"Failed to start application:\n\n{str(e)}\n\nCheck {log_file} for details."
        )
        sys.exit(1)


if __name__ == '__main__':
    main()