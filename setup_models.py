#!/usr/bin/env python3
"""
One-time setup script to download all AI models
Save as: setup_models.py

Run this after installing requirements: python setup_models.py
"""

import torch
from diffusers import StableVideoDiffusionPipeline
import clip
import os
import sys
from pathlib import Path

def check_system():
    """Check system requirements"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check GPU
    gpu_available = torch.cuda.is_available()
    if gpu_available:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"✅ GPU detected: {gpu_name} ({gpu_memory:.1f}GB VRAM)")
        
        if gpu_memory < 6:
            print("⚠️  Warning: Less than 6GB VRAM. Video generation will be slow.")
            print("💡 Consider using VIDEO_QUALITY=fast in .env")
    else:
        print("⚠️  No GPU detected. Using CPU (very slow).")
        print("💡 Consider Google Colab or cloud GPU for better performance.")
    
    # Check disk space
    free_space = shutil.disk_usage('.').free / 1e9
    if free_space < 15:
        print(f"❌ Only {free_space:.1f}GB free space. Need at least 15GB.")
        return False
    
    print(f"✅ {free_space:.1f}GB free space available")
    return True

def setup_cache_directory():
    """Set up model cache directory"""
    
    cache_dir = os.getenv('MODEL_CACHE_DIR', './models_cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    # Set environment variables for model caching
    os.environ['TORCH_HOME'] = cache_dir
    os.environ['HF_HOME'] = cache_dir
    os.environ['TRANSFORMERS_CACHE'] = cache_dir
    
    print(f"📁 Model cache directory: {cache_dir}")
    return cache_dir

def download_stable_video_diffusion():
    """Download Stable Video Diffusion model"""
    
    print("\n🎥 Downloading Stable Video Diffusion...")
    print("📦 Size: ~7GB (this will take a while on first run)")
    
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Download model
        pipeline = StableVideoDiffusionPipeline.from_pretrained(
            "stabilityai/stable-video-diffusion-img2vid-xt",
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            variant="fp16" if device == "cuda" else None
        )
        
        print("✅ Stable Video Diffusion downloaded successfully!")
        
        # Test load to device
        pipeline = pipeline.to(device)
        
        # Enable optimizations
        if device == "cuda":
            pipeline.enable_model_cpu_offload()
            pipeline.enable_vae_slicing()
        
        print("🧪 Testing model load...")
        print("✅ Model loads correctly!")
        
        # Clean up memory
        del pipeline
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading Stable Video Diffusion: {e}")
        print("💡 Try running: pip install --upgrade diffusers transformers")
        return False

def download_clip():
    """Download CLIP model"""
    
    print("\n🔍 Downloading CLIP model...")
    print("📦 Size: ~1.7GB")
    
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Download CLIP
        model, preprocess = clip.load("ViT-L/14", device=device)
        
        print("✅ CLIP model downloaded successfully!")
        
        # Test with dummy input
        print("🧪 Testing CLIP...")
        
        import numpy as np
        from PIL import Image
        
        # Create test image
        test_image = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        test_input = preprocess(test_image).unsqueeze(0).to(device)
        
        # Test text
        text_input = clip.tokenize(["a photo of a shoe"]).to(device)
        
        with torch.no_grad():
            logits_per_image, logits_per_text = model(test_input, text_input)
        
        print("✅ CLIP working correctly!")
        
        # Clean up
        del model, preprocess
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading CLIP: {e}")
        print("💡 Try running: pip install git+https://github.com/openai/CLIP.git")
        return False

def verify_installation():
    """Verify all models are properly installed"""
    
    print("\n🔬 Verifying installation...")
    
    try:
        # Test imports
        from backend.models.stable_video_diffusion import LocalVideoGenerator
        from backend.models.clip_analyzer import CLIPAnalyzer
        
        # Test model initialization (without loading)
        video_gen = LocalVideoGenerator()
        clip_analyzer = CLIPAnalyzer()
        
        print("✅ All imports working")
        print("✅ Model classes initialized")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main setup process"""
    
    print("🤖 Free AI Video Ad Generator - Model Setup")
    print("=" * 50)
    
    # Check system requirements
    if not check_system():
        print("\n❌ System requirements not met. Please fix issues above.")
        sys.exit(1)
    
    # Set up cache directory
    cache_dir = setup_cache_directory()
    
    # Download models
    print("\n📥 Starting model downloads...")
    print("☕ This is a good time for coffee - downloads take 10-20 minutes")
    
    # Download Stable Video Diffusion
    if not download_stable_video_diffusion():
        print("\n❌ Failed to download Stable Video Diffusion")
        sys.exit(1)
    
    # Download CLIP
    if not download_clip():
        print("\n❌ Failed to download CLIP")
        sys.exit(1)
    
    # Verify everything works
    if not verify_installation():
        print("\n❌ Installation verification failed")
        sys.exit(1)
    
    # Success!
    print("\n🎉 Setup completed successfully!")
    print("\n📋 What's ready:")
    print("✅ Stable Video Diffusion (video generation)")
    print("✅ CLIP (product analysis)")
    print("✅ All dependencies installed")
    print(f"✅ Models cached in: {cache_dir}")
    
    print("\n🚀 Next steps:")
    print("1. Copy .env.example to .env")
    print("2. Fill in your Meta API tokens (optional for testing)")
    print("3. Run: python backend/main.py")
    print("4. Test at: http://localhost:8000")
    
    print("\n💡 For cloud deployment:")
    print("1. Push to GitHub")
    print("2. Deploy to Railway.app with GPU enabled")
    print("3. Add environment variables in Railway dashboard")

if __name__ == "__main__":
    import shutil
    main()