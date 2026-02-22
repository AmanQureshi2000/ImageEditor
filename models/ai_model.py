import numpy as np
import cv2
import warnings
from utils.lazy_loader import LazyLoader, LazyModel
from utils.cache_manager import ImageCache
warnings.filterwarnings('ignore')

class AIModel:
    """Model class for AI-powered image enhancements using OpenCV"""
    
    def __init__(self):
        self.initialized = True
        self.lazy_loader = LazyLoader()
        self.cache = ImageCache()
        
        # Lazy-loaded models
        self._torch = LazyModel('torch', self.lazy_loader, lambda m: m)
        self._torchvision = LazyModel('torchvision', self.lazy_loader, lambda m: m)
        self._onnx = LazyModel('onnxruntime', self.lazy_loader, lambda m: m)
        self._skimage = LazyModel('skimage', self.lazy_loader, lambda m: m)
        
        print("AI Model initialized with lazy loading!")
        
    def _validate_and_prepare_image(self, image: np.ndarray, required_channels: int = 3) -> np.ndarray:
        """Validate image and ensure correct format for OpenCV operations"""
        if image is None:
            raise ValueError("Invalid input image")
        
        # Check if image is empty
        if image.size == 0:
            raise ValueError("Empty image")
        
        # Ensure image is 8-bit
        if image.dtype != np.uint8:
            image = cv2.convertScaleAbs(image)
        
        # Convert grayscale to BGR if needed
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:  # RGBA
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        elif image.shape[2] == 3:  # RGB
            # Assume it's BGR already (from get_cv2_image)
            pass
            
        return image
        
    def enhance_resolution(self, image: np.ndarray, scale: int = 2) -> np.ndarray:
        """Enhance image resolution using advanced interpolation"""
        # Generate cache key
        image_id = id(image)
        cache_key = f"enhance_resolution_{image_id}_{scale}"
        
        # Check cache
        cached = self.cache.get_processed(image_id, 'enhance_resolution', {'scale': scale})
        if cached is not None:
            return cached
        try:
            image = self._validate_and_prepare_image(image)
            
            height, width = image.shape[:2]
            
            # Validate scale
            if scale < 1 or scale > 8:
                scale = 2  # Default to safe value
                warnings.warn("Scale must be between 1 and 8, using default 2")
            
            new_dimensions = (width * scale, height * scale)
            
            # Choose interpolation method based on scale
            if scale <= 2:
                enhanced = cv2.resize(image, new_dimensions, interpolation=cv2.INTER_CUBIC)
            else:
                enhanced = cv2.resize(image, new_dimensions, interpolation=cv2.INTER_LANCZOS4)
            
            # Apply sharpening to enhance details
            kernel = np.array([[-1,-1,-1],
                              [-1, 9,-1],
                              [-1,-1,-1]])
            enhanced = cv2.filter2D(enhanced, -1, kernel)
            self.cache.cache_processed(image_id, 'enhance_resolution', {'scale': scale}, enhanced)
            return enhanced
            
        except Exception as e:
            raise RuntimeError(f"Resolution enhancement failed: {str(e)}")
        
    def denoise_image(self, image: np.ndarray, strength: float = 0.1) -> np.ndarray:
        """Remove noise from image using advanced denoising"""
        image_id = id(image)
        cache_key = f"denoise_{image_id}_{strength}"
        
        # Check cache
        cached = self.cache.get_processed(image_id, 'denoise', {'strength': strength})
        if cached is not None:
            return cached
        try:
            image = self._validate_and_prepare_image(image)
            
            # Convert strength to appropriate parameters
            h = strength * 20  # Filter strength
            h_color = h  # For color images
            
            # Apply Non-local Means Denoising
            denoised = cv2.fastNlMeansDenoisingColored(
                image, None, h, h_color, 7, 21
            )

            self.cache.cache_processed(image_id, 'denoise', {'strength': strength}, denoised)
                
            return denoised
            
        except Exception as e:
            raise RuntimeError(f"Denoising failed: {str(e)}")
        
    def colorize_image(self, image: np.ndarray) -> np.ndarray:
        """Colorize black and white image"""
        try:
            if len(image.shape) == 2:
                gray = image
            elif image.shape[2] == 1:
                gray = image[:, :, 0]
            elif image.shape[2] == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                return image
                
            # Apply different color maps for artistic effect
            colored1 = cv2.applyColorMap(gray, cv2.COLORMAP_TURBO)
            colored2 = cv2.applyColorMap(gray, cv2.COLORMAP_VIRIDIS)
            
            # Blend the color maps
            colored = cv2.addWeighted(colored1, 0.5, colored2, 0.5, 0)
            return colored
            
        except Exception as e:
            raise RuntimeError(f"Colorization failed: {str(e)}")
        
    def remove_background(self, image: np.ndarray) -> np.ndarray:
        """Remove background from image using GrabCut algorithm"""
        # Check if we can use the real model (lazy loaded)
        if self._onnx.is_available():
            try:
                return self._real_background_removal(image)
            except:
                pass
        
        # Fallback to GrabCut
        return self._fallback_background_removal(image)
    
    def _real_background_removal(self, image: np.ndarray) -> np.ndarray:
        """Real background removal using ONNX model"""
        # This would use the actual ONNX model
        # For now, use fallback
        return self._fallback_background_removal(image)
    
    def _fallback_background_removal(self, image: np.ndarray) -> np.ndarray:
        """Fallback background removal using GrabCut"""
        # Ensure image is 8UC3 for grabCut
        if len(image.shape) != 3 or image.shape[2] != 3:
            image = self._validate_and_prepare_image(image)
        
        # Create a copy for processing
        img_copy = image.copy()
        
        mask = np.zeros(img_copy.shape[:2], np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        
        # Create initial rectangle (assume object is centered)
        height, width = img_copy.shape[:2]
        rect = (int(width*0.1), int(height*0.1), 
                int(width*0.8), int(height*0.8))
        
        # Apply GrabCut
        cv2.grabCut(img_copy, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        
        # Create mask where 0 and 2 are background, 1 and 3 are foreground
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        
        # Apply mask to image
        result = img_copy * mask2[:, :, np.newaxis]
        
        # Add alpha channel for transparency
        bgra = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = mask2 * 255
        return bgra
    
    def style_transfer(self, image: np.ndarray, style: str) -> np.ndarray:
        """Apply artistic style transfer using OpenCV filters"""
        # Generate cache key
        image_id = id(image)
        cache_key = f"style_{image_id}_{style}"
        
        # Check cache
        cached = self.cache.get_processed(image_id, 'style', {'style': style})
        if cached is not None:
            return cached
        
        try:
            image = self._validate_and_prepare_image(image)
            
            styles = {
                'cartoon': self._cartoon_style,
                'pencil_sketch': self._pencil_style,
                'oil_painting': self._oil_painting_style,
                'watercolor': self._watercolor_style,
                'comic': self._comic_style,
                'vintage': self._vintage_style
            }
            
            style_key = style.lower().replace(' ', '_')
            if style_key in styles:
                result = styles[style_key](image)
                # Cache result
                self.cache.cache_processed(image_id, 'style', {'style': style}, result)
                return result
            return image
            
        except Exception as e:
            raise RuntimeError(f"Style transfer failed: {str(e)}")

        
    def enhance_facial_features(self, image: np.ndarray) -> np.ndarray:
        """Enhance facial features using advanced filters"""
        try:
            image = self._validate_and_prepare_image(image)
            
            # Load face cascade
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            result = image.copy()
            
            for (x, y, w, h) in faces:
                # Extract face region
                face_roi = result[y:y+h, x:x+w]
                
                # Apply bilateral filter for skin smoothing
                smoothed = cv2.bilateralFilter(face_roi, 9, 75, 75)
                
                # Enhance contrast in face region
                lab = cv2.cvtColor(smoothed, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                l = clahe.apply(l)
                enhanced_lab = cv2.merge([l, a, b])
                enhanced_face = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
                
                # Apply slight sharpening to eyes (center portion)
                eye_region_y = int(h * 0.3)
                eye_region_h = int(h * 0.3)
                if eye_region_y + eye_region_h <= enhanced_face.shape[0]:
                    eye_region = enhanced_face[eye_region_y:eye_region_y+eye_region_h, :]
                    
                    kernel = np.array([[-1,-1,-1],
                                      [-1, 9,-1],
                                      [-1,-1,-1]])
                    sharpened_eyes = cv2.filter2D(eye_region, -1, kernel)
                    enhanced_face[eye_region_y:eye_region_y+eye_region_h, :] = sharpened_eyes
                
                # Replace face region
                result[y:y+h, x:x+w] = enhanced_face
                
            # Apply overall enhancement
            result = self._auto_white_balance(result)
            result = self._auto_contrast(result)
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Facial enhancement failed: {str(e)}")
        
    def _cartoon_style(self, image: np.ndarray) -> np.ndarray:
        """Apply cartoon effect"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply median blur to reduce noise
        gray = cv2.medianBlur(gray, 5)
        
        # Detect edges using adaptive threshold
        edges = cv2.adaptiveThreshold(gray, 255, 
                                     cv2.ADAPTIVE_THRESH_MEAN_C,
                                     cv2.THRESH_BINARY, 9, 9)
        
        # Apply bilateral filter for color quantization
        color = cv2.bilateralFilter(image, 9, 300, 300)
        
        # Combine edges with color
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        
        return cartoon
        
    def _pencil_style(self, image: np.ndarray) -> np.ndarray:
        """Apply pencil sketch effect"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Invert image
        inverted = cv2.bitwise_not(gray)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
        
        # Invert blurred image
        inverted_blurred = cv2.bitwise_not(blurred)
        
        # Create sketch
        sketch = cv2.divide(gray, inverted_blurred, scale=256.0)
        
        # Convert back to BGR
        return cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
        
    def _oil_painting_style(self, image: np.ndarray) -> np.ndarray:
        """Apply oil painting effect"""
        # Ensure image is 8UC3
        if image.dtype != np.uint8 or len(image.shape) != 3 or image.shape[2] != 3:
            image = self._validate_and_prepare_image(image)
            
        # Apply bilateral filter for stylization
        oil_effect = cv2.bilateralFilter(image, 9, 150, 150)
        
        # Add texture
        kernel = np.ones((2,2), np.uint8)
        oil_effect = cv2.erode(oil_effect, kernel, iterations=1)
        oil_effect = cv2.dilate(oil_effect, kernel, iterations=1)
        
        return oil_effect
        
    def _watercolor_style(self, image: np.ndarray) -> np.ndarray:
        """Apply watercolor effect"""
        # Apply bilateral filter for smoothing
        watercolor = cv2.bilateralFilter(image, 15, 80, 80)
        
        # Apply edge-preserving filter
        watercolor = cv2.edgePreservingFilter(watercolor, flags=1, sigma_s=60, sigma_r=0.4)
        
        return watercolor
        
    def _comic_style(self, image: np.ndarray) -> np.ndarray:
        """Apply comic book effect"""
        # Convert to grayscale and detect edges
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        # Reduce colors
        z = image.reshape((-1,3))
        z = np.float32(z)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        k = 8
        _, label, center = cv2.kmeans(z, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        center = np.uint8(center)
        quantized = center[label.flatten()]
        quantized = quantized.reshape(image.shape)
        
        # Combine with edges
        comic = cv2.addWeighted(quantized, 0.8, edges, 0.2, 0)
        
        return comic
        
    def _vintage_style(self, image: np.ndarray) -> np.ndarray:
        """Apply vintage/sepia effect"""
        # Create sepia kernel
        kernel = np.array([[0.272, 0.534, 0.131],
                          [0.349, 0.686, 0.168],
                          [0.393, 0.769, 0.189]])
        
        # Apply sepia
        sepia = cv2.transform(image, kernel)
        sepia = np.clip(sepia, 0, 255).astype(np.uint8)
        
        # Add vignette effect
        rows, cols = image.shape[:2]
        kernel_x = cv2.getGaussianKernel(cols, cols/3)
        kernel_y = cv2.getGaussianKernel(rows, rows/3)
        kernel = kernel_y * kernel_x.T
        mask = kernel / kernel.max()
        vignette = np.zeros_like(sepia)
        
        for i in range(3):
            vignette[:,:,i] = sepia[:,:,i] * mask
            
        return vignette
        
    def auto_enhance(self, image: np.ndarray) -> np.ndarray:
        """Automatically enhance image using multiple techniques"""
        image_id = id(image)
        cache_key = f"auto_enhance_{image_id}"
        
        # Check cache
        cached = self.cache.get_processed(image_id, 'auto_enhance', {})
        if cached is not None:
            return cached
        try:
            image = self._validate_and_prepare_image(image)
            result = image.copy()
            
            # Auto white balance
            result = self._auto_white_balance(result)
            
            # Auto contrast
            result = self._auto_contrast(result)
            
            # Auto sharpening (if needed)
            if self._is_blurry(result):
                result = self._auto_sharpen(result)
            
            # Auto denoising (if needed)
            if self._has_noise(result):
                result = self.denoise_image(result, 0.05)
            
            # Auto color enhancement
            result = self._enhance_colors(result)
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Auto enhancement failed: {str(e)}")
        
    def _auto_white_balance(self, image: np.ndarray) -> np.ndarray:
        """Simple auto white balance using gray world assumption"""
        result = image.copy().astype(np.float32)
        
        # Calculate mean of each channel
        avg_b = np.mean(result[:, :, 0])
        avg_g = np.mean(result[:, :, 1])
        avg_r = np.mean(result[:, :, 2])
        
        # Calculate scaling factors
        avg_gray = (avg_b + avg_g + avg_r) / 3
        scale_b = avg_gray / avg_b if avg_b > 0 else 1
        scale_g = avg_gray / avg_g if avg_g > 0 else 1
        scale_r = avg_gray / avg_r if avg_r > 0 else 1
        
        # Apply scaling
        result[:, :, 0] = np.clip(result[:, :, 0] * scale_b, 0, 255)
        result[:, :, 1] = np.clip(result[:, :, 1] * scale_g, 0, 255)
        result[:, :, 2] = np.clip(result[:, :, 2] * scale_r, 0, 255)
        
        return result.astype(np.uint8)
        
    def _auto_contrast(self, image: np.ndarray) -> np.ndarray:
        """Auto contrast adjustment using CLAHE"""
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        
        # Merge channels
        enhanced_lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
            
        return enhanced
        
    def _auto_sharpen(self, image: np.ndarray) -> np.ndarray:
        """Auto sharpening using unsharp mask"""
        # Create Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), 3)
        
        # Apply unsharp masking
        sharpened = cv2.addWeighted(image, 1.5, blurred, -0.5, 0)
        
        return sharpened
        
    def _enhance_colors(self, image: np.ndarray) -> np.ndarray:
        """Enhance color saturation and vibrance"""
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # Increase saturation
        s = np.clip(s * 1.2, 0, 255).astype(np.uint8)
        
        # Merge channels
        enhanced_hsv = cv2.merge([h, s, v])
        enhanced = cv2.cvtColor(enhanced_hsv, cv2.COLOR_HSV2BGR)
        
        return enhanced
        
    def _is_blurry(self, image: np.ndarray, threshold: float = 100.0) -> bool:
        """Check if image is blurry using variance of Laplacian"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        return variance < threshold
        
    def _has_noise(self, image: np.ndarray, threshold: float = 0.05) -> bool:
        """Simple noise detection"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate local variance
        mean = cv2.blur(gray, (5, 5))
        variance = cv2.blur(cv2.pow(gray - mean, 2), (5, 5))
        
        # High variance might indicate noise
        noise_level = np.mean(variance) / 255.0
        return noise_level > threshold
        
    def upscale_advanced(self, image: np.ndarray, scale: int = 4) -> np.ndarray:
        """Advanced upscaling using multiple techniques"""
        image = self._validate_and_prepare_image(image)
        current = image.copy()
        
        # Progressive upscaling for better quality
        for _ in range(scale // 2):
            # Double the size
            h, w = current.shape[:2]
            current = cv2.resize(current, (w*2, h*2), interpolation=cv2.INTER_CUBIC)
            
            # Apply edge enhancement
            kernel = np.array([[-0.5,-0.5,-0.5],
                              [-0.5, 5, -0.5],
                              [-0.5,-0.5,-0.5]])
            current = cv2.filter2D(current, -1, kernel)
            
            # Apply slight denoising
            current = cv2.fastNlMeansDenoisingColored(current, None, 3, 3, 7, 21)
            
        return current