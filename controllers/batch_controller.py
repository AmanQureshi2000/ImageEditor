from PyQt5.QtCore import QObject, pyqtSignal, QThread
import os
import glob
from PIL import Image, ImageEnhance, ImageFilter
import traceback

class BatchProcessingThread(QThread):
    """Thread for batch processing multiple images"""
    
    progress = pyqtSignal(int, int)  # current, total
    file_completed = pyqtSignal(str)  # filename
    error = pyqtSignal(str, str)  # filename, error
    finished = pyqtSignal()
    status = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.input_files = []
        self.output_dir = ""
        self.operations = []  # List of (operation, params) tuples
        self._is_cancelled = False
        
    def setup(self, input_files, output_dir, operations):
        """Setup batch processing"""
        self.input_files = input_files
        self.output_dir = output_dir
        self.operations = operations
        self._is_cancelled = False
        
    def cancel(self):
        """Cancel batch processing"""
        self._is_cancelled = True
        
    def run(self):
        """Main thread execution"""
        try:
            total = len(self.input_files)
            
            for i, file_path in enumerate(self.input_files):
                if self._is_cancelled:
                    self.status.emit("Batch processing cancelled")
                    break
                
                self.status.emit(f"Processing {os.path.basename(file_path)} ({i+1}/{total})")
                self.progress.emit(i + 1, total)
                
                try:
                    self._process_single_image(file_path)
                    self.file_completed.emit(os.path.basename(file_path))
                except Exception as e:
                    self.error.emit(os.path.basename(file_path), str(e))
                    traceback.print_exc()
            
            self.finished.emit()
            
        except Exception as e:
            self.error.emit("Batch Error", str(e))
            self.finished.emit()
    
    # Add these improvements to BatchProcessingThread

    def _process_single_image(self, file_path):
        """Process a single image with all operations and error handling"""
        try:
            # Validate file exists and is readable
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check file size (skip if too large)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            if file_size > 100:  # Skip files larger than 100MB
                raise ValueError(f"File too large: {file_size:.1f}MB")
            
            # Load image with error handling
            try:
                img = Image.open(file_path)
                # Verify it's actually an image
                img.verify()
                # Reopen after verify
                img = Image.open(file_path)
            except Exception as e:
                raise ValueError(f"Invalid or corrupted image: {str(e)}")
            
            # Convert to RGB if necessary
            if img.mode not in ['RGB', 'RGBA']:
                img = img.convert('RGB')
            
            # Apply each operation
            for operation, params in self.operations:
                if self._is_cancelled:
                    return
                
                try:
                    img = self._apply_operation(img, operation, params)
                except Exception as e:
                    raise RuntimeError(f"Operation {operation} failed: {str(e)}")
            
            # Generate output path
            base_name = os.path.basename(file_path)
            name, ext = os.path.splitext(base_name)
            
            # Check if format conversion is requested
            output_format = None
            for op, params in self.operations:
                if op == 'convert_format':
                    output_format = params.get('format', 'JPEG').lower()
                    if output_format == 'jpeg':
                        output_format = 'jpg'
                    break
            
            if output_format:
                output_path = os.path.join(self.output_dir, f"{name}.{output_format}")
            else:
                output_path = os.path.join(self.output_dir, base_name)
            
            # Ensure output directory exists
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Save with appropriate format
            save_kwargs = {}
            if output_format in ['jpg', 'jpeg']:
                save_kwargs['quality'] = 95
                save_kwargs['optimize'] = True
            elif output_format == 'png':
                save_kwargs['optimize'] = True
                save_kwargs['compress_level'] = 6
            
            img.save(output_path, **save_kwargs)
            
        except Exception as e:
            raise RuntimeError(f"Failed to process {os.path.basename(file_path)}: {str(e)}") 
    
    def _apply_operation(self, img, operation, params):
        """Apply a single operation to image"""
        
        if operation == 'resize':
            width = params.get('width', img.width)
            height = params.get('height', img.height)
            return img.resize((width, height), Image.Resampling.LANCZOS)
        
        elif operation == 'brightness':
            factor = params.get('factor', 1.0)
            enhancer = ImageEnhance.Brightness(img)
            return enhancer.enhance(factor)
        
        elif operation == 'contrast':
            factor = params.get('factor', 1.0)
            enhancer = ImageEnhance.Contrast(img)
            return enhancer.enhance(factor)
        
        elif operation == 'saturation':
            factor = params.get('factor', 1.0)
            enhancer = ImageEnhance.Color(img)
            return enhancer.enhance(factor)
        
        elif operation == 'sharpness':
            factor = params.get('factor', 1.0)
            enhancer = ImageEnhance.Sharpness(img)
            return enhancer.enhance(factor)
        
        elif operation == 'blur':
            radius = params.get('radius', 2)
            return img.filter(ImageFilter.GaussianBlur(radius=radius))
        
        elif operation == 'rotate':
            angle = params.get('angle', 0)
            return img.rotate(angle, expand=True)
        
        elif operation == 'copy':
            return img.copy()
        
        return img

