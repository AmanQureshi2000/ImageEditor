import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import cv2
from typing import Tuple, Optional, List
import colorsys

class ImageProcessor:
    """Utility class for image processing operations"""
    
    @staticmethod
    def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format"""
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
        """Convert OpenCV image to PIL format"""
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))
    
    @staticmethod
    def resize_with_aspect_ratio(image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """Resize image while maintaining aspect ratio"""
        h, w = image.shape[:2]
        target_w, target_h = target_size
        
        # Calculate aspect ratios
        aspect_ratio = w / h
        target_aspect = target_w / target_h
        
        if aspect_ratio > target_aspect:
            # Width is the limiting factor
            new_w = target_w
            new_h = int(target_w / aspect_ratio)
        else:
            # Height is the limiting factor
            new_h = target_h
            new_w = int(target_h * aspect_ratio)
            
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    @staticmethod
    def auto_crop(image: np.ndarray, tolerance: int = 10) -> np.ndarray:
        """Auto crop whitespace from image"""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Find non-white/transparent areas
        mask = gray < 255 - tolerance
        
        # Find coordinates of non-white areas
        coords = np.argwhere(mask)
        if len(coords) == 0:
            return image
            
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0) + 1
        
        # Crop image
        return image[y_min:y_max, x_min:x_max]
    
    @staticmethod
    def adjust_hsl(image: np.ndarray, hue: float, saturation: float, lightness: float) -> np.ndarray:
        """Adjust HSL values"""
        # Convert to float and normalize
        img_float = image.astype(np.float32) / 255.0
        
        # Convert RGB to HLS
        hls_img = cv2.cvtColor(img_float, cv2.COLOR_BGR2HLS)
        
        # Adjust channels
        hls_img[:, :, 0] = (hls_img[:, :, 0] + hue / 360.0) % 1.0  # Hue
        hls_img[:, :, 1] = np.clip(hls_img[:, :, 1] * (1.0 + lightness / 100.0), 0, 1)  # Lightness
        hls_img[:, :, 2] = np.clip(hls_img[:, :, 2] * (1.0 + saturation / 100.0), 0, 1)  # Saturation
        
        # Convert back to RGB
        result = cv2.cvtColor(hls_img, cv2.COLOR_HLS2BGR)
        return (result * 255).astype(np.uint8)
    
    @staticmethod
    def create_histogram(image: np.ndarray) -> dict:
        """Create histogram data for image"""
        hist_data = {}
        
        if len(image.shape) == 3:
            colors = ('b', 'g', 'r')
            for i, color in enumerate(colors):
                hist = cv2.calcHist([image], [i], None, [256], [0, 256])
                hist_data[color] = hist.flatten()
        else:
            hist = cv2.calcHist([image], [0], None, [256], [0, 256])
            hist_data['gray'] = hist.flatten()
            
        return hist_data
    
    @staticmethod
    def equalize_histogram(image: np.ndarray) -> np.ndarray:
        """Apply histogram equalization"""
        if len(image.shape) == 3:
            # Convert to YUV color space
            yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            # Equalize the Y channel
            yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
            # Convert back to BGR
            return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        else:
            return cv2.equalizeHist(image)
    
    @staticmethod
    def apply_gamma_correction(image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
        """Apply gamma correction"""
        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)]).astype("uint8")
        return cv2.LUT(image, table)
    
    @staticmethod
    def create_collage(images: List[np.ndarray], grid_size: Tuple[int, int]) -> np.ndarray:
        """Create a collage from multiple images"""
        grid_w, grid_h = grid_size
        n_images = len(images)
        
        if n_images == 0:
            return None
            
        # Calculate collage dimensions
        cell_w = max(img.shape[1] for img in images)
        cell_h = max(img.shape[0] for img in images)
        
        collage_w = cell_w * grid_w
        collage_h = cell_h * grid_h
        
        # Create blank canvas
        collage = np.zeros((collage_h, collage_w, 3), dtype=np.uint8)
        
        # Place images
        for idx, img in enumerate(images):
            if idx >= grid_w * grid_h:
                break
                
            row = idx // grid_w
            col = idx % grid_w
            
            # Resize image to fit cell
            img_resized = cv2.resize(img, (cell_w, cell_h))
            
            # Place in collage
            y_start = row * cell_h
            y_end = y_start + cell_h
            x_start = col * cell_w
            x_end = x_start + cell_w
            
            collage[y_start:y_end, x_start:x_end] = img_resized
            
        return collage
    
    @staticmethod
    def apply_watermark(image: np.ndarray, watermark: np.ndarray, 
                        position: str = 'bottom-right', opacity: float = 0.5) -> np.ndarray:
        """Apply watermark to image"""
        result = image.copy()
        h, w = image.shape[:2]
        wm_h, wm_w = watermark.shape[:2]
        
        # Calculate position
        if position == 'top-left':
            pos = (10, 10)
        elif position == 'top-right':
            pos = (w - wm_w - 10, 10)
        elif position == 'bottom-left':
            pos = (10, h - wm_h - 10)
        else:  # bottom-right
            pos = (w - wm_w - 10, h - wm_h - 10)
            
        # Create ROI
        roi = result[pos[1]:pos[1] + wm_h, pos[0]:pos[0] + wm_w]
        
        # Blend watermark
        blended = cv2.addWeighted(roi, 1 - opacity, watermark, opacity, 0)
        result[pos[1]:pos[1] + wm_h, pos[0]:pos[0] + wm_w] = blended
        
        return result
    
    @staticmethod
    def detect_edges(image: np.ndarray, method: str = 'canny') -> np.ndarray:
        """Detect edges in image"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        if method == 'canny':
            edges = cv2.Canny(gray, 50, 150)
        elif method == 'sobel':
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            edges = np.sqrt(grad_x**2 + grad_y**2)
            edges = np.uint8(np.clip(edges, 0, 255))
        elif method == 'laplacian':
            edges = cv2.Laplacian(gray, cv2.CV_64F)
            edges = np.uint8(np.clip(edges, 0, 255))
        else:
            edges = gray
            
        return edges
    
    @staticmethod
    def get_image_metadata(image_path: str) -> dict:
        """Extract metadata from image"""
        metadata = {}
        
        try:
            from PIL import Image, ExifTags
            
            img = Image.open(image_path)
            
            # Basic info
            metadata['format'] = img.format
            metadata['mode'] = img.mode
            metadata['size'] = img.size
            metadata['width'], metadata['height'] = img.size
            
            # EXIF data
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    metadata[tag] = str(value)
                    
        except Exception as e:
            metadata['error'] = str(e)
            
        return metadata
    
    @staticmethod
    def compress_image(image: np.ndarray, quality: int = 85) -> bytes:
        """Compress image to JPEG format"""
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, enc_img = cv2.imencode('.jpg', image, encode_param)
        return enc_img.tobytes()
    
    @staticmethod
    def create_thumbnail(image: np.ndarray, size: Tuple[int, int] = (128, 128)) -> np.ndarray:
        """Create thumbnail from image"""
        return cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    
    @staticmethod
    def blend_images(image1: np.ndarray, image2: np.ndarray, 
                     alpha: float = 0.5, beta: float = 0.5) -> np.ndarray:
        """Blend two images together"""
        # Resize second image to match first if needed
        if image1.shape != image2.shape:
            image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
            
        return cv2.addWeighted(image1, alpha, image2, beta, 0)
    
    @staticmethod
    def apply_gradient_map(image: np.ndarray, gradient_colors: List[Tuple[int, int, int]]) -> np.ndarray:
        """Apply gradient map to image"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Normalize gray values
        normalized = gray.astype(np.float32) / 255.0
        
        # Create gradient lookup table
        gradient = np.zeros((256, 1, 3), dtype=np.uint8)
        n_colors = len(gradient_colors)
        
        for i in range(256):
            pos = i / 255.0 * (n_colors - 1)
            idx1 = int(pos)
            idx2 = min(idx1 + 1, n_colors - 1)
            frac = pos - idx1
            
            # Interpolate between colors
            color = [
                int((1 - frac) * gradient_colors[idx1][c] + frac * gradient_colors[idx2][c])
                for c in range(3)
            ]
            gradient[i] = color
            
        # Apply gradient map
        return cv2.LUT(gray, gradient)