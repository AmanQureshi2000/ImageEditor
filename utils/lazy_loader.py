import importlib
import threading
import time
from typing import Any, Callable, Dict, Optional, Union

class LazyLoader:
    """Lazy loading for modules and resources"""
    
    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}
        self._loading_lock = threading.RLock()
        self._load_times: Dict[str, float] = {}
        self._import_errors: Dict[str, str] = {}
        
    def load_module(self, module_name: str, import_name: Optional[str] = None, 
                   package: Optional[str] = None) -> Optional[Any]:
        """
        Lazily load a module
        
        Args:
            module_name: Name of the module to import
            import_name: Specific attribute to import from the module
            package: Package context for relative imports
        
        Returns:
            Loaded module/attribute or None if import fails
        """
        with self._loading_lock:
            # Create a composite key for cached modules
            cache_key = f"{module_name}.{import_name}" if import_name else module_name
            
            if cache_key in self._loaded_modules:
                return self._loaded_modules[cache_key]
            
            start = time.time()
            try:
                # Import the module
                module = importlib.import_module(module_name, package=package)
                
                # If specific attribute requested, get it from module
                if import_name:
                    try:
                        result = getattr(module, import_name)
                    except AttributeError:
                        error_msg = f"Attribute '{import_name}' not found in module '{module_name}'"
                        self._import_errors[module_name] = error_msg
                        print(f"Failed to load {cache_key}: {error_msg}")
                        return None
                else:
                    result = module
                
                # Cache the result
                self._loaded_modules[cache_key] = result
                self._load_times[cache_key] = time.time() - start
                
                # Remove any previous error for this module
                self._import_errors.pop(module_name, None)
                
                return result
                
            except ImportError as e:
                error_msg = str(e)
                self._import_errors[module_name] = error_msg
                print(f"Failed to load module {module_name}: {error_msg}")
                return None
            except Exception as e:
                error_msg = f"Unexpected error loading {module_name}: {str(e)}"
                self._import_errors[module_name] = error_msg
                print(error_msg)
                return None
    
    def is_loaded(self, module_name: str, import_name: Optional[str] = None) -> bool:
        """Check if module/attribute is loaded"""
        cache_key = f"{module_name}.{import_name}" if import_name else module_name
        return cache_key in self._loaded_modules
    
    def unload_module(self, module_name: str, import_name: Optional[str] = None):
        """Unload a module to free memory"""
        with self._loading_lock:
            cache_key = f"{module_name}.{import_name}" if import_name else module_name
            
            if cache_key in self._loaded_modules:
                # Try to clean up if possible
                module = self._loaded_modules[cache_key]
                if hasattr(module, '__dict__'):
                    # Clear the module's dictionary to help garbage collection
                    module.__dict__.clear()
                
                del self._loaded_modules[cache_key]
            
            if cache_key in self._load_times:
                del self._load_times[cache_key]
    
    def get_load_time(self, module_name: str, import_name: Optional[str] = None) -> Optional[float]:
        """Get time taken to load module"""
        cache_key = f"{module_name}.{import_name}" if import_name else module_name
        return self._load_times.get(cache_key)
    
    def get_error(self, module_name: str) -> Optional[str]:
        """Get the last error for a module if any"""
        return self._import_errors.get(module_name)
    
    def clear_errors(self):
        """Clear all stored import errors"""
        with self._loading_lock:
            self._import_errors.clear()
    
    def get_loaded_modules(self) -> list:
        """Get list of all loaded module keys"""
        with self._loading_lock:
            return list(self._loaded_modules.keys())

class LazyModel:
    """Wrapper for lazy-loaded AI models with improved error handling"""
    
    def __init__(self, model_name: str, loader: LazyLoader, 
                 load_func: Optional[Callable] = None):
        """
        Initialize lazy model wrapper
        
        Args:
            model_name: Name of the module to load
            loader: LazyLoader instance
            load_func: Optional function to transform the loaded module
        """
        self.model_name = model_name
        self.loader = loader
        self.load_func = load_func or (lambda x: x)  # Identity function if None
        self._model = None
        self._lock = threading.RLock()
        self._loading = False
        self._load_start_time: Optional[float] = None
        self._load_error: Optional[str] = None
        self._load_attempts = 0
        self._max_attempts = 3
        
    def _ensure_loaded(self):
        """Ensure model is loaded before use with retry logic"""
        if self._model is not None:
            return
        
        with self._lock:
            # Double-check after acquiring lock
            if self._model is not None:
                return
            
            if self._loading:
                # Wait for loading to complete with timeout
                timeout = 30  # 30 seconds timeout
                start_wait = time.time()
                while self._loading:
                    if time.time() - start_wait > timeout:
                        self._loading = False
                        raise TimeoutError(f"Loading {self.model_name} timed out after {timeout}s")
                    time.sleep(0.1)
                return
            
            self._loading = True
            self._load_start_time = time.time()
            self._load_attempts += 1
            
            try:
                # Load the model with retries
                for attempt in range(self._max_attempts):
                    try:
                        module = self.loader.load_module(self.model_name)
                        if module is not None:
                            self._model = self.load_func(module)
                            self._load_error = None
                            break
                        else:
                            error = self.loader.get_error(self.model_name)
                            self._load_error = error or f"Failed to load {self.model_name}"
                            if attempt < self._max_attempts - 1:
                                time.sleep(1)  # Wait before retry
                            continue
                    except Exception as e:
                        self._load_error = str(e)
                        if attempt < self._max_attempts - 1:
                            time.sleep(1)
                        continue
                
            finally:
                self._loading = False
    
    def __getattr__(self, name):
        """Proxy attribute access to loaded model"""
        self._ensure_loaded()
        if self._model is None:
            raise AttributeError(
                f"Model {self.model_name} not available. "
                f"Last error: {self._load_error or 'Unknown error'}"
            )
        
        # Check if attribute exists
        if not hasattr(self._model, name):
            raise AttributeError(
                f"'{self.model_name}' object has no attribute '{name}'"
            )
        
        return getattr(self._model, name)
    
    def __call__(self, *args, **kwargs):
        """Allow the wrapper to be called directly if the model is callable"""
        self._ensure_loaded()
        if self._model is None:
            raise RuntimeError(
                f"Model {self.model_name} not available. "
                f"Last error: {self._load_error or 'Unknown error'}"
            )
        
        if not callable(self._model):
            raise TypeError(f"'{self.model_name}' object is not callable")
        
        return self._model(*args, **kwargs)
    
    def is_available(self) -> bool:
        """Check if model is available"""
        try:
            self._ensure_loaded()
            return self._model is not None
        except:
            return False
    
    def get_load_time(self) -> Optional[float]:
        """Get time taken to load model"""
        if self._load_start_time and self._model is not None:
            return time.time() - self._load_start_time
        return None
    
    def get_error(self) -> Optional[str]:
        """Get the last error that occurred during loading"""
        return self._load_error
    
    def reset(self):
        """Reset the lazy model (force reload on next access)"""
        with self._lock:
            self._model = None
            self._loading = False
            self._load_error = None
            self._load_attempts = 0
    
    def __repr__(self) -> str:
        """String representation"""
        status = "loaded" if self._model is not None else "not loaded"
        error = f", error: {self._load_error}" if self._load_error else ""
        return f"<LazyModel {self.model_name} ({status}{error})>"
    
    def __bool__(self) -> bool:
        """Boolean representation - True if model is available"""
        return self.is_available()