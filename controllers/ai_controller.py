from PyQt5.QtCore import QObject, pyqtSignal, QThread, QMutex, QWaitCondition,QMutexLocker
import numpy as np
import cv2
import traceback
import time
from models.ai_model import AIModel

class AIProcessingThread(QThread):
    """Dedicated thread for AI processing with improved thread safety"""
    
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.ai_model = AIModel()
        self.operation = None
        self.image = None
        self.params = {}
        self._is_cancelled = False
        self.mutex = QMutex()
        self.result = None
        
    def setup(self, operation: str, image: np.ndarray, params: dict):
        """Setup the thread for processing"""
        with QMutexLocker(self.mutex):
            self.operation = operation
            # Create a deep copy to prevent modification from main thread
            self.image = image.copy() if image is not None else None
            self.params = params.copy()
            self._is_cancelled = False
            self.result = None
        
    def cancel(self):
        """Cancel the current operation"""
        with QMutexLocker(self.mutex):
            self._is_cancelled = True
        
    def run(self):
        """Main thread execution"""
        try:
            # Get a local copy of parameters
            with QMutexLocker(self.mutex):
                if self.image is None:
                    self.error.emit("No image provided")
                    return
                
                operation = self.operation
                image = self.image.copy()  # Another copy for processing
                params = self.params.copy()
                is_cancelled = self._is_cancelled
            
            if is_cancelled:
                return
                
            self.status.emit(f"Starting {operation}...")
            
            # Map operations to methods
            operation_map = {
                'enhance_resolution': self._enhance_resolution,
                'denoise': self._denoise,
                'colorize': self._colorize,
                'remove_background': self._remove_background,
                'enhance_facial': self._enhance_facial,
                'style_transfer': self._style_transfer,
                'auto_enhance': self._auto_enhance
            }
            
            if operation not in operation_map:
                self.error.emit(f"Unknown operation: {operation}")
                return
            
            # Check cancellation before processing
            with QMutexLocker(self.mutex):
                if self._is_cancelled:
                    return
            
            # Execute the operation
            start_time = time.time()
            result = operation_map[operation](image, params)
            processing_time = time.time() - start_time
            
            # Check cancellation after processing
            with QMutexLocker(self.mutex):
                if self._is_cancelled:
                    return
                
                if result is not None:
                    self.result = result.copy()  # Store result for later
                    self.finished.emit(result)
                    self.status.emit(f"{operation} completed in {processing_time:.2f}s")
                else:
                    self.error.emit(f"{operation} returned no result")
                
        except Exception as e:
            self.error.emit(f"Error in {operation}: {str(e)}")
            traceback.print_exc()
            
    def _enhance_resolution(self, image, params):
        """Enhance resolution with progress updates"""
        scale = params.get('scale', 2)
        self.progress.emit(10)
        
        # Check cancellation
        with QMutexLocker(self.mutex):
            if self._is_cancelled: return None
        
        result = self.ai_model.enhance_resolution(image, scale)
        self.progress.emit(80)
        
        with QMutexLocker(self.mutex):
            if self._is_cancelled: return None
        
        # Apply additional sharpening
        if not self._is_cancelled:
            kernel = np.array([[-1,-1,-1],
                              [-1, 9,-1],
                              [-1,-1,-1]])
            result = cv2.filter2D(result, -1, kernel)
            
        self.progress.emit(100)
        return result
        
    def _denoise(self, image, params):
        """Denoise image with progress updates"""
        strength = params.get('strength', 0.1)
        self.progress.emit(10)
        
        with QMutexLocker(self.mutex):
            if self._is_cancelled: return None
        
        result = self.ai_model.denoise_image(image, strength)
        self.progress.emit(100)
        return result
        
    def _colorize(self, image, params):
        """Colorize image with progress updates"""
        self.progress.emit(10)
        
        with QMutexLocker(self.mutex):
            if self._is_cancelled: return None
        
        result = self.ai_model.colorize_image(image)
        self.progress.emit(100)
        return result
        
    def _remove_background(self, image, params):
        """Remove background with progress updates"""
        self.progress.emit(10)
        
        with QMutexLocker(self.mutex):
            if self._is_cancelled: return None
        
        result = self.ai_model.remove_background(image)
        self.progress.emit(80)
        
        with QMutexLocker(self.mutex):
            if self._is_cancelled: return None
        
        # Post-process to clean up
        if result.shape[-1] == 4:  # Has alpha
            alpha = result[:, :, 3]
            alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
            result[:, :, 3] = alpha
            
        self.progress.emit(100)
        return result
        
    def _enhance_facial(self, image, params):
        """Enhance facial features with progress updates"""
        self.progress.emit(10)
        
        with QMutexLocker(self.mutex):
            if self._is_cancelled: return None
        
        result = self.ai_model.enhance_facial_features(image)
        self.progress.emit(100)
        return result
        
    def _style_transfer(self, image, params):
        """Apply style transfer with progress updates"""
        style = params.get('style', 'cartoon')
        self.progress.emit(10)
        
        with QMutexLocker(self.mutex):
            if self._is_cancelled: return None
        
        result = self.ai_model.style_transfer(image, style)
        self.progress.emit(100)
        return result
        
    def _auto_enhance(self, image, params):
        """Auto enhance with progress updates"""
        self.progress.emit(10)
        
        with QMutexLocker(self.mutex):
            if self._is_cancelled: return None
        
        result = self.ai_model.auto_enhance(image)
        self.progress.emit(50)
        
        with QMutexLocker(self.mutex):
            if self._is_cancelled: return None
        
        # Apply additional enhancements
        result = self.ai_model._auto_contrast(result)
        self.progress.emit(80)
        
        with QMutexLocker(self.mutex):
            if self._is_cancelled: return None
        
        result = self.ai_model._enhance_colors(result)
        self.progress.emit(100)
        return result

