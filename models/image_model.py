import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ExifTags
import cv2
from dataclasses import dataclass
from typing import Optional, Tuple, List
import os
import warnings
import traceback
import io
import time
from collections import OrderedDict

# Custom Exceptions
class ImageLoadError(Exception):
    """Raised when image loading fails"""
    pass

class ImageSaveError(Exception):
    """Raised when image saving fails"""
    pass

class ImageProcessingError(Exception):
    """Raised when image processing fails"""
    pass

@dataclass
class ImageData:
    """Data class to hold image information"""
    path: str
    name: str
    width: int
    height: int
    mode: str
    format: str
    size: int  # in bytes
    exif_data: dict = None

class ImageModel:
    """Model class for handling image operations with performance optimizations"""
    
    # Supported formats
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}
    MAX_IMAGE_SIZE_MB = 100  # Maximum image size in MB
    MAX_HISTORY_ITEMS = 20  # Maximum number of history items
    MAX_HISTORY_MEMORY_MB = 200  # Maximum memory for history in MB
    THUMBNAIL_SIZE = (100, 100)  # Size for history thumbnails
    
    def __init__(self):
        self.current_image: Optional[Image.Image] = None
        self.original_image: Optional[Image.Image] = None
        self.image_data: Optional[ImageData] = None
        
        # Optimized history storage
        self.history_data: List[bytes] = []  # Compressed image data
        self.history_thumbnails: List[Image.Image] = []  # Thumbnails for display
        self.history_sizes: List[int] = []  # Size of each history item in bytes
        self.history_timestamps: List[float] = []  # For LRU cleanup
        self.current_history_index: int = -1
        
        # Cache for frequently used operations
        self._cache = OrderedDict()
        self._cache_max_size = 10
        self._cache_max_memory_mb = 50
        
        self._processing = False
        
    def _get_image_size_bytes(self, image: Image.Image) -> int:
        """Calculate approximate memory size of image in bytes"""
        if image:
            width, height = image.size
            channels = len(image.getbands())
            return width * height * channels
        return 0
        
    def _compress_image(self, image: Image.Image, quality: int = 85) -> bytes:
        """Compress image for history storage"""
        buffer = io.BytesIO()
        # Use JPEG for RGB, PNG for RGBA
        if image.mode == 'RGBA':
            image.save(buffer, format='PNG', optimize=True)
        else:
            # Convert to RGB for JPEG compression
            if image.mode != 'RGB':
                rgb_image = image.convert('RGB')
            else:
                rgb_image = image
            rgb_image.save(buffer, format='JPEG', quality=quality, optimize=True)
        return buffer.getvalue()
    
    def _decompress_image(self, data: bytes) -> Image.Image:
        """Decompress image from history storage"""
        return Image.open(io.BytesIO(data))
    
    def _create_thumbnail(self, image: Image.Image) -> Image.Image:
        """Create thumbnail for history display"""
        thumb = image.copy()
        thumb.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        return thumb
    
    def _cleanup_history_by_memory(self):
        """Remove oldest history items if memory limit exceeded"""
        total_memory = sum(self.history_sizes) / (1024 * 1024)  # Convert to MB
        
        while total_memory > self.MAX_HISTORY_MEMORY_MB and len(self.history_data) > 1:
            # Remove oldest item (but keep current)
            if self.current_history_index > 0:
                removed_data = self.history_data.pop(0)
                removed_thumb = self.history_thumbnails.pop(0)
                removed_size = self.history_sizes.pop(0)
                self.history_timestamps.pop(0)
                total_memory -= removed_size / (1024 * 1024)
                self.current_history_index -= 1
                
                # Explicitly delete to help garbage collection
                del removed_data
                del removed_thumb
            else:
                break

    def validate_image_format(self, filepath: str) -> bool:
        """Validate that file is a supported image format"""
        import imghdr
        
        # Check by extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in valid_extensions:
            return False
        
        # Check by magic numbers
        image_type = imghdr.what(filepath)
        return image_type is not None
    
    def _add_to_history(self):
        """Add current state to history with compression"""
        if self._processing:
            return
            
        if self.current_image:
            try:
                # Remove future history if we're not at the end
                if self.current_history_index < len(self.history_data) - 1:
                    self.history_data = self.history_data[:self.current_history_index + 1]
                    self.history_thumbnails = self.history_thumbnails[:self.current_history_index + 1]
                    self.history_sizes = self.history_sizes[:self.current_history_index + 1]
                    self.history_timestamps = self.history_timestamps[:self.current_history_index + 1]
                
                # Compress and store current image
                compressed = self._compress_image(self.current_image)
                thumbnail = self._create_thumbnail(self.current_image)
                size_bytes = len(compressed)
                
                self.history_data.append(compressed)
                self.history_thumbnails.append(thumbnail)
                self.history_sizes.append(size_bytes)
                self.history_timestamps.append(time.time())
                self.current_history_index = len(self.history_data) - 1
                
                # Limit history size
                if len(self.history_data) > self.MAX_HISTORY_ITEMS:
                    self.history_data.pop(0)
                    self.history_thumbnails.pop(0)
                    self.history_sizes.pop(0)
                    self.history_timestamps.pop(0)
                    self.current_history_index -= 1
                
                # Check memory limit
                self._cleanup_history_by_memory()
                    
            except Exception as e:
                print(f"Warning: Failed to add to history: {e}")

    

    def save_image(self, filepath: str, format: str = None, quality: int = 95) -> bool:
        """Save the current image with error handling and validation"""
        try:
            if self.current_image is None:
                raise ImageSaveError("No image to save")
            
            # Validate format
            valid_formats = ['JPEG', 'JPG', 'PNG', 'BMP', 'TIFF', 'WEBP', 'GIF']
            if format and format.upper() not in valid_formats:
                format = 'PNG'  # Default to PNG
                warnings.warn(f"Invalid format specified, using PNG")
            
            # Check if file exists and ask for confirmation
            if os.path.exists(filepath):
                # This should be handled by UI, but we'll warn
                warnings.warn(f"File already exists: {filepath}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            # Save with appropriate parameters
            save_kwargs = {}
            if format and format.upper() in ['JPEG', 'JPG']:
                save_kwargs['quality'] = max(1, min(100, quality))
                save_kwargs['optimize'] = True
                save_kwargs['progressive'] = True
            elif format and format.upper() == 'PNG':
                save_kwargs['optimize'] = True
                save_kwargs['compress_level'] = 6
            elif format and format.upper() == 'WEBP':
                save_kwargs['quality'] = max(1, min(100, quality))
                save_kwargs['method'] = 6  # Slower but better compression
            
            self.current_image.save(filepath, format=format, **save_kwargs)
            
            # Verify save was successful
            if not os.path.exists(filepath):
                raise ImageSaveError("File was not created")
                
            return True
            
        except ImageSaveError:
            raise
        except Exception as e:
            raise ImageSaveError(f"Failed to save image: {str(e)}")
    
    def _clear_history(self):
        """Clear history to free memory"""
        self.history_data = []
        self.history_thumbnails = []
        self.history_sizes = []
        self.history_timestamps = []
        self.current_history_index = -1
        
    def load_image(self, filepath: str) -> bool:
        """Load an image from file with comprehensive error handling"""
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                raise ImageLoadError(f"File not found: {filepath}")
            
            # Check file size
            file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
            if file_size > self.MAX_IMAGE_SIZE_MB:
                raise ImageLoadError(f"Image too large: {file_size:.1f}MB (max: {self.MAX_IMAGE_SIZE_MB}MB)")
            
            # Check file format
            file_ext = os.path.splitext(filepath)[1].lower()
            if file_ext not in self.SUPPORTED_FORMATS:
                raise ImageLoadError(f"Unsupported format: {file_ext}")
            
            # Load image with PIL
            try:
                self.original_image = Image.open(filepath)
            except Exception as e:
                raise ImageLoadError(f"PIL cannot open image: {str(e)}")
            
            # Handle EXIF orientation
            try:
                exif = self.original_image._getexif()
                if exif:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation':
                            break
                    
                    if exif.get(orientation) == 3:
                        self.original_image = self.original_image.rotate(180, expand=True)
                    elif exif.get(orientation) == 6:
                        self.original_image = self.original_image.rotate(270, expand=True)
                    elif exif.get(orientation) == 8:
                        self.original_image = self.original_image.rotate(90, expand=True)
            except:
                warnings.warn("Could not read EXIF orientation data")
            
            # Convert to RGB for consistency
            try:
                if self.original_image.mode not in ['RGB', 'RGBA']:
                    self.original_image = self.original_image.convert('RGB')
                elif self.original_image.mode == 'RGBA':
                    # Keep RGBA for transparency
                    pass
                else:
                    self.original_image = self.original_image.convert('RGB')
            except Exception as e:
                raise ImageLoadError(f"Failed to convert image mode: {str(e)}")
            
            # Check if image loaded successfully
            if self.original_image is None:
                raise ImageLoadError("Image loaded but is None")
            
            self.current_image = self.original_image.copy()
            
            # Extract EXIF data
            exif_data = {}
            try:
                if hasattr(self.original_image, '_getexif') and self.original_image._getexif():
                    exif = self.original_image._getexif()
                    for tag_id, value in exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        exif_data[tag] = str(value)
            except:
                exif_data = None
            
            # Get image info
            file_stats = os.stat(filepath)
            self.image_data = ImageData(
                path=filepath,
                name=os.path.basename(filepath),
                width=self.current_image.width,
                height=self.current_image.height,
                mode=self.current_image.mode,
                format=self.current_image.format or 'Unknown',
                size=file_stats.st_size,
                exif_data=exif_data
            )
            
            # Clear history for new image
            self._clear_history()
            self._add_to_history()
            
            return True
            
        except ImageLoadError as e:
            print(f"Image load error: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error loading image: {e}")
            traceback.print_exc()
            raise ImageLoadError(f"Unexpected error: {str(e)}")
    
    def undo(self):
        """Undo last operation with optimized loading"""
        if self.current_history_index > 0:
            self.current_history_index -= 1
            # Decompress from history
            compressed = self.history_data[self.current_history_index]
            self.current_image = self._decompress_image(compressed)
        else:
            warnings.warn("Cannot undo: at beginning of history")
    
    def redo(self):
        """Redo last undone operation with optimized loading"""
        if self.current_history_index < len(self.history_data) - 1:
            self.current_history_index += 1
            # Decompress from history
            compressed = self.history_data[self.current_history_index]
            self.current_image = self._decompress_image(compressed)
        else:
            warnings.warn("Cannot redo: at end of history")
    
    def get_history_thumbnails(self) -> List[Image.Image]:
        """Get thumbnails for history display"""
        return self.history_thumbnails.copy()
    
    # Cache methods for frequently used operations
    def _get_cached(self, key: str):
        """Get item from cache"""
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None
    
    def _set_cache(self, key: str, value):
        """Set item in cache with LRU eviction"""
        self._cache[key] = value
        self._cache.move_to_end(key)
        
        # Check memory limit
        if len(self._cache) > self._cache_max_size:
            self._cache.popitem(last=False)
    
    def get_cv2_image_cached(self) -> Optional[np.ndarray]:
        """Get CV2 image with caching"""
        if self.current_image is None:
            return None
        
        # Use image dimensions and mode as cache key
        cache_key = f"{id(self.current_image)}_{self.current_image.size}_{self.current_image.mode}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached.copy()  # Return copy to prevent modification
        
        # Convert and cache
        try:
            open_cv_image = np.array(self.current_image)
            if open_cv_image.shape[-1] == 4:  # RGBA
                open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGBA2BGRA)
            else:  # RGB
                open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
            
            self._set_cache(cache_key, open_cv_image.copy())
            return open_cv_image
        except Exception as e:
            print(f"Error converting to CV2 image: {e}")
            return None
    
    # Existing methods with performance optimizations
    def adjust_brightness(self, factor: float):
        """Adjust image brightness with error handling"""
        try:
            if self.current_image is None:
                raise ImageProcessingError("No image loaded")
            
            self._processing = True
            enhancer = ImageEnhance.Brightness(self.current_image)
            self.current_image = enhancer.enhance(factor)
            self._add_to_history()
            self._cache.clear()  # Clear cache on image change
            self._processing = False
        except Exception as e:
            self._processing = False
            raise ImageProcessingError(f"Brightness adjustment failed: {str(e)}")
    
    # ... (other adjustment methods remain similar with cache clearing)
    
    def adjust_contrast(self, factor: float):
        """Adjust image contrast"""
        try:
            if self.current_image is None:
                raise ImageProcessingError("No image loaded")
            
            self._processing = True
            enhancer = ImageEnhance.Contrast(self.current_image)
            self.current_image = enhancer.enhance(factor)
            self._add_to_history()
            self._cache.clear()
            self._processing = False
        except Exception as e:
            self._processing = False
            raise ImageProcessingError(f"Contrast adjustment failed: {str(e)}")
    
    def adjust_saturation(self, factor: float):
        """Adjust image saturation"""
        try:
            if self.current_image is None:
                raise ImageProcessingError("No image loaded")
            
            self._processing = True
            enhancer = ImageEnhance.Color(self.current_image)
            self.current_image = enhancer.enhance(factor)
            self._add_to_history()
            self._cache.clear()
            self._processing = False
        except Exception as e:
            self._processing = False
            raise ImageProcessingError(f"Saturation adjustment failed: {str(e)}")
    
    def adjust_sharpness(self, factor: float):
        """Adjust image sharpness"""
        try:
            if self.current_image is None:
                raise ImageProcessingError("No image loaded")
            
            self._processing = True
            enhancer = ImageEnhance.Sharpness(self.current_image)
            self.current_image = enhancer.enhance(factor)
            self._add_to_history()
            self._cache.clear()
            self._processing = False
        except Exception as e:
            self._processing = False
            raise ImageProcessingError(f"Sharpness adjustment failed: {str(e)}")
    
    def apply_blur(self, radius: float = 2):
        """Apply Gaussian blur"""
        try:
            if self.current_image:
                self._processing = True
                self.current_image = self.current_image.filter(
                    ImageFilter.GaussianBlur(radius=radius)
                )
                self._add_to_history()
                self._cache.clear()
                self._processing = False
        except Exception as e:
            self._processing = False
            raise ImageProcessingError(f"Blur failed: {str(e)}")
    
    def rotate(self, angle: float):
        """Rotate image"""
        try:
            if self.current_image:
                self._processing = True
                self.current_image = self.current_image.rotate(angle, expand=True)
                self._add_to_history()
                self._cache.clear()
                self._processing = False
        except Exception as e:
            self._processing = False
            raise ImageProcessingError(f"Rotation failed: {str(e)}")
    
    def crop(self, box: Tuple[int, int, int, int]):
        """Crop image (left, top, right, bottom)"""
        try:
            if self.current_image:
                self._processing = True
                self.current_image = self.current_image.crop(box)
                self._add_to_history()
                self._cache.clear()
                self._processing = False
        except Exception as e:
            self._processing = False
            raise ImageProcessingError(f"Crop failed: {str(e)}")
    
    def reset_to_original(self):
        """Reset to original image"""
        if self.original_image:
            self._processing = True
            self.current_image = self.original_image.copy()
            self._add_to_history()
            self._cache.clear()
            self._processing = False