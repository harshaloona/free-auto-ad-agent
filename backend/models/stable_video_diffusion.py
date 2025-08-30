"""
Local Stable Video Diffusion implementation
Save as: backend/models/stable_video_diffusion.py
"""

import torch
from diffusers import StableVideoDiffusionPipeline
from PIL import Image
import numpy as np
import cv2
import os
import tempfile
from typing import Optional, List
import gc

class LocalVideoGenerator:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline = None
        self.model_loaded = False
        self.model_path = "stabilityai/stable-video-diffusion-img2vid-xt"
        
        print(f"🎥 Video Generator initialized on {self.device}")
        
        # Performance settings
        self.quality_configs = {
            "fast": {
                "num_inference_steps": 15,
                "guidance_scale": 3.0,
                "height": 512,
                "width": 512,
                "num_frames": 14
            },
            "balanced": {
                "num_inference_steps": 25, 
                "guidance_scale": 7.5,
                "height": 576,
                "width": 1024,
                "num_frames": 25
            },
            "high": {
                "num_inference_steps": 35,
                "guidance_scale": 12.0,
                "height": 576,
                "width": 1024,
                "num_frames": 25
            }
        }
    
    def load_model(self):
        """Load Stable Video Diffusion model (lazy loading)"""
        if self.model_loaded:
            return True
            
        print("📥 Loading Stable Video Diffusion model...")
        print("⏳ This takes 30-60 seconds on first run...")
        
        try:
            # Clear any existing GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Load pipeline with optimizations
            self.pipeline = StableVideoDiffusionPipeline.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                variant="fp16" if self.device == "cuda" else None
            )
            
            # Move to device
            self.pipeline = self.pipeline.to(self.device)
            
            # Enable memory optimizations
            if self.device == "cuda":
                self.pipeline.enable_model_cpu_offload()
                self.pipeline.enable_vae_slicing()
                self.pipeline.enable_attention_slicing(1)
            
            self.model_loaded = True
            print("✅ Stable Video Diffusion loaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            print("💡 Try running setup_models.py first")
            return False
    
    def generate_product_video(
        self, 
        image_path: str, 
        motion_type: str = "orbit",
        quality: str = "fast",
        seed: Optional[int] = None
    ) -> str:
        """
        Generate video from product image
        
        Args:
            image_path: Path to product image
            motion_type: Type of motion (orbit, zoom, sway)
            quality: Generation quality (fast, balanced, high)
            seed: Random seed for reproducible results
        
        Returns:
            Path to generated video file
        """
        
        if not self.load_model():
            raise Exception("Failed to load video generation model")
        
        print(f"🎬 Generating {motion_type} video in {quality} mode...")
        
        # Load and preprocess image
        image = self._preprocess_image(image_path, quality)
        
        # Get quality configuration
        config = self.quality_configs.get(quality, self.quality_configs["fast"])
        
        # Set random seed
        if seed is None:
            seed = 42
        generator = torch.manual_seed(seed)
        
        try:
            # Generate video frames
            with torch.no_grad():
                frames = self.pipeline(
                    image,
                    height=config["height"],
                    width=config["width"], 
                    num_frames=config["num_frames"],
                    decode_chunk_size=8,
                    generator=generator,
                    num_inference_steps=config["num_inference_steps"],
                    fps=8
                ).frames[0]
            
            # Convert frames to video
            video_path = self._frames_to_video(frames, motion_type, quality)
            
            print(f"✅ Video generated: {video_path}")
            
            # Clear GPU memory
            self._clear_memory()
            
            return video_path
            
        except Exception as e:
            self._clear_memory()
            raise Exception(f"Video generation failed: {e}")
    
    def _preprocess_image(self, image_path: str, quality: str) -> Image.Image:
        """Preprocess image for video generation"""
        
        image = Image.open(image_path).convert("RGB")
        
        # Get target size based on quality
        config = self.quality_configs[quality]
        target_size = (config["width"], config["height"])
        
        # Resize with proper aspect ratio
        image.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Pad to exact size if needed
        if image.size != target_size:
            new_image = Image.new("RGB", target_size, (255, 255, 255))
            paste_pos = (
                (target_size[0] - image.size[0]) // 2,
                (target_size[1] - image.size[1]) // 2
            )
            new_image.paste(image, paste_pos)
            image = new_image
        
        return image
    
    def _frames_to_video(self, frames: List[Image.Image], motion_type: str, quality: str) -> str:
        """Convert PIL frames to MP4 video"""
        
        # Create output directory
        output_dir = "generated_videos"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{motion_type}_{quality}_{timestamp}.mp4"
        video_path = os.path.join(output_dir, filename)
        
        # Convert PIL frames to numpy arrays
        frame_arrays = []
        for frame in frames:
            frame_array = np.array(frame)
            frame_arrays.append(frame_array)
        
        # Get video dimensions
        height, width = frame_arrays[0].shape[:2]
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 8  # Standard for social media
        out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
        
        # Write frames
        for frame_array in frame_arrays:
            # Convert RGB to BGR for OpenCV
            frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)
        
        # Release video writer
        out.release()
        cv2.destroyAllWindows()
        
        print(f"💾 Video saved: {video_path}")
        return video_path
    
    def _clear_memory(self):
        """Clear GPU memory after generation"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
    
    def unload_model(self):
        """Unload model to free memory"""
        if self.pipeline:
            del self.pipeline
            self.pipeline = None
            self.model_loaded = False
            self._clear_memory()
            print("🗑️  Model unloaded to free memory")
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        return {
            "model_loaded": self.model_loaded,
            "device": self.device,
            "model_path": self.model_path,
            "gpu_available": torch.cuda.is_available(),
            "gpu_memory_gb": torch.cuda.get_device_properties(0).total_memory / 1e9 if torch.cuda.is_available() else 0
        }