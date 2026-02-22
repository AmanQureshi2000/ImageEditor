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
            elif self.active_layer_index > index:
                self.active_layer_index -= 1
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
        
        # Sort indices in ascending order for processing
        indices.sort()
        
        # Get the bottom layer as base (lowest index)
        base_index = indices[0]
        base_layer = self.layers[base_index]
        
        # Start with base layer image
        result_image = base_layer.image.copy()
        
        # Composite all layers above the base (excluding the base itself)
        for idx in indices[1:]:
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
        
        # Remove merged layers (from highest to lowest to avoid index shift)
        for idx in sorted(indices, reverse=True):
            self.remove_layer(idx)
        
        # Insert the merged layer at the position of the bottom-most merged layer
        insert_pos = min(base_index, len(self.layers))
        self.layers.insert(insert_pos, merged_layer)
        self.active_layer_index = insert_pos
        
        # Update canvas size
        self._update_canvas_size()
        
        return merged_layer
    
    def flatten(self) -> Image.Image:
        """Flatten all visible layers into one image"""
        if not self.layers:
            return None
        
        # Get canvas size from the largest layer or use first layer's size
        w, h = self.width, self.height
        if w <= 0 or h <= 0:
            # Find max dimensions from all layers
            w = max((layer.image.width for layer in self.layers), default=0)
            h = max((layer.image.height for layer in self.layers), default=0)
        
        if w <= 0 or h <= 0:
            return None
        
        # Start with transparent background
        result = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        
        # Composite all visible layers (bottom to top)
        for layer in self.layers:
            if layer.visible:
                # Ensure image is RGBA
                top_img = layer.image
                if top_img.mode != 'RGBA':
                    top_img = top_img.convert('RGBA')
                
                # Create a canvas-sized version of the layer image
                layer_canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                # Paste the layer image at the top-left corner (assuming same coordinate system)
                layer_canvas.paste(top_img, (0, 0))
                
                result = self._blend_images(
                    result,
                    layer_canvas,
                    layer.blend_mode,
                    layer.opacity
                )
        
        return result
    
    def _blend_images(self, bottom: Image.Image, top: Image.Image, 
                      mode: str, opacity: float) -> Image.Image:
        """Blend two images with specified mode"""
        # Ensure both images are RGBA for consistent processing
        if bottom.mode != 'RGBA':
            bottom = bottom.convert('RGBA')
        if top.mode != 'RGBA':
            top = top.convert('RGBA')
        
        # Ensure both images are the same size
        if bottom.size != top.size:
            top = top.resize(bottom.size, Image.Resampling.LANCZOS)
        
        # Convert to numpy for blending (0-255 range)
        bottom_np = np.array(bottom).astype(np.float32)
        top_np = np.array(top).astype(np.float32)
        
        # Get alpha channels
        bottom_alpha = bottom_np[:, :, 3:4] / 255.0 if bottom_np.shape[2] == 4 else np.ones((bottom_np.shape[0], bottom_np.shape[1], 1))
        top_alpha = top_np[:, :, 3:4] / 255.0 if top_np.shape[2] == 4 else np.ones((top_np.shape[0], top_np.shape[1], 1))
        
        # Apply layer opacity to top alpha
        top_alpha = top_alpha * opacity
        
        # Extract RGB channels
        bottom_rgb = bottom_np[:, :, :3]
        top_rgb = top_np[:, :, :3]
        
        # Apply blend mode to RGB channels
        if mode == 'normal':
            blended_rgb = top_rgb
        elif mode == 'multiply':
            blended_rgb = bottom_rgb * top_rgb / 255.0
        elif mode == 'screen':
            blended_rgb = 255 - (255 - bottom_rgb) * (255 - top_rgb) / 255.0
        elif mode == 'overlay':
            mask = bottom_rgb < 128
            blended_rgb = np.where(mask, 
                                  2 * bottom_rgb * top_rgb / 255.0,
                                  255 - 2 * (255 - bottom_rgb) * (255 - top_rgb) / 255.0)
        elif mode == 'darken':
            blended_rgb = np.minimum(bottom_rgb, top_rgb)
        elif mode == 'lighten':
            blended_rgb = np.maximum(bottom_rgb, top_rgb)
        elif mode == 'difference':
            blended_rgb = np.abs(bottom_rgb - top_rgb)
        elif mode == 'exclusion':
            blended_rgb = bottom_rgb + top_rgb - 2 * bottom_rgb * top_rgb / 255.0
        elif mode == 'soft_light':
            blended_rgb = 255 - (255 - bottom_rgb) * (255 - (top_rgb / 255.0)) / 255.0
        elif mode == 'hard_light':
            mask = top_rgb < 128
            blended_rgb = np.where(mask,
                                  2 * bottom_rgb * top_rgb / 255.0,
                                  255 - 2 * (255 - bottom_rgb) * (255 - top_rgb) / 255.0)
        else:
            blended_rgb = top_rgb
        
        # Composite using alpha compositing formula: result = bottom * (1 - top_alpha) + blended * top_alpha
        # Expand dimensions for broadcasting
        top_alpha_expanded = np.repeat(top_alpha, 3, axis=2)
        
        # Composite
        result_rgb = bottom_rgb * (1 - top_alpha_expanded) + blended_rgb * top_alpha_expanded
        
        # Calculate result alpha (union of alphas)
        result_alpha = bottom_alpha + top_alpha * (1 - bottom_alpha)
        result_alpha = np.clip(result_alpha * 255, 0, 255).astype(np.uint8)
        
        # Combine RGB and alpha
        result = np.dstack((result_rgb.astype(np.uint8), result_alpha))
        
        return Image.fromarray(result, 'RGBA')
    
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
    
    def get_layer_names(self) -> list:
        """Get list of layer names"""
        return [layer.name for layer in self.layers]
    
    def get_layer_thumbnails(self) -> list:
        """Get list of layer thumbnails"""
        return [layer.thumbnail for layer in self.layers if layer.thumbnail]
    
    def get_layer_opacities(self) -> list:
        """Get list of layer opacities"""
        return [layer.opacity for layer in self.layers]
    
    def get_layer_visibilities(self) -> list:
        """Get list of layer visibilities"""
        return [layer.visible for layer in self.layers]
    
    def get_layer_blend_modes(self) -> list:
        """Get list of layer blend modes"""
        return [layer.blend_mode for layer in self.layers]