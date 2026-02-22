import importlib
import threading
import time
from typing import Any, Callable, Dict, Optional

class LazyLoader:
    """Lazy loading for modules and resources"""
    
    def __init__(self):
        self._loaded_modules = {}
        self._loading_lock = threading.RLock()
        self._load_times = {}
        
    def load_module(self, module_name: str, import_name: str = None) -> Any:
        """Lazily load a module"""
        with self._loading_lock:
            if module_name in self._loaded_modules:
                return self._loaded_modules[module_name]
            
            start = time.time()
            try:
                module = importlib.import_module(module_name)
                if import_name:
                    module = getattr(module, import_name)
                
                self._loaded_modules[module_name] = module
                self._load_times[module_name] = time.time() - start
                return module
            except ImportError as e:
                print(f"Failed to load module {module_name}: {e}")
                return None
    
    def is_loaded(self, module_name: str) -> bool:
        """Check if module is loaded"""
        return module_name in self._loaded_modules
    
    def unload_module(self, module_name: str):
        """Unload a module to free memory"""
        with self._loading_lock:
            if module_name in self._loaded_modules:
                del self._loaded_modules[module_name]
            if module_name in self._load_times:
                del self._load_times[module_name]
    
    def get_load_time(self, module_name: str) -> Optional[float]:
        """Get time taken to load module"""
        return self._load_times.get(module_name)

class LazyModel:
    """Wrapper for lazy-loaded AI models"""
    
    def __init__(self, model_name: str, loader: LazyLoader, load_func: Callable):
        self.model_name = model_name
        self.loader = loader
        self.load_func = load_func
        self._model = None
        self._lock = threading.RLock()
        self._loading = False
        self._load_start_time = None
        
    def _ensure_loaded(self):
        """Ensure model is loaded before use"""
        if self._model is not None:
            return
        
        with self._lock:
            if self._model is not None:
                return
            
            if self._loading:
                # Wait for loading to complete
                while self._loading:
                    time.sleep(0.1)
                return
            
            self._loading = True
            self._load_start_time = time.time()
            
            try:
                # Load the model
                module = self.loader.load_module(self.model_name)
                if module:
                    self._model = self.load_func(module)
                else:
                    # Fallback to traditional method
                    self._model = None
            finally:
                self._loading = False
    
    def __getattr__(self, name):
        """Proxy attribute access to loaded model"""
        self._ensure_loaded()
        if self._model is None:
            raise AttributeError(f"Model {self.model_name} not available")
        return getattr(self._model, name)
    
    def is_available(self) -> bool:
        """Check if model is available"""
        self._ensure_loaded()
        return self._model is not None
    
    def get_load_time(self) -> Optional[float]:
        """Get time taken to load model"""
        if self._load_start_time:
            return time.time() - self._load_start_time
        return None