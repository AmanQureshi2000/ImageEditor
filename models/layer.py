from PIL import Image, ImageEnhance
import numpy as np

class Layer:
    """Layer class for image composition"""
    
    BLEND_MODES = [
        'normal', 'multiply', 'screen', 'overlay',
        'darken', 'lighten', 'difference', 'exclusion',
        'soft_light', 'hard_light'
    ]
    
    def __init__(self, image: Image.Image, name: str = "Layer", opacity: float = 1.0, visible: bool = True):
        self.image = image.copy()
        self.name = name
        self.opacity = max(0.0, min(1.0, opacity))
        self.visible = visible
        self.blend_mode = 'normal'
        self.locked = False
        self.thumbnail = self._create_thumbnail()
        
    def _create_thumbnail(self, size=(64, 64)):
        """Create thumbnail for layer preview"""
        if self.image:
            thumb = self.image.copy()
            thumb.thumbnail(size, Image.Resampling.LANCZOS)
            return thumb
        return None
    
    def set_blend_mode(self, mode: str):
        """Set blend mode for layer"""
        if mode in self.BLEND_MODES:
            self.blend_mode = mode
    
    def apply_opacity(self, image: Image.Image) -> Image.Image:
        """Apply opacity to image"""
        if self.opacity >= 1.0:
            return image
        
        if image.mode == 'RGBA':
            # Adjust alpha channel
            r, g, b, a = image.split()
            a = a.point(lambda p: int(p * self.opacity))
            return Image.merge('RGBA', (r, g, b, a))
        else:
            # Convert to RGBA and adjust alpha
            rgba = image.convert('RGBA')
            r, g, b, a = rgba.split()
            a = a.point(lambda p: int(p * self.opacity))
            return Image.merge('RGBA', (r, g, b, a))
    
    def duplicate(self) -> 'Layer':
        """Create a duplicate of this layer"""
        new_layer = Layer(
            self.image.copy(),
            f"{self.name} copy",
            self.opacity,
            self.visible
        )
        new_layer.blend_mode = self.blend_mode
        return new_layer

class LayerManager:
    """Manager for layer operations"""
    
    def __init__(self):
        self.layers = []
        self.active_layer_index = -1
        self.width = 0
        self.height = 0
        
    def add_layer(self, layer: Layer, position: int = -1):
        """Add a new layer"""
        if position < 0 or position >= len(self.layers):
            self.layers.append(layer)
            self.active_layer_index = len(self.layers) - 1
        else:
            self.layers.insert(position, layer)
            self.active_layer_index = position
        
        # Update canvas size
        self._update_canvas_size()
    
    def remove_layer(self, index: int):
        """Remove a layer"""
        if 0 <= index < len(self.layers):
            del self.layers[index]
            if self.active_layer_index >= len(self.layers):
                self.active_layer_index = len(self.layers) - 1
            self._update_canvas_size()
    
    def move_layer(self, from_index: int, to_index: int):
        """Move layer to new position"""
        if 0 <= from_index < len(self.layers) and 0 <= to_index < len(self.layers):
            layer = self.layers.pop(from_index)
            self.layers.insert(to_index, layer)
            self.active_layer_index = to_index
    
    def duplicate_layer(self, index: int):
        """Duplicate a layer"""
        if 0 <= index < len(self.layers):
            new_layer = self.layers[index].duplicate()
            self.add_layer(new_layer, index + 1)
    
    def merge_layers(self, indices: list) -> Layer:
        """Merge multiple layers into one"""
        if len(indices) < 2:
            return None
        
        # Sort indices in reverse order
        indices.sort(reverse=True)
        
        # Get the bottom layer as base
        base_index = indices[-1]
        base_layer = self.layers[base_index]
        
        # Composite all layers onto base
        result_image = base_layer.image.copy()
        
        for idx in indices[:-1]:  # Skip the base
            layer = self.layers[idx]
            if layer.visible:
                result_image = self._blend_images(
                    result_image,
                    layer.image,
                    layer.blend_mode,
                    layer.opacity
                )
        
        # Create merged layer
        merged_layer = Layer(result_image, "Merged Layer")
        
        # Remove merged layers
        for idx in indices:
            self.remove_layer(idx)
        
        return merged_layer
    
    def flatten(self) -> Image.Image:
        """Flatten all visible layers into one image"""
        if not self.layers:
            return None
        
        # Start with bottom layer
        result = self.layers[0].image.copy()
        
        # Composite all layers
        for layer in self.layers[1:]:
            if layer.visible:
                result = self._blend_images(
                    result,
                    layer.image,
                    layer.blend_mode,
                    layer.opacity
                )
        
        return result
    
    def _blend_images(self, bottom: Image.Image, top: Image.Image, 
                      mode: str, opacity: float) -> Image.Image:
        """Blend two images with specified mode"""
        # Ensure both images are the same size
        if bottom.size != top.size:
            top = top.resize(bottom.size, Image.Resampling.LANCZOS)
        
        # Convert to numpy for blending
        bottom_np = np.array(bottom).astype(np.float32)
        top_np = np.array(top).astype(np.float32)
        
        # Apply blend mode
        if mode == 'normal':
            result = bottom_np * (1 - opacity) + top_np * opacity
        elif mode == 'multiply':
            result = bottom_np * top_np / 255.0
            result = bottom_np * (1 - opacity) + result * opacity
        elif mode == 'screen':
            result = 255 - (255 - bottom_np) * (255 - top_np) / 255.0
            result = bottom_np * (1 - opacity) + result * opacity
        elif mode == 'overlay':
            mask = bottom_np < 128
            result = np.where(mask, 
                            2 * bottom_np * top_np / 255.0,
                            255 - 2 * (255 - bottom_np) * (255 - top_np) / 255.0)
            result = bottom_np * (1 - opacity) + result * opacity
        elif mode == 'darken':
            result = np.minimum(bottom_np, top_np)
            result = bottom_np * (1 - opacity) + result * opacity
        elif mode == 'lighten':
            result = np.maximum(bottom_np, top_np)
            result = bottom_np * (1 - opacity) + result * opacity
        elif mode == 'difference':
            result = np.abs(bottom_np - top_np)
            result = bottom_np * (1 - opacity) + result * opacity
        else:
            result = bottom_np * (1 - opacity) + top_np * opacity
        
        return Image.fromarray(result.astype(np.uint8))
    
    def _update_canvas_size(self):
        """Update canvas size based on layers"""
        max_width = 0
        max_height = 0
        
        for layer in self.layers:
            if layer.image:
                max_width = max(max_width, layer.image.width)
                max_height = max(max_height, layer.image.height)
        
        self.width = max_width
        self.height = max_height
    
    def get_active_layer(self) -> Layer:
        """Get the currently active layer"""
        if 0 <= self.active_layer_index < len(self.layers):
            return self.layers[self.active_layer_index]
        return None
    
    def set_active_layer(self, index: int):
        """Set the active layer"""
        if 0 <= index < len(self.layers):
            self.active_layer_index = index
    
    def get_layer_count(self) -> int:
        """Get number of layers"""
        return len(self.layers)