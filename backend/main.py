from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import os
import uuid
import json
import tempfile
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

app = FastAPI(title="Free AI Video Ad Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components (lazy loaded)
ai_components = {}
job_storage: Dict[str, Any] = {}

def get_ai_components():
    """Initialize AI components on first use"""
    if not ai_components:
        print("🤖 Loading AI components...")
        try:
            from models.clip_analyzer import CLIPAnalyzer
            from models.stable_video_diffusion import LocalVideoGenerator
            from models.image_processor import ImageVariantGenerator
            from utils.video_overlay import VideoOverlayProcessor
            from utils.storage import LocalStorage
            
            ai_components['clip'] = CLIPAnalyzer()
            ai_components['video'] = LocalVideoGenerator()
            ai_components['image'] = ImageVariantGenerator()
            ai_components['overlay'] = VideoOverlayProcessor()
            ai_components['storage'] = LocalStorage()
            print("✅ AI components loaded!")
        except Exception as e:
            print(f"❌ Failed to load AI components: {e}")
            raise
    return ai_components

@app.on_event("startup")
async def startup_event():
    os.makedirs("generated_videos", exist_ok=True)
    os.makedirs("temp_uploads", exist_ok=True)
    os.makedirs("models_cache", exist_ok=True)

@app.get("/")
async def root():
    return {"status": "running", "service": "Free AI Video Ad Generator"}

@app.post("/upload")
async def upload_product(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    name: str = Form(...),
    price: str = Form(...),
    url: str = Form(...),
    description: Optional[str] = Form(None),
    quality: str = Form("fast")
):
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    job_id = str(uuid.uuid4())
    image_data = await image.read()
    
    job_storage[job_id] = {
        'status': 'queued',
        'product_name': name,
        'price': price,
        'url': url,
        'description': description,
        'quality': quality,
        'created_at': datetime.now().isoformat(),
        'progress': 'Queued for processing'
    }
    
    background_tasks.add_task(process_video_generation, job_id, image_data, {
        'name': name, 'price': price, 'url': url, 
        'description': description, 'quality': quality
    })
    
    return {'job_id': job_id, 'status': 'queued', 'estimated_time': '2-8 minutes'}

async def process_video_generation(job_id: str, image_data: bytes, product_info: dict):
    try:
        components = get_ai_components()
        
        job_storage[job_id]['status'] = 'processing'
        job_storage[job_id]['progress'] = 'Analyzing product...'
        
        # Save temp image
        temp_path = f"temp_uploads/{job_id}.jpg"
        with open(temp_path, "wb") as f:
            f.write(image_data)
        
        # Analyze product
        analysis = components['clip'].analyze_product(image_data)
        
        job_storage[job_id]['progress'] = 'Generating image variants...'
        
        # Generate variants
        variants = components['image'].generate_variants(temp_path)
        
        generated_videos = []
        
        for format_name, variant_path in variants.items():
            job_storage[job_id]['progress'] = f'Generating {format_name} video...'
            
            video_path = components['video'].generate_product_video(
                variant_path,
                motion_type=analysis.get('motion_style', 'orbit'),
                quality=product_info['quality']
            )
            
            job_storage[job_id]['progress'] = f'Adding overlay to {format_name}...'
            
            final_video = components['overlay'].add_product_overlay(
                video_path, product_info['name'], product_info['price']
            )
            
            stored_path = components['storage'].save_video(final_video, job_id, format_name)
            
            generated_videos.append({
                'format': format_name,
                'video_path': stored_path,
                'ready': True,
                'download_url': f"/download/{job_id}/{format_name}"
            })
        
        job_storage[job_id].update({
            'status': 'completed',
            'progress': 'All videos generated successfully!',
            'videos': generated_videos,
            'completed_at': datetime.now().isoformat()
        })
        
        os.unlink(temp_path)
        
    except Exception as e:
        job_storage[job_id].update({
            'status': 'failed',
            'progress': f'Error: {str(e)}',
            'error': str(e)
        })

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_storage[job_id]

@app.get("/download/{job_id}/{format}")
async def download_video(job_id: str, format: str):
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_storage[job_id]
    for video in job.get('videos', []):
        if video['format'] == format:
            video_path = video['video_path']
            if os.path.exists(video_path):
                return FileResponse(video_path, media_type='video/mp4')
    
    raise HTTPException(status_code=404, detail="Video not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))