import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ExifTags
import cv2
from typing import Tuple, Optional, List, Union
import colorsys
import os

class ImageProcessor:
    """Utility class for image processing operations"""
    
    @staticmethod
    def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format"""
        if pil_image is None:
            raise ValueError("Input PIL image is None")
        try:
            # Convert PIL to numpy array
            np_image = np.array(pil_image)
            
            # Handle different modes
            if len(np_image.shape) == 2:
                # Grayscale
                return cv2.cvtColor(np_image, cv2.COLOR_GRAY2BGR)
            elif np_image.shape[2] == 4:
                # RGBA
                return cv2.cvtColor(np_image, cv2.COLOR_RGBA2BGR)
            elif np_image.shape[2] == 3:
                # RGB
                return cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)
            else:
                raise ValueError(f"Unexpected image shape: {np_image.shape}")
        except Exception as e:
            raise RuntimeError(f"Failed to convert PIL to CV2: {str(e)}")
    
    @staticmethod
    def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
        """Convert OpenCV image to PIL format"""
        if cv2_image is None:
            raise ValueError("Input CV2 image is None")
        try:
            if len(cv2_image.shape) == 2:
                # Grayscale
                return Image.fromarray(cv2_image)
            elif cv2_image.shape[2] == 4:
                # BGRA
                return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGRA2RGBA))
            elif cv2_image.shape[2] == 3:
                # BGR
                return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))
            else:
                raise ValueError(f"Unexpected image shape: {cv2_image.shape}")
        except Exception as e:
            raise RuntimeError(f"Failed to convert CV2 to PIL: {str(e)}")
    
    @staticmethod
    def resize_with_aspect_ratio(image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """Resize image while maintaining aspect ratio"""
        if image is None:
            raise ValueError("Input image is None")
        try:
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
            
            # Ensure dimensions are at least 1
            new_w = max(1, new_w)
            new_h = max(1, new_h)
            
            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        except Exception as e:
            raise RuntimeError(f"Failed to resize image: {str(e)}")
    
    @staticmethod
    def auto_crop(image: np.ndarray, tolerance: int = 10) -> np.ndarray:
        """Auto crop whitespace from image"""
        if image is None:
            raise ValueError("Input image is None")
        try:
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
        except Exception as e:
            raise RuntimeError(f"Failed to auto crop: {str(e)}")
    
    @staticmethod
    def adjust_hsl(image: np.ndarray, hue: float, saturation: float, lightness: float) -> np.ndarray:
        """Adjust HSL values"""
        if image is None:
            raise ValueError("Input image is None")
        try:
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
        except Exception as e:
            raise RuntimeError(f"Failed to adjust HSL: {str(e)}")
    
    @staticmethod
    def create_histogram(image: np.ndarray) -> dict:
        """Create histogram data for image"""
        if image is None:
            raise ValueError("Input image is None")
        try:
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
        except Exception as e:
            raise RuntimeError(f"Failed to create histogram: {str(e)}")
    
    @staticmethod
    def equalize_histogram(image: np.ndarray) -> np.ndarray:
        """Apply histogram equalization"""
        if image is None:
            raise ValueError("Input image is None")
        try:
            if len(image.shape) == 3:
                # Convert to YUV color space
                yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
                # Equalize the Y channel
                yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
                # Convert back to BGR
                return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
            else:
                return cv2.equalizeHist(image)
        except Exception as e:
            raise RuntimeError(f"Failed to equalize histogram: {str(e)}")
    
    @staticmethod
    def apply_gamma_correction(image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
        """Apply gamma correction"""
        if image is None:
            raise ValueError("Input image is None")
        try:
            if gamma <= 0:
                gamma = 1.0
            inv_gamma = 1.0 / gamma
            table = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)]).astype("uint8")
            return cv2.LUT(image, table)
        except Exception as e:
            raise RuntimeError(f"Failed to apply gamma correction: {str(e)}")
    
    @staticmethod
    def create_collage(images: List[np.ndarray], grid_size: Tuple[int, int]) -> Optional[np.ndarray]:
        """Create a collage from multiple images"""
        if not images:
            return None
        try:
            grid_w, grid_h = grid_size
            n_images = len(images)
            
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
        except Exception as e:
            raise RuntimeError(f"Failed to create collage: {str(e)}")
    
    @staticmethod
    def apply_watermark(image: np.ndarray, watermark: np.ndarray, 
                        position: str = 'bottom-right', opacity: float = 0.5) -> np.ndarray:
        """Apply watermark to image"""
        if image is None or watermark is None:
            raise ValueError("Input image or watermark is None")
        try:
            result = image.copy()
            h, w = image.shape[:2]
            wm_h, wm_w = watermark.shape[:2]
            
            # Ensure watermark fits
            if wm_h > h or wm_w > w:
                # Resize watermark to fit
                scale = min(h / wm_h, w / wm_w) * 0.8
                new_w = int(wm_w * scale)
                new_h = int(wm_h * scale)
                watermark = cv2.resize(watermark, (new_w, new_h))
                wm_h, wm_w = new_h, new_w
            
            # Calculate position
            if position == 'top-left':
                pos = (10, 10)
            elif position == 'top-right':
                pos = (w - wm_w - 10, 10)
            elif position == 'bottom-left':
                pos = (10, h - wm_h - 10)
            else:  # bottom-right
                pos = (w - wm_w - 10, h - wm_h - 10)
            
            # Ensure position is valid
            pos_x = max(0, min(pos[0], w - wm_w))
            pos_y = max(0, min(pos[1], h - wm_h))
            
            # Create ROI
            roi = result[pos_y:pos_y + wm_h, pos_x:pos_x + wm_w]
            
            # If watermark has alpha channel, use it for blending
            if len(watermark.shape) == 3 and watermark.shape[2] == 4:
                # Watermark has alpha
                alpha = watermark[:, :, 3] / 255.0 * opacity
                watermark_rgb = watermark[:, :, :3]
                
                for c in range(3):
                    roi[:, :, c] = (roi[:, :, c] * (1 - alpha) + 
                                    watermark_rgb[:, :, c] * alpha).astype(np.uint8)
            else:
                # No alpha, use simple blending
                blended = cv2.addWeighted(roi, 1 - opacity, watermark, opacity, 0)
                result[pos_y:pos_y + wm_h, pos_x:pos_x + wm_w] = blended
            
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to apply watermark: {str(e)}")
    
    @staticmethod
    def detect_edges(image: np.ndarray, method: str = 'canny') -> np.ndarray:
        """Detect edges in image"""
        if image is None:
            raise ValueError("Input image is None")
        try:
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
            elif method == 'scharr':
                grad_x = cv2.Scharr(gray, cv2.CV_64F, 1, 0)
                grad_y = cv2.Scharr(gray, cv2.CV_64F, 0, 1)
                edges = np.sqrt(grad_x**2 + grad_y**2)
                edges = np.uint8(np.clip(edges, 0, 255))
            else:
                edges = gray
                
            return edges
        except Exception as e:
            raise RuntimeError(f"Failed to detect edges: {str(e)}")
    
    @staticmethod
    def get_image_metadata(image_path: str) -> dict:
        """Extract metadata from image"""
        metadata = {}
        
        try:
            if not os.path.exists(image_path):
                metadata['error'] = f"File not found: {image_path}"
                return metadata
                
            img = Image.open(image_path)
            
            # Basic info
            metadata['format'] = img.format
            metadata['mode'] = img.mode
            metadata['size'] = img.size
            metadata['width'], metadata['height'] = img.size
            metadata['filename'] = os.path.basename(image_path)
            metadata['filesize'] = os.path.getsize(image_path)
            
            # EXIF data
            try:
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        metadata[tag] = str(value)
            except:
                pass
                
        except Exception as e:
            metadata['error'] = str(e)
            
        return metadata
    
    @staticmethod
    def compress_image(image: np.ndarray, quality: int = 85) -> bytes:
        """Compress image to JPEG format"""
        if image is None:
            raise ValueError("Input image is None")
        try:
            quality = max(1, min(100, quality))
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            _, enc_img = cv2.imencode('.jpg', image, encode_param)
            return enc_img.tobytes()
        except Exception as e:
            raise RuntimeError(f"Failed to compress image: {str(e)}")
    
    @staticmethod
    def create_thumbnail(image: np.ndarray, size: Tuple[int, int] = (128, 128)) -> np.ndarray:
        """Create thumbnail from image"""
        if image is None:
            raise ValueError("Input image is None")
        try:
            # Ensure size is positive
            w = max(1, size[0])
            h = max(1, size[1])
            return cv2.resize(image, (w, h), interpolation=cv2.INTER_AREA)
        except Exception as e:
            raise RuntimeError(f"Failed to create thumbnail: {str(e)}")
    
    @staticmethod
    def blend_images(image1: np.ndarray, image2: np.ndarray, 
                     alpha: float = 0.5, beta: float = 0.5) -> np.ndarray:
        """Blend two images together"""
        if image1 is None or image2 is None:
            raise ValueError("Input images cannot be None")
        try:
            # Resize second image to match first if needed
            if image1.shape != image2.shape:
                image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
            
            # Ensure same number of channels
            if len(image1.shape) != len(image2.shape):
                if len(image1.shape) == 3 and len(image2.shape) == 2:
                    image2 = cv2.cvtColor(image2, cv2.COLOR_GRAY2BGR)
                elif len(image1.shape) == 2 and len(image2.shape) == 3:
                    image1 = cv2.cvtColor(image1, cv2.COLOR_GRAY2BGR)
            
            return cv2.addWeighted(image1, alpha, image2, beta, 0)
        except Exception as e:
            raise RuntimeError(f"Failed to blend images: {str(e)}")
    
    @staticmethod
    def apply_gradient_map(image: np.ndarray, gradient_colors: List[Tuple[int, int, int]]) -> np.ndarray:
        """Apply gradient map to image"""
        if image is None:
            raise ValueError("Input image is None")
        if not gradient_colors or len(gradient_colors) < 2:
            raise ValueError("Need at least 2 gradient colors")
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
                
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
        except Exception as e:
            raise RuntimeError(f"Failed to apply gradient map: {str(e)}")
    
    @staticmethod
    def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by given angle"""
        if image is None:
            raise ValueError("Input image is None")
        try:
            h, w = image.shape[:2]
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, matrix, (w, h), 
                                     flags=cv2.INTER_LANCZOS4,
                                     borderMode=cv2.BORDER_REPLICATE)
            return rotated
        except Exception as e:
            raise RuntimeError(f"Failed to rotate image: {str(e)}")
    
    @staticmethod
    def flip_image(image: np.ndarray, direction: str = 'horizontal') -> np.ndarray:
        """Flip image horizontally or vertically"""
        if image is None:
            raise ValueError("Input image is None")
        try:
            if direction == 'horizontal':
                return cv2.flip(image, 1)
            elif direction == 'vertical':
                return cv2.flip(image, 0)
            else:
                return image
        except Exception as e:
            raise RuntimeError(f"Failed to flip image: {str(e)}")