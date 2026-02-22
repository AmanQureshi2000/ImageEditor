import time
from collections import OrderedDict
import threading
import numpy as np
from PIL import Image
import io
import hashlib
import pickle

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
                try:
                    size = data.width * data.height * len(data.getbands())
                except:
                    size = 1024 * 1024  # Default fallback
            elif isinstance(data, bytes):
                size = len(data)
            elif isinstance(data, (dict, list, tuple)):
                # For serializable objects, estimate pickle size
                try:
                    size = len(pickle.dumps(data))
                except:
                    size = 1024 * 1024
            else:
                size = 1024 * 1024  # Default 1MB estimate
            
            # Check if item is too large for cache
            if size > self.max_size * 0.5:  # Don't cache items > 50% of cache size
                return
            
            # Ensure space
            while (self.current_size + size > self.max_size or 
                   len(self.cache) >= self.max_items) and self.cache:
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
        elif isinstance(item['data'], Image.Image):
            item['data'].close() if hasattr(item['data'], 'close') else None
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            # Clean up resources
            for item in self.cache.values():
                if isinstance(item['data'], Image.Image):
                    try:
                        item['data'].close() if hasattr(item['data'], 'close') else None
                    except:
                        pass
                elif isinstance(item['data'], np.ndarray):
                    del item['data']
            
            self.cache.clear()
            self.current_size = 0
    
    def invalidate(self, key_pattern=None):
        """Invalidate cache entries matching pattern"""
        with self.lock:
            if key_pattern is None:
                self.clear()
                return
            
            # Handle string pattern matching
            if isinstance(key_pattern, str):
                keys_to_delete = [k for k in self.cache.keys() if key_pattern in str(k)]
            else:
                # Assume key_pattern is a callable predicate
                keys_to_delete = [k for k in self.cache.keys() if key_pattern(k)]
            
            for key in keys_to_delete:
                self.current_size -= self.cache[key]['size']
                # Clean up resources
                if isinstance(self.cache[key]['data'], Image.Image):
                    try:
                        self.cache[key]['data'].close() if hasattr(self.cache[key]['data'], 'close') else None
                    except:
                        pass
                del self.cache[key]
    
    def get_stats(self):
        """Get cache statistics"""
        with self.lock:
            hits = self.hits
            misses = self.misses
            return {
                'size_mb': self.current_size / (1024 * 1024),
                'items': len(self.cache),
                'hits': hits,
                'misses': misses,
                'evictions': self.evictions,
                'hit_ratio': hits / (hits + misses) if (hits + misses) > 0 else 0
            }
    
    def contains(self, key):
        """Check if key exists in cache"""
        with self.lock:
            return key in self.cache
    
    def get_keys(self):
        """Get all cache keys"""
        with self.lock:
            return list(self.cache.keys())

class ImageCache:
    """Specialized cache for image thumbnails and processed images"""
    
    def __init__(self):
        self.thumbnail_cache = CacheManager(max_size_mb=100, max_items=200)
        self.processed_cache = CacheManager(max_size_mb=300, max_items=30)
        self.history_cache = CacheManager(max_size_mb=50, max_items=50)
        
    def _generate_image_id(self, image):
        """Generate a stable ID for an image"""
        if image is None:
            return "none"
        
        try:
            if isinstance(image, Image.Image):
                # Use hash of image data for PIL images
                img_bytes = image.tobytes()
                return hashlib.md5(img_bytes).hexdigest()[:16]
            elif isinstance(image, np.ndarray):
                # Use hash of array data for numpy arrays
                return hashlib.md5(image.tobytes()).hexdigest()[:16]
            else:
                return str(id(image))  # Fallback to object id
        except:
            return str(id(image))  # Fallback on error
    
    def get_thumbnail(self, image, size):
        """Get cached thumbnail"""
        image_id = self._generate_image_id(image)
        key = f"thumb_{image_id}_{size[0]}x{size[1]}"
        return self.thumbnail_cache.get(key)
    
    def cache_thumbnail(self, image, thumbnail, size):
        """Cache thumbnail"""
        if image is None or thumbnail is None:
            return
        image_id = self._generate_image_id(image)
        key = f"thumb_{image_id}_{size[0]}x{size[1]}"
        self.thumbnail_cache.put(key, thumbnail, {'size': size, 'original_id': image_id})
    
    def get_processed(self, image, operation, params):
        """Get cached processed image"""
        if image is None:
            return None
        image_id = self._generate_image_id(image)
        
        # Create a stable parameter string
        try:
            # Sort params to ensure consistent keys
            sorted_params = sorted(params.items()) if params else []
            param_str = '_'.join([f"{k}_{v}" for k, v in sorted_params])
        except:
            param_str = str(params) if params else ""
        
        key = f"proc_{image_id}_{operation}_{param_str}"
        return self.processed_cache.get(key)
    
    def cache_processed(self, image, operation, params, result):
        """Cache processed image"""
        if image is None or result is None:
            return
        image_id = self._generate_image_id(image)
        
        # Create a stable parameter string
        try:
            sorted_params = sorted(params.items()) if params else []
            param_str = '_'.join([f"{k}_{v}" for k, v in sorted_params])
        except:
            param_str = str(params) if params else ""
        
        key = f"proc_{image_id}_{operation}_{param_str}"
        self.processed_cache.put(key, result, {
            'operation': operation, 
            'params': params,
            'original_id': image_id
        })
    
    def get_history_item(self, history_id):
        """Get cached history item"""
        key = f"hist_{history_id}"
        return self.history_cache.get(key)
    
    def cache_history_item(self, history_id, item):
        """Cache history item"""
        key = f"hist_{history_id}"
        self.history_cache.put(key, item, {'history_id': history_id})
    
    def invalidate_for_image(self, image):
        """Invalidate all caches for a specific image"""
        if image is None:
            return
        image_id = self._generate_image_id(image)
        self.thumbnail_cache.invalidate(lambda k: image_id in str(k))
        self.processed_cache.invalidate(lambda k: image_id in str(k))
        # Don't invalidate history cache as it's independent
    
    def invalidate_all(self):
        """Invalidate all caches"""
        self.thumbnail_cache.clear()
        self.processed_cache.clear()
        self.history_cache.clear()
    
    def get_stats(self):
        """Get statistics for all caches"""
        return {
            'thumbnail': self.thumbnail_cache.get_stats(),
            'processed': self.processed_cache.get_stats(),
            'history': self.history_cache.get_stats()
        }
    
    def cleanup_old_entries(self, max_age_hours=24):
        """Remove entries older than max_age_hours"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for cache in [self.thumbnail_cache, self.processed_cache, self.history_cache]:
            with cache.lock:
                keys_to_delete = []
                for key, item in cache.cache.items():
                    age = current_time - item['created']
                    if age > max_age_seconds:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    cache.current_size -= cache.cache[key]['size']
                    del cache.cache[key]
                    cache.evictions += 1