"""
Simplified FastAPI app for Railway free tier
Save as: backend/main.py
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import subprocess
import sys

app = FastAPI(title="Free AI Video Ad Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage
job_storage: Dict[str, Any] = {}

def install_ai_dependencies():
    """Install AI dependencies at runtime to stay under Railway's 4GB limit"""
    
    print("📦 Installing AI dependencies at runtime...")
    
    try:
        # Install PyTorch CPU version (much smaller)
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "torch==2.1.0", 
            "torchvision==0.16.0",
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ])
        
        # Install other AI packages
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "diffusers==0.24.0",
            "transformers==4.35.2", 
            "git+https://github.com/openai/CLIP.git"
        ])
        
        print("✅ AI dependencies installed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to install AI dependencies: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("🚀 Starting Free AI Video Ad Generator...")
    
    # Create directories
    os.makedirs("generated_videos", exist_ok=True)
    os.makedirs("temp_uploads", exist_ok=True)
    os.makedirs("models_cache", exist_ok=True)
    
    print("✅ Basic server ready!")
    print("💡 AI models will install on first video generation request")

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "running",
        "service": "Free AI Video Ad Generator",
        "version": "1.0.0",
        "ai_ready": False,  # Will be True after first AI install
        "message": "Upload a product image to start!"
    }

@app.post("/upload")
async def upload_product(
    image: UploadFile = File(...),
    name: str = Form(...),
    price: str = Form(...),
    url: str = Form(...),
    description: Optional[str] = Form(None)
):
    """Upload product and start processing"""
    
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    job_id = str(uuid.uuid4())
    
    # Store job info
    job_storage[job_id] = {
        'status': 'queued',
        'product_name': name,
        'price': price,
        'url': url,
        'description': description or f"High-quality {name}",
        'created_at': datetime.now().isoformat(),
        'progress': 'Queued for processing'
    }
    
    # For now, return success (AI processing will be added after basic deployment works)
    return {
        'job_id': job_id,
        'status': 'queued',
        'message': 'Basic upload successful! AI features will be enabled after deployment verification.',
        'next_step': 'Check /status/{job_id} for updates'
    }

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Check job status"""
    
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_storage[job_id]

@app.post("/install-ai")
async def install_ai_models():
    """Install AI dependencies on demand"""
    
    try:
        success = install_ai_dependencies()
        
        if success:
            return {
                "status": "success",
                "message": "AI dependencies installed successfully!",
                "ai_ready": True
            }
        else:
            return {
                "status": "error", 
                "message": "Failed to install AI dependencies"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Installation failed: {str(e)}"
        }

@app.get("/system-info")
async def get_system_info():
    """Get system information"""
    
    import platform
    
    try:
        # Check if AI packages are available
        ai_available = False
        try:
            import torch
            ai_available = True
            gpu_available = torch.cuda.is_available()
        except ImportError:
            gpu_available = False
        
        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "ai_packages_installed": ai_available,
            "gpu_available": gpu_available,
            "working_directory": os.getcwd(),
            "environment": "railway" if os.getenv("RAILWAY_ENVIRONMENT") else "local"
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