class AIController(QObject):
    """Controller for AI-specific operations with improved thread safety"""
    
    ai_processing_started = pyqtSignal()
    ai_processing_finished = pyqtSignal()
    ai_progress_updated = pyqtSignal(int)
    ai_status_updated = pyqtSignal(str)
    ai_error_occurred = pyqtSignal(str)
    ai_result_ready = pyqtSignal(object)
    
    def __init__(self, image_model):
        super().__init__()
        self.image_model = image_model
        self.thread = AIProcessingThread()
        self.is_processing = False
        self.processing_queue = []
        self.mutex = QMutex()
        
        # Connect thread signals
        self.thread.progress.connect(self.ai_progress_updated)
        self.thread.finished.connect(self._on_processing_finished)
        self.thread.error.connect(self._on_processing_error)
        self.thread.status.connect(self.ai_status_updated)
        
    def process_with_ai(self, operation: str, **kwargs):
        """Process image with AI operation in separate thread"""
        with QMutexLocker(self.mutex):
            if self.is_processing:
                # Add to queue instead of rejecting
                self.processing_queue.append({
                    'operation': operation,
                    'params': kwargs
                })
                self.ai_status_updated.emit(f"Operation queued. {len(self.processing_queue)} waiting.")
                return
            
            # Get current image (create a copy for thread safety)
            cv2_image = self.image_model.get_cv2_image()
            if cv2_image is None:
                self.ai_error_occurred.emit("No image loaded")
                return
            
            # Make a deep copy for thread safety
            image_copy = cv2_image.copy()
            
            # Setup and start thread
            self.is_processing = True
            self.thread.setup(operation, image_copy, kwargs)
            
        # Emit signals outside mutex
        self.ai_processing_started.emit()
        self.ai_status_updated.emit(f"Starting {operation.replace('_', ' ')}...")
        
        # Start thread
        if not self.thread.isRunning():
            self.thread.start()
    
    def cancel_processing(self):
        """Cancel current AI processing"""
        with QMutexLocker(self.mutex):
            if self.is_processing and self.thread.isRunning():
                self.thread.cancel()
                self.thread.quit()
                self.thread.wait(2000)
                if self.thread.isRunning():
                    self.thread.terminate()
                    self.thread.wait()
                
                self.is_processing = False
                self.processing_queue.clear()
        
        self.ai_status_updated.emit("Processing cancelled")
        self.ai_processing_finished.emit()
    
    def _on_processing_finished(self, result):
        """Handle successful processing completion"""
        next_operation = None
        
        with QMutexLocker(self.mutex):
            if result is not None:
                # Update image model in main thread
                try:
                    self.image_model.update_from_cv2(result)
                    self.ai_result_ready.emit(result)
                    self.ai_status_updated.emit("AI processing completed")
                except Exception as e:
                    self.ai_error_occurred.emit(f"Failed to update image: {str(e)}")
            
            # Check for next operation in queue
            if self.processing_queue:
                next_operation = self.processing_queue.pop(0)
                self.is_processing = True
            else:
                self.is_processing = False
        
        # Process next operation if any
        if next_operation:
            self.process_with_ai(next_operation['operation'], **next_operation['params'])
        else:
            self.ai_processing_finished.emit()
    
    def _on_processing_error(self, error_msg):
        """Handle processing errors"""
        next_operation = None
        
        with QMutexLocker(self.mutex):
            self.is_processing = False
            # Clear queue on error
            self.processing_queue.clear()
        
        self.ai_error_occurred.emit(error_msg)
        self.ai_processing_finished.emit()
    
    def get_queue_status(self) -> dict:
        """Get current queue status"""
        with QMutexLocker(self.mutex):
            return {
                'is_processing': self.is_processing,
                'queue_length': len(self.processing_queue),
                'thread_running': self.thread.isRunning()
            }
    
    def get_available_models(self) -> dict:
        """Get available AI models and their status"""
        return {
            "super_resolution": True,
            "denoising": True,
            "colorization": True,
            "initialized": True
        }
    
