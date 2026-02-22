import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from views.main_window import MainWindow

def global_exception_handler(exctype, value, tb):
    """Global exception handler for uncaught exceptions"""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    
    # Log to file
    with open('error.log', 'a') as f:
        f.write(f"\n--- Uncaught Exception ---\n{error_msg}\n")
    
    # Show error dialog
    app = QApplication.instance()
    if app:
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Unexpected Error")
        error_dialog.setText("An unexpected error occurred. The application will continue running.")
        error_dialog.setDetailedText(error_msg)
        error_dialog.exec_()
    
    # Call the default exception handler
    sys.__excepthook__(exctype, value, tb)

def main():
    """Main application entry point"""
    
    # Set global exception handler
    sys.excepthook = global_exception_handler
    
    try:
        # Enable high DPI scaling
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("AI Image Editor")
        app.setOrganizationName("AI Image Editor")
        
        # Set application style
        app.setStyle('Fusion')
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Run application
        sys.exit(app.exec_())
        
    except Exception as e:
        error_msg = f"Failed to start application: {str(e)}\n{traceback.format_exc()}"
        
        # Log to file
        with open('error.log', 'w') as f:
            f.write(error_msg)
        
        # Show error dialog
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "Application Error",
            f"Failed to start application:\n\n{str(e)}\n\nCheck error.log for details."
        )
        sys.exit(1)

if __name__ == '__main__':
    main()