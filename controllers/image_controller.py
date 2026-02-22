from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
import numpy as np
from PIL import ImageQt,Image
from models.image_model import ImageModel
from models.ai_model import AIModel
import io
from models.layer import LayerManager, Layer
import cv2

class ImageController(QObject):
    """Controller for image operations"""
    
    image_updated = pyqtSignal()
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.image_model = ImageModel()
        self.ai_model = AIModel()
        self.layer_manager = LayerManager()
        self.use_layers = False
        
    def load_image(self, filepath: str) -> bool:
        """Load image from file"""
        try:
            success = self.image_model.load_image(filepath)
            if success:
                self.image_updated.emit()
                self.status_updated.emit(f"Loaded: {self.image_model.image_data.name}")
            else:
                self.status_updated.emit("Failed to load image")
            return success
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
            return False
        
    def save_image(self, filepath: str) -> bool:
        """Save current image"""
        try:
            success = self.image_model.save_image(filepath)
            if success:
                self.status_updated.emit(f"Saved: {filepath}")
            else:
                self.status_updated.emit("Failed to save image")
            return success
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
            return False
        
    def get_current_pixmap(self) -> QPixmap:
        """Get current image as QPixmap for display"""
        if self.image_model.current_image:
            try:
                # Method 1: Using PIL ImageQt
                image_q = ImageQt.ImageQt(self.image_model.current_image)
                qimage = QImage(image_q)
                return QPixmap.fromImage(qimage)
            except AttributeError:
                # Method 2: Alternative conversion
                img_data = self.image_model.current_image.tobytes("raw", "RGB")
                qimage = QImage(img_data, 
                              self.image_model.current_image.width,
                              self.image_model.current_image.height,
                              self.image_model.current_image.width * 3,
                              QImage.Format_RGB888)
                return QPixmap.fromImage(qimage)
            except Exception:
                # Method 3: Bytes IO fallback
                byte_array = io.BytesIO()
                self.image_model.current_image.save(byte_array, format='PNG')
                pixmap = QPixmap()
                pixmap.loadFromData(byte_array.getvalue())
                return pixmap
        return None
        
    def adjust_brightness(self, value: int):
        """Adjust brightness (value from -100 to 100)"""
        try:
            factor = 1.0 + (value / 100.0)
            self.image_model.adjust_brightness(factor)
            self.image_updated.emit()
            self.status_updated.emit(f"Brightness adjusted: {value}%")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
        
    def adjust_contrast(self, value: int):
        """Adjust contrast (value from -100 to 100)"""
        try:
            factor = 1.0 + (value / 100.0)
            self.image_model.adjust_contrast(factor)
            self.image_updated.emit()
            self.status_updated.emit(f"Contrast adjusted: {value}%")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
        
    def adjust_saturation(self, value: int):
        """Adjust saturation (value from -100 to 100)"""
        try:
            factor = 1.0 + (value / 100.0)
            self.image_model.adjust_saturation(factor)
            self.image_updated.emit()
            self.status_updated.emit(f"Saturation adjusted: {value}%")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
        
    def adjust_sharpness(self, value: int):
        """Adjust sharpness (value from -100 to 100)"""
        try:
            factor = 1.0 + (value / 100.0)
            self.image_model.adjust_sharpness(factor)
            self.image_updated.emit()
            self.status_updated.emit(f"Sharpness adjusted: {value}%")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
        
    def apply_blur(self, radius: float):
        """Apply blur effect"""
        try:
            self.image_model.apply_blur(radius)
            self.image_updated.emit()
            self.status_updated.emit(f"Blur applied: radius {radius}")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
        
    def apply_edge_enhance(self):
        """Apply edge enhancement"""
        try:
            self.image_model.apply_edge_enhance()
            self.image_updated.emit()
            self.status_updated.emit("Edge enhancement applied")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
        
    def rotate(self, angle: float):
        """Rotate image"""
        try:
            self.image_model.rotate(angle)
            self.image_updated.emit()
            self.status_updated.emit(f"Rotated: {angle}°")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
        
    def flip_horizontal(self):
        """Flip image horizontally"""
        try:
            self.image_model.flip_horizontal()
            self.image_updated.emit()
            self.status_updated.emit("Flipped horizontally")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
        
    def flip_vertical(self):
        """Flip image vertically"""
        try:
            self.image_model.flip_vertical()
            self.image_updated.emit()
            self.status_updated.emit("Flipped vertically")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
        
    def reset_image(self):
        """Reset to original image"""
        try:
            self.image_model.reset_to_original()
            self.image_updated.emit()
            self.status_updated.emit("Reset to original")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
        
    def undo(self):
        """Undo last operation"""
        try:
            self.image_model.undo()
            self.image_updated.emit()
            self.status_updated.emit("Undo")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
        
    def redo(self):
        """Redo last operation"""
        try:
            self.image_model.redo()
            self.image_updated.emit()
            self.status_updated.emit("Redo")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
        
    def ai_enhance_resolution(self, scale: int = 2):
        """AI-based resolution enhancement"""
        try:
            self.progress_updated.emit(10)
            cv2_image = self.image_model.get_cv2_image()
            if cv2_image is not None:
                self.progress_updated.emit(30)
                enhanced = self.ai_model.enhance_resolution(cv2_image, scale)
                self.progress_updated.emit(80)
                self.image_model.update_from_cv2(enhanced)
                self.image_updated.emit()
                self.status_updated.emit(f"Resolution enhanced: {scale}x")
            self.progress_updated.emit(100)
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
            self.progress_updated.emit(100)
        
    def ai_denoise(self, strength: float = 0.1):
        """AI-based denoising"""
        try:
            self.progress_updated.emit(10)
            cv2_image = self.image_model.get_cv2_image()
            if cv2_image is not None:
                self.progress_updated.emit(40)
                denoised = self.ai_model.denoise_image(cv2_image, strength)
                self.progress_updated.emit(80)
                self.image_model.update_from_cv2(denoised)
                self.image_updated.emit()
                self.status_updated.emit("Noise reduction applied")
            self.progress_updated.emit(100)
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
            self.progress_updated.emit(100)
        
    def ai_auto_enhance(self):
        """AI-based auto enhancement"""
        try:
            self.progress_updated.emit(10)
            cv2_image = self.image_model.get_cv2_image()
            if cv2_image is not None:
                self.progress_updated.emit(30)
                enhanced = self.ai_model.auto_enhance(cv2_image)
                self.progress_updated.emit(80)
                self.image_model.update_from_cv2(enhanced)
                self.image_updated.emit()
                self.status_updated.emit("Auto enhancement applied")
            self.progress_updated.emit(100)
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
            self.progress_updated.emit(100)
        
    def ai_style_transfer(self, style: str):
        """Apply AI style transfer"""
        try:
            self.progress_updated.emit(10)
            cv2_image = self.image_model.get_cv2_image()
            if cv2_image is not None:
                self.progress_updated.emit(40)
                styled = self.ai_model.style_transfer(cv2_image, style)
                self.progress_updated.emit(80)
                self.image_model.update_from_cv2(styled)
                self.image_updated.emit()
                self.status_updated.emit(f"Style applied: {style}")
            self.progress_updated.emit(100)
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
            self.progress_updated.emit(100)
        
    def ai_remove_background(self):
        """Remove background using AI"""
        try:
            self.progress_updated.emit(10)
            cv2_image = self.image_model.get_cv2_image()
            if cv2_image is not None:
                self.progress_updated.emit(40)
                result = self.ai_model.remove_background(cv2_image)
                self.progress_updated.emit(80)
                self.image_model.update_from_cv2(result)
                self.image_updated.emit()
                self.status_updated.emit("Background removed")
            self.progress_updated.emit(100)
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
            self.progress_updated.emit(100)
        
    def ai_enhance_facial(self):
        """Enhance facial features"""
        try:
            self.progress_updated.emit(10)
            cv2_image = self.image_model.get_cv2_image()
            if cv2_image is not None:
                self.progress_updated.emit(40)
                enhanced = self.ai_model.enhance_facial_features(cv2_image)
                self.progress_updated.emit(80)
                self.image_model.update_from_cv2(enhanced)
                self.image_updated.emit()
                self.status_updated.emit("Facial features enhanced")
            self.progress_updated.emit(100)
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
            self.progress_updated.emit(100)

    def reset_image(self):
        """Reset to original image"""
        try:
            if hasattr(self.image_model, 'reset_to_original'):
                self.image_model.reset_to_original()
                self.image_updated.emit()
                self.status_updated.emit("Reset to original")
            else:
                # Fallback method
                if self.image_model.original_image:
                    self.image_model.current_image = self.image_model.original_image.copy()
                    self.image_model._add_to_history()
                    self.image_updated.emit()
                    self.status_updated.emit("Reset to original")
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")

    def toggle_layer_mode(self, enabled: bool):
        """Toggle layer mode on/off"""
        self.use_layers = enabled
        if enabled and self.image_model.current_image:
            # Create base layer from current image
            layer = Layer(self.image_model.current_image, "Background")
            self.layer_manager.add_layer(layer)
            self.status_updated.emit("Layer mode enabled")

    def add_layer(self, name: str = "New Layer"):
        """Add a new blank layer"""
        if self.image_model.current_image:
            # Create blank layer with same size
            blank = Image.new('RGBA', 
                            (self.image_model.current_image.width,
                            self.image_model.current_image.height),
                            (0, 0, 0, 0))
            layer = Layer(blank, name)
            self.layer_manager.add_layer(layer)
            self._update_from_layers()
            self.status_updated.emit(f"Layer added: {name}")

    def add_image_as_layer(self, image: Image.Image, name: str = "Image Layer"):
        """Add an image as a new layer"""
        layer = Layer(image, name)
        self.layer_manager.add_layer(layer)
        self._update_from_layers()
        self.status_updated.emit(f"Layer added: {name}")

    def remove_layer(self, index: int):
        """Remove a layer"""
        if self.use_layers:
            self.layer_manager.remove_layer(index)
            self._update_from_layers()
            self.status_updated.emit("Layer removed")

    def duplicate_layer(self, index: int):
        """Duplicate a layer"""
        if self.use_layers:
            self.layer_manager.duplicate_layer(index)
            self._update_from_layers()
            self.status_updated.emit("Layer duplicated")

    def merge_layers(self, indices: list):
        """Merge selected layers"""
        if self.use_layers and len(indices) >= 2:
            merged = self.layer_manager.merge_layers(indices)
            if merged:
                self._update_from_layers()
                self.status_updated.emit("Layers merged")

    def flatten_layers(self):
        """Flatten all layers"""
        if self.use_layers:
            flattened = self.layer_manager.flatten()
            if flattened:
                # Clear layers and set flattened as current
                self.layer_manager = LayerManager()
                layer = Layer(flattened, "Flattened")
                self.layer_manager.add_layer(layer)
                self.image_model.current_image = flattened
                self.image_model._add_to_history()
                self.image_updated.emit()
                self.status_updated.emit("Layers flattened")

    def set_layer_opacity(self, index: int, opacity: float):
        """Set layer opacity"""
        if self.use_layers and 0 <= index < len(self.layer_manager.layers):
            self.layer_manager.layers[index].opacity = opacity
            self._update_from_layers()

    def set_layer_blend_mode(self, index: int, mode: str):
        """Set layer blend mode"""
        if self.use_layers and 0 <= index < len(self.layer_manager.layers):
            self.layer_manager.layers[index].set_blend_mode(mode)
            self._update_from_layers()

    def set_layer_visibility(self, index: int, visible: bool):
        """Set layer visibility"""
        if self.use_layers and 0 <= index < len(self.layer_manager.layers):
            self.layer_manager.layers[index].visible = visible
            self._update_from_layers()

    def _update_from_layers(self):
        """Update current image from layers"""
        if self.use_layers:
            flattened = self.layer_manager.flatten()
            if flattened:
                self.image_model.current_image = flattened
                self.image_updated.emit()

    def get_layer_info(self) -> dict:
        """Get information about all layers"""
        if not self.use_layers:
            return None
        
        info = {
            'names': [],
            'thumbnails': [],
            'opacities': [],
            'blend_modes': [],
            'visibilities': []
        }
        
        for layer in self.layer_manager.layers:
            info['names'].append(layer.name)
            info['thumbnails'].append(layer.thumbnail)
            info['opacities'].append(layer.opacity)
            info['blend_modes'].append(layer.blend_mode)
            info['visibilities'].append(layer.visible)
        
        return info
    
    
    def adjust_hue(self, value: int):
        """Adjust image hue"""
        if self.image_model.current_image:
            try:
                # Convert to numpy array for processing
                img_array = np.array(self.image_model.current_image)
                
                # Convert to HSV
                if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
                    # Adjust hue
                    hsv[:, :, 0] = (hsv[:, :, 0] + value) % 180
                    # Convert back to RGB
                    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
                    self.image_model.current_image = Image.fromarray(rgb)
                    self.image_model._add_to_history()
                    self.image_updated.emit()
                    self.status_updated.emit(f"Hue adjusted: {value}")
            except Exception as e:
                self.status_updated.emit(f"Error adjusting hue: {str(e)}")

    def adjust_gamma(self, value: float):
        """Adjust image gamma"""
        if self.image_model.current_image:
            try:
                # Convert to numpy array
                img_array = np.array(self.image_model.current_image).astype(np.float32) / 255.0
                
                # Apply gamma correction
                gamma_corrected = np.power(img_array, 1.0 / value)
                gamma_corrected = (gamma_corrected * 255).astype(np.uint8)
                
                self.image_model.current_image = Image.fromarray(gamma_corrected)
                self.image_model._add_to_history()
                self.image_updated.emit()
                self.status_updated.emit(f"Gamma adjusted: {value:.2f}")
            except Exception as e:
                self.status_updated.emit(f"Error adjusting gamma: {str(e)}")