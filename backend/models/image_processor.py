"""
Image variant generator for different ad formats
Save as: backend/models/image_processor.py
"""

from PIL import Image, ImageFilter, ImageEnhance
import cv2
import numpy as np
import os
from typing import Dict, Tuple
import tempfile

class ImageVariantGenerator:
    def __init__(self):
        # Standard social media dimensions
        self.formats = {
            "feed": (1080, 1080),      # Square feed posts
            "story": (1080, 1920),     # Instagram/Facebook Stories  
            "reels": (1080, 1920),     # Same as stories but optimized for video
            "landscape": (1200, 630)   # Facebook feed landscape
        }
        
        print("🖼️  Image processor initialized with formats:", list(self.formats.keys()))
    
    def generate_variants(self, image_path: str) -> Dict[str, str]:
        """
        Generate image variants for different ad formats
        
        Args:
            image_path: Path to source product image
            
        Returns:
            Dict mapping format names to generated image paths
        """
        
        # Load original image
        original = Image.open(image_path).convert("RGB")
        print(f"📸 Processing image: {original.size} pixels")
        
        variants = {}
        
        for format_name, (target_width, target_height) in self.formats.items():
            print(f"🔄 Creating {format_name} variant ({target_width}x{target_height})")
            
            # Generate variant
            variant_image = self._create_format_variant(
                original, 
                target_width, 
                target_height,
                format_name
            )
            
            # Save variant
            variant_path = self._save_variant(variant_image, image_path, format_name)
            variants[format_name] = variant_path
        
        print(f"✅ Generated {len(variants)} image variants")
        return variants
    
    def _create_format_variant(
        self, 
        image: Image.Image, 
        target_width: int, 
        target_height: int,
        format_name: str
    ) -> Image.Image:
        """Create optimized variant for specific format"""
        
        original_width, original_height = image.size
        target_aspect = target_width / target_height
        original_aspect = original_width / original_height
        
        if format_name in ["feed"]:
            # Square format - crop to center square
            return self._create_square_variant(image, target_width, target_height)
        
        elif format_name in ["story", "reels"]:
            # Vertical format - add padding or crop smartly
            return self._create_vertical_variant(image, target_width, target_height)
        
        elif format_name in ["landscape"]:
            # Landscape format - center with padding
            return self._create_landscape_variant(image, target_width, target_height)
        
        else:
            # Default: smart crop/pad
            return self._smart_resize(image, target_width, target_height)
    
    def _create_square_variant(self, image: Image.Image, size: int, target_height: int) -> Image.Image:
        """Create square variant - good for feed posts"""
        
        width, height = image.size
        
        # Create square crop
        if width > height:
            # Landscape: crop sides
            crop_size = min(width, height)
            left = (width - crop_size) // 2
            top = (height - crop_size) // 2
            image = image.crop((left, top, left + crop_size, top + crop_size))
        elif height > width:
            # Portrait: crop top/bottom, preserve center
            crop_size = min(width, height)
            left = (width - crop_size) // 2
            top = (height - crop_size) // 4  # Bias toward top for products
            image = image.crop((left, top, left + crop_size, top + crop_size))
        
        # Resize to target
        return image.resize((size, target_height), Image.Resampling.LANCZOS)
    
    def _create_vertical_variant(self, image: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """Create vertical variant for Stories/Reels"""
        
        # Create canvas with gradient background
        canvas = Image.new("RGB", (target_width, target_height), (245, 245, 245))
        
        # Add subtle gradient background
        canvas = self._add_gradient_background(canvas)
        
        # Resize product image to fit nicely
        img_width, img_height = image.size
        
        # Calculate size to fit in upper 70% of canvas
        available_height = int(target_height * 0.7)
        available_width = target_width - 40  # 20px padding each side
        
        # Maintain aspect ratio
        scale_w = available_width / img_width
        scale_h = available_height / img_height
        scale = min(scale_w, scale_h)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center horizontally, position in upper portion vertically
        x = (target_width - new_width) // 2
        y = (target_height - new_height) // 3  # Upper third
        
        # Add subtle shadow
        shadow_offset = 8
        shadow = Image.new("RGBA", (new_width + shadow_offset*2, new_height + shadow_offset*2), (0, 0, 0, 30))
        canvas.paste(shadow, (x - shadow_offset, y - shadow_offset), shadow)
        
        # Paste main image
        canvas.paste(resized_image, (x, y))
        
        return canvas
    
    def _create_landscape_variant(self, image: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """Create landscape variant for Facebook feed"""
        
        # Create canvas
        canvas = Image.new("RGB", (target_width, target_height), (255, 255, 255))
        
        # Resize image to fit
        img_width, img_height = image.size
        scale_w = target_width / img_width
        scale_h = target_height / img_height
        scale = min(scale_w, scale_h) * 0.8  # Leave some padding
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center the image
        x = (target_width - new_width) // 2
        y = (target_height - new_height) // 2
        
        canvas.paste(resized_image, (x, y))
        
        return canvas
    
    def _smart_resize(self, image: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """Smart resize with aspect ratio preservation"""
        
        # Calculate scaling
        scale_w = target_width / image.width
        scale_h = target_height / image.height
        scale = min(scale_w, scale_h)
        
        # New dimensions
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)
        
        # Resize image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create canvas and center image
        canvas = Image.new("RGB", (target_width, target_height), (255, 255, 255))
        x = (target_width - new_width) // 2
        y = (target_height - new_height) // 2
        canvas.paste(resized, (x, y))
        
        return canvas
    
    def _add_gradient_background(self, canvas: Image.Image) -> Image.Image:
        """Add subtle gradient background"""
        
        width, height = canvas.size
        
        # Create gradient from light gray to white
        gradient = np.zeros((height, width, 3), dtype=np.uint8)
        
        for i in range(height):
            # Linear gradient from 240 to 255
            value = int(240 + (255 - 240) * (i / height))
            gradient[i, :] = [value, value, value]
        
        gradient_image = Image.fromarray(gradient, 'RGB')
        
        # Blend with original canvas
        return Image.blend(canvas, gradient_image, 0.3)
    
    def _save_variant(self, image: Image.Image, original_path: str, format_name: str) -> str:
        """Save variant image to temporary file"""
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        # Generate filename
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        filename = f"{base_name}_{format_name}_variant.jpg"
        variant_path = os.path.join(temp_dir, filename)
        
        # Save with high quality
        image.save(variant_path, "JPEG", quality=95, optimize=True)
        
        return variant_path
    
    def enhance_product_image(self, image_path: str) -> str:
        """Apply enhancement filters to make product look better"""
        
        image = Image.open(image_path)
        
        # Enhance contrast slightly
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)
        
        # Enhance color saturation slightly
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.05)
        
        # Enhance sharpness slightly
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.05)
        
        # Save enhanced version
        enhanced_path = image_path.replace('.jpg', '_enhanced.jpg')
        image.save(enhanced_path, "JPEG", quality=95)
        
        return enhanced_path