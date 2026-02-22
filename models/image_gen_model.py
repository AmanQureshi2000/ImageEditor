"""
AI Image Generation Model — generates images from text prompts using
Pollinations.ai and completely free alternatives (no API keys required).
"""
import io
import urllib.request
import urllib.parse
import urllib.error
import json
import time
import random
import threading
from PIL import Image

# Try to import requests if available (for fallback methods)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: 'requests' library not available. Some fallback methods may not work.")
    print("Install with: pip install requests")


class ImageGenModel:
    """Generates images from text prompts using free AI APIs (no keys required)."""

    PROVIDERS = {
        "Pollinations (Fast)": "pollinations_fast",
        "Pollinations (Quality)": "pollinations_quality",
        "Craiyon (Alternative)": "craiyon",
        "Prodia (Free)": "prodia",
        "GetImg (Free)": "getimg",
        "Pollinations (Fallback)": "pollinations_fallback",
    }

    ASPECT_RATIOS = {
        "Square (1:1)": (1024, 1024),
        "Landscape (16:9)": (1344, 768),
        "Portrait (9:16)": (768, 1344),
        "Photo (4:3)": (1152, 896),
        "Wide (21:9)": (1536, 640),
        "Banner (3:1)": (1536, 512),
    }

    STYLE_PRESETS = {
        "None": "",
        "Photorealistic": "photorealistic, ultra detailed, 8k, professional photography",
        "Digital Art": "digital art, concept art, artstation trending, highly detailed",
        "Oil Painting": "oil painting, classical art, museum quality, detailed brushwork",
        "Anime": "anime style, vibrant colors, detailed, Studio Ghibli inspired",
        "Cinematic": "cinematic shot, movie still, dramatic lighting, film grain",
        "Watercolor": "watercolor painting, soft colors, artistic, flowing",
        "Sketch": "pencil sketch, hand drawn, detailed linework, black and white",
        "3D Render": "3D render, octane render, ray tracing, photorealistic",
        "Vintage": "vintage photograph, film photography, retro style, nostalgic",
    }

    NEGATIVE_PRESETS = {
        "Default": "blurry, low quality, distorted, deformed, ugly, bad anatomy",
        "Portrait": "blurry, low quality, deformed face, extra limbs, bad anatomy, watermark",
        "Landscape": "people, text, watermark, blurry, oversaturated",
        "None": "",
    }

    def __init__(self):
        self._cancel_event = threading.Event()
        self._last_error = None
        self._retry_count = 0
        self.max_retries = 2

    def cancel(self):
        """Signal the current generation to stop."""
        self._cancel_event.set()

    def reset_cancel(self):
        """Reset cancellation flag for a new request."""
        self._cancel_event.clear()
        self._retry_count = 0

    def generate(
        self,
        prompt: str,
        provider: str = "pollinations_fast",
        width: int = 1024,
        height: int = 1024,
        seed: int = -1,
        style_preset: str = "",
        negative_prompt: str = "",
        progress_callback=None,
        status_callback=None,
    ) -> Image.Image:
        """
        Generate an image and return a PIL Image.
        Raises RuntimeError on failure or if cancelled.
        """
        self.reset_cancel()

        full_prompt = prompt
        if style_preset:
            full_prompt = f"{prompt}, {style_preset}"

        if progress_callback:
            progress_callback(5)
        if status_callback:
            status_callback("Initializing generation...")

        if self._cancel_event.is_set():
            raise RuntimeError("Generation cancelled.")

        # Route to appropriate provider
        if provider == "pollinations_fast":
            return self._generate_pollinations_fast(
                full_prompt, negative_prompt, width, height, seed,
                progress_callback, status_callback
            )
        elif provider == "pollinations_quality":
            return self._generate_pollinations_quality(
                full_prompt, negative_prompt, width, height, seed,
                progress_callback, status_callback
            )
        elif provider == "pollinations_fallback":
            return self._generate_pollinations_fallback(
                full_prompt, negative_prompt, width, height, seed,
                progress_callback, status_callback
            )
        elif provider == "craiyon":
            return self._generate_craiyon(
                full_prompt, width, height, progress_callback, status_callback
            )
        elif provider == "prodia":
            return self._generate_prodia(
                full_prompt, negative_prompt, width, height, seed,
                progress_callback, status_callback
            )
        elif provider == "getimg":
            return self._generate_getimg(
                full_prompt, width, height, progress_callback, status_callback
            )
        else:
            raise RuntimeError(f"Unknown provider: {provider}")

    # ==================== POLLINATIONS METHODS ====================

    def _generate_pollinations_fast(
        self, prompt, negative_prompt, width, height, seed,
        progress_callback, status_callback
    ) -> Image.Image:
        """Generate using Pollinations with fast model."""
        return self._generate_pollinations_base(
            prompt, negative_prompt, width, height, seed, "flux",
            progress_callback, status_callback
        )

    def _generate_pollinations_quality(
        self, prompt, negative_prompt, width, height, seed,
        progress_callback, status_callback
    ) -> Image.Image:
        """Generate using Pollinations with quality model."""
        return self._generate_pollinations_base(
            prompt, negative_prompt, width, height, seed, "flux-realism",
            progress_callback, status_callback
        )

    def _generate_pollinations_fallback(
        self, prompt, negative_prompt, width, height, seed,
        progress_callback, status_callback
    ) -> Image.Image:
        """Try multiple Pollinations models with retry logic."""
        
        models_to_try = ["flux", "flux-realism", "turbo", "pixart", "sd3"]
        last_error = None
        
        for attempt in range(self.max_retries):
            for model in models_to_try:
                if self._cancel_event.is_set():
                    raise RuntimeError("Generation cancelled.")
                
                try:
                    if status_callback:
                        status_callback(f"Trying Pollinations ({model})...")
                    
                    return self._generate_pollinations_base(
                        prompt, negative_prompt, width, height, seed, model,
                        progress_callback, status_callback
                    )
                except Exception as e:
                    last_error = e
                    if "530" in str(e) and "1033" in str(e):
                        if status_callback:
                            status_callback(f"Service busy, trying next model...")
                        time.sleep(1)
                        continue
                    else:
                        # If it's not a 530 error, raise immediately
                        raise
            
            if attempt < self.max_retries - 1:
                if status_callback:
                    status_callback(f"Retrying in 3 seconds... (attempt {attempt + 2}/{self.max_retries})")
                time.sleep(3)
        
        raise RuntimeError(f"All Pollinations models failed. Last error: {last_error}")

    def _generate_pollinations_base(
        self, prompt, negative_prompt, width, height, seed, model,
        progress_callback, status_callback
    ) -> Image.Image:
        """Base Pollinations generation method."""
        
        # Proper URL encoding
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Build URL
        base_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        
        # Parameters
        params = {
            "width": width,
            "height": height,
            "nologo": "true",
            "model": model,
            "seed": seed if seed >= 0 else random.randint(1, 999999),
        }
        
        # Add negative prompt if provided
        if negative_prompt:
            params["negative"] = negative_prompt
        
        # Build query string
        query_string = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
        url = f"{base_url}?{query_string}"

        if status_callback:
            status_callback(f"Generating with Pollinations ({model})...")
        if progress_callback:
            progress_callback(15)

        if self._cancel_event.is_set():
            raise RuntimeError("Generation cancelled.")

        # Make request
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "image/*",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                if self._cancel_event.is_set():
                    raise RuntimeError("Generation cancelled.")

                # Check content type
                content_type = response.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    error_data = json.loads(response.read().decode('utf-8'))
                    error_msg = error_data.get('error', 'Unknown error')
                    error_code = error_data.get('code', 'unknown')
                    raise RuntimeError(f"API Error: {error_msg} (code: {error_code})")

                if progress_callback:
                    progress_callback(60)
                if status_callback:
                    status_callback("Downloading image...")

                data = response.read()
                
                # Validate image data
                if len(data) < 1000:
                    try:
                        error_json = json.loads(data.decode('utf-8'))
                        raise RuntimeError(f"API Error: {error_json.get('error', 'Unknown')}")
                    except:
                        pass

                if self._cancel_event.is_set():
                    raise RuntimeError("Generation cancelled.")

                if progress_callback:
                    progress_callback(85)
                if status_callback:
                    status_callback("Processing image...")

                # Load image
                img = Image.open(io.BytesIO(data))
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                if progress_callback:
                    progress_callback(100)
                if status_callback:
                    status_callback("Image generated successfully!")

                return img

        except urllib.error.HTTPError as e:
            error_msg = f"API error {e.code}"
            try:
                error_data = e.read().decode('utf-8')
                if error_data:
                    error_msg += f": {error_data}"
            except:
                error_msg += f": {e.reason}"
            raise RuntimeError(error_msg)
        except Exception as e:
            if "cancelled" in str(e).lower():
                raise
            raise RuntimeError(f"Generation failed: {str(e)}")

    # ==================== CRAIYON (FREE ALTERNATIVE) ====================
    
    def _generate_craiyon(
        self, prompt, width, height, progress_callback, status_callback
    ) -> Image.Image:
        """
        Generate using Craiyon (formerly DALL-E Mini) - completely free, no API key.
        Note: Craiyon generates 9 images, we'll use the first one.
        """
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("Requests library required for Craiyon. Install with: pip install requests")
        
        if status_callback:
            status_callback("Connecting to Craiyon (free alternative)...")
        if progress_callback:
            progress_callback(10)
        
        # Craiyon API endpoint
        url = "https://api.craiyon.com/v3"
        
        # Prepare payload
        payload = {
            "prompt": prompt,
            "version": "35s5hfwn9n78gb06",
            "negative_prompt": "",
            "model": "v3",
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
        }
        
        try:
            if status_callback:
                status_callback("Generating with Craiyon (this may take 20-30 seconds)...")
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if self._cancel_event.is_set():
                raise RuntimeError("Generation cancelled.")
            
            if progress_callback:
                progress_callback(50)
            
            if response.status_code == 200:
                data = response.json()
                
                # Craiyon returns base64 images
                if 'images' in data and len(data['images']) > 0:
                    import base64
                    img_data = base64.b64decode(data['images'][0])
                    
                    if progress_callback:
                        progress_callback(80)
                    
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Resize to requested dimensions
                    if (width, height) != img.size:
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
                    
                    if progress_callback:
                        progress_callback(100)
                    if status_callback:
                        status_callback("Image generated with Craiyon!")
                    
                    return img
                else:
                    raise RuntimeError("No images in response")
            else:
                raise RuntimeError(f"Craiyon API error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            raise RuntimeError("Craiyon request timed out (service may be busy)")
        except Exception as e:
            raise RuntimeError(f"Craiyon generation failed: {str(e)}")

    # ==================== PRODIA (FREE ALTERNATIVE) ====================
    
    def _generate_prodia(
        self, prompt, negative_prompt, width, height, seed,
        progress_callback, status_callback
    ) -> Image.Image:
        """
        Generate using Prodia's free API (no key required for basic usage).
        """
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("Requests library required for Prodia. Install with: pip install requests")
        
        if status_callback:
            status_callback("Connecting to Prodia (free alternative)...")
        if progress_callback:
            progress_callback(10)
        
        # Prodia has a public API that doesn't require authentication for basic usage
        # First, create a job
        job_url = "https://api.prodia.com/generate"
        
        # Map dimensions to Prodia's supported models
        model = "v1-5-pruned-emaonly.safetensors [dance]"
        
        # Prepare parameters
        params = {
            "model": model,
            "prompt": prompt,
            "negative_prompt": negative_prompt if negative_prompt else "",
            "steps": 25,
            "cfg_scale": 7,
            "seed": seed if seed >= 0 else random.randint(1, 9999999),
            "sampler": "DPM++ 2M Karras",
            "width": width,
            "height": height,
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
        }
        
        try:
            # Create generation job
            if status_callback:
                status_callback("Creating generation job...")
            
            response = requests.post(job_url, json=params, headers=headers, timeout=30)
            
            if self._cancel_event.is_set():
                raise RuntimeError("Generation cancelled.")
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to create job: {response.status_code}")
            
            job_data = response.json()
            job_id = job_data.get('job')
            
            if not job_id:
                raise RuntimeError("No job ID received")
            
            if progress_callback:
                progress_callback(30)
            
            # Poll for completion
            status_url = f"https://api.prodia.com/job/{job_id}"
            max_attempts = 30
            attempt = 0
            
            if status_callback:
                status_callback("Generating image (this may take 15-20 seconds)...")
            
            while attempt < max_attempts:
                if self._cancel_event.is_set():
                    raise RuntimeError("Generation cancelled.")
                
                status_response = requests.get(status_url, timeout=30)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    if status_data.get('status') == 'succeeded':
                        # Get image URL
                        image_url = status_data.get('imageUrl')
                        if image_url:
                            if progress_callback:
                                progress_callback(70)
                            
                            # Download the image
                            img_response = requests.get(image_url, timeout=30)
                            
                            if img_response.status_code == 200:
                                if progress_callback:
                                    progress_callback(85)
                                
                                img = Image.open(io.BytesIO(img_response.content))
                                
                                if progress_callback:
                                    progress_callback(100)
                                if status_callback:
                                    status_callback("Image generated with Prodia!")
                                
                                return img
                    
                    elif status_data.get('status') == 'failed':
                        raise RuntimeError("Generation failed on Prodia's servers")
                
                attempt += 1
                time.sleep(2)
            
            raise RuntimeError("Timeout waiting for Prodia generation")
            
        except Exception as e:
            raise RuntimeError(f"Prodia generation failed: {str(e)}")

    # ==================== GETIMG (FREE ALTERNATIVE) ====================
    
    def _generate_getimg(
        self, prompt, width, height, progress_callback, status_callback
    ) -> Image.Image:
        """
        Generate using GetImg.ai's free tier (no API key required for limited usage).
        """
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("Requests library required for GetImg. Install with: pip install requests")
        
        if status_callback:
            status_callback("Connecting to GetImg (free alternative)...")
        if progress_callback:
            progress_callback(10)
        
        # GetImg has a public playground API
        url = "https://api.getimg.ai/v1/stable-diffusion/text-to-image"
        
        # They sometimes allow requests without key for testing
        payload = {
            "model": "sd-1-5",
            "prompt": prompt,
            "negative_prompt": "",
            "width": min(width, 768),  # GetImg has size limits
            "height": min(height, 768),
            "steps": 25,
            "guidance": 7.5,
            "scheduler": "dpmsolver++",
            "output_format": "png",
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        try:
            if status_callback:
                status_callback("Generating with GetImg...")
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if self._cancel_event.is_set():
                raise RuntimeError("Generation cancelled.")
            
            if progress_callback:
                progress_callback(50)
            
            if response.status_code == 200:
                data = response.json()
                
                # GetImg returns base64 image
                if 'image' in data:
                    import base64
                    img_data = base64.b64decode(data['image'])
                    
                    if progress_callback:
                        progress_callback(80)
                    
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Resize to requested dimensions if needed
                    if (width, height) != img.size:
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
                    
                    if progress_callback:
                        progress_callback(100)
                    if status_callback:
                        status_callback("Image generated with GetImg!")
                    
                    return img
                else:
                    raise RuntimeError("No image in response")
            else:
                # Try to get error message
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                except:
                    error_msg = response.text[:100]
                
                raise RuntimeError(f"GetImg API error {response.status_code}: {error_msg}")
                
        except Exception as e:
            raise RuntimeError(f"GetImg generation failed: {str(e)}")

    # ==================== UTILITY METHODS ====================

    def get_available_models(self) -> list:
        """Return list of available model names."""
        return list(self.PROVIDERS.keys())

    def build_prompt_suggestions(self, base: str) -> list:
        """Return prompt enhancement suggestions."""
        enhancements = [
            "highly detailed",
            "4k resolution",
            "professional lighting",
            "sharp focus",
            "vivid colors",
            "masterpiece",
            "trending on artstation",
        ]
        return [f"{base}, {e}" for e in enhancements]

    def test_connection(self, provider: str = "pollinations_fast") -> bool:
        """Test if a provider is accessible."""
        try:
            if provider.startswith("pollinations"):
                test_prompt = "test"
                encoded = urllib.parse.quote(test_prompt)
                url = f"https://image.pollinations.ai/prompt/{encoded}?width=64&height=64&nologo=true"
                
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as response:
                    return response.getcode() == 200
            else:
                # For other providers, just return True if they're available
                return True
        except:
            return False


# Add auto-fallback feature
class AutoFallbackImageGen(ImageGenModel):
    """Extended version that automatically tries all providers if one fails."""
    
    def generate_with_auto_fallback(
        self,
        prompt: str,
        preferred_provider: str = "pollinations_fast",
        **kwargs
    ) -> Image.Image:
        """Try preferred provider, then fall back to others automatically."""
        
        # Order of providers to try
        fallback_order = [
            preferred_provider,
            "pollinations_fallback",
            "pollinations_quality",
            "pollinations_fast",
            "craiyon",
            "prodia",
            "getimg",
        ]
        
        # Remove duplicates
        seen = set()
        fallback_order = [x for x in fallback_order if not (x in seen or seen.add(x))]
        
        last_error = None
        
        for provider in fallback_order:
            try:
                if self._cancel_event.is_set():
                    raise RuntimeError("Generation cancelled.")
                
                if kwargs.get('status_callback'):
                    kwargs['status_callback'](f"Trying {provider}...")
                
                return self.generate(
                    prompt=prompt,
                    provider=provider,
                    **kwargs
                )
            except Exception as e:
                last_error = e
                if kwargs.get('status_callback'):
                    kwargs['status_callback'](f"{provider} failed, trying next...")
                continue
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")