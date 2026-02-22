import time
from collections import OrderedDict
import threading
import numpy as np
from PIL import Image
import io

class CacheManager:
    """Thread-safe cache manager for image processing"""
    
    def __init__(self, max_size_mb=500, max_items=50):
        self.cache = OrderedDict()
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.max_items = max_items
        self.current_size = 0
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
    def get(self, key):
        """Get item from cache"""
        with self.lock:
            if key in self.cache:
                # Move to end (LRU)
                item = self.cache.pop(key)
                self.cache[key] = item
                item['last_accessed'] = time.time()
                self.hits += 1
                return item['data']
            self.misses += 1
            return None
    
    def put(self, key, data, metadata=None):
        """Put item in cache"""
        with self.lock:
            # Calculate size
            if isinstance(data, np.ndarray):
                size = data.nbytes
            elif isinstance(data, Image.Image):
                # Estimate PIL image size
                size = data.width * data.height * len(data.getbands())
            elif isinstance(data, bytes):
                size = len(data)
            else:
                size = 1024 * 1024  # Default 1MB estimate
            
            # Check if item is too large for cache
            if size > self.max_size * 0.5:  # Don't cache items > 50% of cache size
                return
            
            # Ensure space
            while self.current_size + size > self.max_size or len(self.cache) >= self.max_items:
                self._evict_oldest()
            
            # Add to cache
            self.cache[key] = {
                'data': data,
                'size': size,
                'metadata': metadata or {},
                'created': time.time(),
                'last_accessed': time.time()
            }
            self.current_size += size
    
    def _evict_oldest(self):
        """Evict oldest item from cache"""
        if not self.cache:
            return
        
        # Remove first item (oldest)
        key, item = self.cache.popitem(last=False)
        self.current_size -= item['size']
        self.evictions += 1
        
        # Cleanup if possible
        if isinstance(item['data'], np.ndarray):
            del item['data']
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
            self.current_size = 0
    
    def invalidate(self, key_pattern=None):
        """Invalidate cache entries matching pattern"""
        with self.lock:
            if key_pattern is None:
                self.clear()
                return
            
            keys_to_delete = [k for k in self.cache.keys() if key_pattern in k]
            for key in keys_to_delete:
                self.current_size -= self.cache[key]['size']
                del self.cache[key]
    
    def get_stats(self):
        """Get cache statistics"""
        with self.lock:
            return {
                'size_mb': self.current_size / (1024 * 1024),
                'items': len(self.cache),
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'hit_ratio': self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
            }

class ImageCache:
    """Specialized cache for image thumbnails and processed images"""
    
    def __init__(self):
        self.thumbnail_cache = CacheManager(max_size_mb=100, max_items=200)
        self.processed_cache = CacheManager(max_size_mb=300, max_items=30)
        self.history_cache = CacheManager(max_size_mb=50, max_items=50)
    
    def get_thumbnail(self, image_id, size):
        """Get cached thumbnail"""
        key = f"thumb_{image_id}_{size[0]}x{size[1]}"
        return self.thumbnail_cache.get(key)
    
    def cache_thumbnail(self, image_id, thumbnail, size):
        """Cache thumbnail"""
        key = f"thumb_{image_id}_{size[0]}x{size[1]}"
        self.thumbnail_cache.put(key, thumbnail, {'size': size})
    
    def get_processed(self, image_id, operation, params):
        """Get cached processed image"""
        param_str = '_'.join([f"{k}_{v}" for k, v in sorted(params.items())])
        key = f"proc_{image_id}_{operation}_{param_str}"
        return self.processed_cache.get(key)
    
    def cache_processed(self, image_id, operation, params, result):
        """Cache processed image"""
        param_str = '_'.join([f"{k}_{v}" for k, v in sorted(params.items())])
        key = f"proc_{image_id}_{operation}_{param_str}"
        self.processed_cache.put(key, result, {'operation': operation, 'params': params})
    
    def invalidate_for_image(self, image_id):
        """Invalidate all caches for a specific image"""
        self.thumbnail_cache.invalidate(image_id)
        self.processed_cache.invalidate(image_id)
        self.history_cache.invalidate(image_id)