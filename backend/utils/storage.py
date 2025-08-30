"""
Local storage handler for videos and images
Save as: backend/utils/storage.py
"""

import os
import shutil
from datetime import datetime
from typing import Optional
import uuid

class LocalStorage:
    def __init__(self):
        self.base_dir = os.getenv('LOCAL_STORAGE_PATH', './generated_videos')
        self.ensure_directories()
        
        print(f"💾 Storage initialized at: {self.base_dir}")
    
    def ensure_directories(self):
        """Create necessary storage directories"""
        
        directories = [
            self.base_dir,
            os.path.join(self.base_dir, 'videos'),
            os.path.join(self.base_dir, 'images'),
            os.path.join(self.base_dir, 'temp')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def save_video(self, video_path: str, job_id: str, format_name: str) -> str:
        """Save video to permanent storage"""
        
        # Generate permanent filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{job_id}_{format_name}_{timestamp}.mp4"
        
        # Destination path
        dest_path = os.path.join(self.base_dir, 'videos', filename)
        
        # Copy video to permanent storage
        shutil.copy2(video_path, dest_path)
        
        # Remove temporary file
        if os.path.exists(video_path):
            os.unlink(video_path)
        
        print(f"💾 Video saved: {dest_path}")
        return dest_path
    
    def save_image(self, image_path: str, job_id: str, variant_name: str) -> str:
        """Save image variant to permanent storage"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{job_id}_{variant_name}_{timestamp}.jpg"
        
        dest_path = os.path.join(self.base_dir, 'images', filename)
        shutil.copy2(image_path, dest_path)
        
        return dest_path
    
    def cleanup_old_files(self, days_old: int = 7):
        """Clean up files older than specified days"""
        
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)
        
        cleaned_count = 0
        
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check file age
                if os.path.getctime(file_path) < cutoff_time:
                    try:
                        os.unlink(file_path)
                        cleaned_count += 1
                    except Exception as e:
                        print(f"⚠️  Could not delete {file_path}: {e}")
        
        print(f"🧹 Cleaned up {cleaned_count} old files")
        return cleaned_count
    
    def get_storage_info(self) -> dict:
        """Get storage usage information"""
        
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        return {
            'total_files': file_count,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'storage_path': self.base_dir
        }