class BatchController(QObject):
    """Controller for batch processing operations"""
    
    batch_started = pyqtSignal()
    batch_progress = pyqtSignal(int, int)
    batch_file_completed = pyqtSignal(str)
    batch_error = pyqtSignal(str, str)
    batch_finished = pyqtSignal()
    batch_status = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.thread = BatchProcessingThread()
        self.is_processing = False
        
        # Connect signals
        self.thread.progress.connect(self.batch_progress)
        self.thread.file_completed.connect(self.batch_file_completed)
        self.thread.error.connect(self.batch_error)
        self.thread.finished.connect(self._on_batch_finished)
        self.thread.status.connect(self.batch_status)
        
    def process_batch(self, input_files, output_dir, operations):
        """Start batch processing"""
        if self.is_processing:
            self.batch_status.emit("Batch processing already in progress")
            return
        
        # Validate inputs
        if not input_files:
            self.batch_error.emit("No files", "No input files selected")
            return
        
        if not output_dir:
            self.batch_error.emit("No output directory", "Please select output directory")
            return
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                self.batch_error.emit("Output directory error", str(e))
                return
        
        self.is_processing = True
        self.thread.setup(input_files, output_dir, operations)
        self.batch_started.emit()
        
        if not self.thread.isRunning():
            self.thread.start()
    
    def cancel_batch(self):
        """Cancel batch processing"""
        if self.is_processing and self.thread.isRunning():
            self.thread.cancel()
            self.thread.quit()
            self.thread.wait(2000)
            if self.thread.isRunning():
                self.thread.terminate()
                self.thread.wait()
            self.is_processing = False
    
    def _on_batch_finished(self):
        """Handle batch completion"""
        self.is_processing = False
        self.batch_finished.emit()
    
    def get_supported_formats(self):
        """Get list of supported image formats"""
        return {
            '*.jpg': 'JPEG files',
            '*.jpeg': 'JPEG files',
            '*.png': 'PNG files',
            '*.bmp': 'BMP files',
            '*.gif': 'GIF files',
            '*.tiff': 'TIFF files',
            '*.webp': 'WebP files'
        }
    
    def collect_files(self, input_paths, recursive=False):
        """Collect all image files from given paths"""
        files = []
        extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
        
        for path in input_paths:
            if os.path.isfile(path):
                ext = os.path.splitext(path)[1].lower()
                if ext in extensions:
                    files.append(path)
            elif os.path.isdir(path):
                if recursive:
                    for ext in extensions:
                        files.extend(glob.glob(os.path.join(path, '**', f'*{ext}'), recursive=True))
                else:
                    for ext in extensions:
                        files.extend(glob.glob(os.path.join(path, f'*{ext}')))
        
        return sorted(list(set(files)))  # Remove duplicates