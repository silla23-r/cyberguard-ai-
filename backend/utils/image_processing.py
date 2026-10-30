"""
Image preprocessing and computer vision utilities for CyberGuard AI.
Normalizes incoming screenshots, improves OCR clarity, and extracts QR crops.
"""
import io
import logging
from typing import List, Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

def preprocess_image_bytes(image_bytes: bytes) -> bytes:
    """
    Cleans up noise, increases contrast, and resizes large images
    to optimize token usage and OCR precision.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert RGBA/Palette to RGB
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        # Downscale if excessively large to save tokens and latency
        max_dim = 1920
        if max(image.size) > max_dim:
            image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            
        # Subtle contrast and sharpness boost for text clarity
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)
        
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=90)
        return output_buffer.getvalue()
    except Exception as e:
        logger.warning(f"Error during image preprocessing: {e}. Returning raw bytes.")
        return image_bytes

def get_pil_image(image_bytes: bytes) -> Optional[Image.Image]:
    """Helper to convert bytes into a PIL Image safely."""
    try:
        return Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        logger.error(f"Failed to parse PIL Image: {e}")
        return None
