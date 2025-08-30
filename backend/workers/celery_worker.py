"""
Celery worker for background video processing
Save as: backend/workers/celery_worker.py
"""

from celery import Celery
import os
import sys
import tempfile
from datetime import datetime

# Add backend to path
sys.path.append('/app/backend')

# Configure Celery
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery_app = Celery(
    'video_ad_worker',
    broker=redis_url,
    backend=redis_url,
    include=['backend.workers.celery_worker']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,  # Important for GPU tasks
    task_acks_late=True,
    worker_max_tasks_per_child=1,  # Restart worker after each task to free GPU memory
)

# Import AI components (will be loaded on first use)
video_generator = None
image_processor = None
overlay_processor = None
meta_client = None

def get_ai_components():
    """Initialize AI components (lazy loading)"""
    global video_generator, image_processor, overlay_processor, meta_client
    
    if video_generator is None:
        from models.stable_video_diffusion import LocalVideoGenerator
        from models.image_processor import ImageVariantGenerator
        from utils.video_overlay import VideoOverlayProcessor
        from meta.ads_client import MetaAdsClient
        
        print("🤖 Initializing AI components in worker...")
        video_generator = LocalVideoGenerator()
        image_processor = ImageVariantGenerator()
        overlay_processor = VideoOverlayProcessor()
        meta_client = MetaAdsClient()
        print("✅ Worker AI components ready!")

@celery_app.task(bind=True, name='create_video_ad_task')
def create_video_ad_task(self, job_id: str, image_data: bytes, product_info: dict):
    """
    Main Celery task to create video ads
    
    Args:
        job_id: Unique job identifier
        image_data: Raw image bytes
        product_info: Product details (name, price, url, description, quality)
    """
    
    print(f"🚀 Starting video generation for job {job_id}")
    
    try:
        # Initialize AI components
        get_ai_components()
        
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={
                'step': 'initializing', 
                'progress': 10,
                'message': 'AI models loaded'
            }
        )
        
        # Step 1: Save temporary image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_img:
            temp_img.write(image_data)
            temp_img_path = temp_img.name
        
        print(f"💾 Saved temp image: {temp_img_path}")
        
        # Step 2: Generate image variants
        self.update_state(
            state='PROGRESS',
            meta={
                'step': 'generating_variants',
                'progress': 20,
                'message': 'Creating image variants for different formats'
            }
        )
        
        variants = image_processor.generate_variants(temp_img_path)
        print(f"🖼️  Generated {len(variants)} image variants")
        
        # Step 3: Generate videos for each variant
        generated_videos = []
        total_variants = len(variants)
        
        for i, (format_name, variant_path) in enumerate(variants.items()):
            progress = 30 + (i * 40 // total_variants)  # 30-70% progress
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'step': f'generating_video_{format_name}',
                    'progress': progress,
                    'message': f'Generating {format_name} video with AI...'
                }
            )
            
            print(f"🎥 Generating video for {format_name}...")
            
            # Generate video with local AI
            video_path = video_generator.generate_product_video(
                variant_path,
                motion_type="orbit",  # Could be dynamic based on product analysis
                quality=product_info.get('quality', 'fast'),
                seed=42  # Consistent results
            )
            
            # Add text overlay
            self.update_state(
                state='PROGRESS', 
                meta={
                    'step': f'adding_overlay_{format_name}',
                    'progress': progress + 5,
                    'message': f'Adding text overlay to {format_name} video...'
                }
            )
            
            final_video = overlay_processor.add_product_overlay(
                video_path,
                product_info['name'],
                product_info['price'],
                style="modern"
            )
            
            generated_videos.append({
                'format': format_name,
                'video_path': final_video,
                'ready': True,
                'size_mb': round(os.path.getsize(final_video) / (1024*1024), 2)
            })
            
            print(f"✅ {format_name} video completed")
            
            # Clean up temporary files
            if os.path.exists(video_path):
                os.unlink(video_path)
            if os.path.exists(variant_path):
                os.unlink(variant_path)
        
        # Step 4: Meta Ads integration
        self.update_state(
            state='PROGRESS',
            meta={
                'step': 'meta_integration',
                'progress': 80,
                'message': 'Creating Meta ad creative...'
            }
        )
        
        try:
            meta_result = meta_client.create_ad_creative(
                videos=generated_videos,
                product_info=product_info
            )
            print(f"📘 Meta creative created: {meta_result['creative_id']}")
        except Exception as e:
            print(f"⚠️  Meta integration failed: {e}")
            # Continue without Meta integration
            meta_result = {
                'creative_id': None,
                'status': 'meta_failed',
                'error': str(e)
            }
        
        # Step 5: Final cleanup
        self.update_state(
            state='PROGRESS',
            meta={
                'step': 'finalizing',
                'progress': 95,
                'message': 'Finalizing and cleaning up...'
            }
        )
        
        # Clean up original temp image
        if os.path.exists(temp_img_path):
            os.unlink(temp_img_path)
        
        # Calculate total processing time
        processing_time = datetime.now().isoformat()
        
        print(f"🎉 Job {job_id} completed successfully!")
        
        return {
            'status': 'completed',
            'job_id': job_id,
            'videos': generated_videos,
            'meta_creative_id': meta_result.get('creative_id'),
            'meta_status': meta_result.get('status'),
            'ad_preview_url': meta_result.get('preview_urls', {}).get('feed'),
            'completed_at': processing_time,
            'total_videos': len(generated_videos)
        }
        
    except Exception as e:
        print(f"❌ Job {job_id} failed: {str(e)}")
        
        # Clean up any temporary files
        try:
            if 'temp_img_path' in locals() and os.path.exists(temp_img_path):
                os.unlink(temp_img_path)
        except:
            pass
        
        return {
            'status': 'failed',
            'job_id': job_id,
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        }

@celery_app.task(name='cleanup_task')
def cleanup_old_files():
    """Periodic cleanup of old generated files"""
    
    from utils.storage import LocalStorage
    
    storage = LocalStorage()
    cleaned_count = storage.cleanup_old_files(days_old=7)
    
    return {
        'status': 'completed',
        'files_cleaned': cleaned_count,
        'cleanup_date': datetime.now().isoformat()
    }

@celery_app.task(name='health_check_task')
def health_check():
    """Worker health check"""
    
    return {
        'status': 'healthy',
        'worker_id': os.getpid(),
        'gpu_available': torch.cuda.is_available() if 'torch' in globals() else False,
        'timestamp': datetime.now().isoformat()
    }

if __name__ == '__main__':
    # Start worker
    celery_app.start()