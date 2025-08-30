"""
Video text overlay processor
Save as: backend/utils/video_overlay.py
"""

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
import os
import tempfile
from typing import Optional, Tuple, Dict

class VideoOverlayProcessor:
    def __init__(self):
        self.font_path = self._get_font_path()
        self.temp_dir = tempfile.mkdtemp()
        
        print(f"🎨 Video overlay processor initialized")
        print(f"📝 Using font: {self.font_path}")
    
    def add_product_overlay(
        self, 
        video_path: str, 
        product_name: str, 
        price: str,
        style: str = "modern",
        brand_color: str = "#FF6B35"
    ) -> str:
        """
        Add text overlay to generated video
        
        Args:
            video_path: Path to source video
            product_name: Product name to display
            price: Price to display
            style: Overlay style (modern, minimal, premium, bold)
            brand_color: Brand accent color (hex)
            
        Returns:
            Path to video with overlay
        """
        
        print(f"🎬 Adding {style} overlay to video...")
        
        # Load video
        video = VideoFileClip(video_path)
        
        # Generate overlay elements based on style
        overlay_clips = self._create_overlay_clips(
            video, product_name, price, style, brand_color
        )
        
        # Compose final video
        final_clips = [video] + overlay_clips
        final_video = CompositeVideoClip(final_clips)
        
        # Export with social media optimization
        output_path = self._export_video(final_video, video_path, style)
        
        # Clean up
        video.close()
        final_video.close()
        
        print(f"✅ Overlay added: {output_path}")
        return output_path
    
    def _create_overlay_clips(
        self, 
        video: VideoFileClip, 
        product_name: str, 
        price: str,
        style: str,
        brand_color: str
    ) -> list:
        """Create text and graphic overlay clips"""
        
        duration = video.duration
        width, height = video.size
        
        if style == "modern":
            return self._modern_style_overlay(
                product_name, price, duration, width, height, brand_color
            )
        elif style == "minimal":
            return self._minimal_style_overlay(
                product_name, price, duration, width, height
            )
        elif style == "premium":
            return self._premium_style_overlay(
                product_name, price, duration, width, height, brand_color
            )
        elif style == "bold":
            return self._bold_style_overlay(
                product_name, price, duration, width, height, brand_color
            )
        else:
            return self._modern_style_overlay(
                product_name, price, duration, width, height, brand_color
            )
    
    def _modern_style_overlay(self, product_name: str, price: str, duration: float, width: int, height: int, brand_color: str) -> list:
        """Modern style with background bars and clean typography"""
        
        clips = []
        
        # Product name with background
        name_bg = ColorClip(
            size=(width, 80), 
            color=(0, 0, 0),
            duration=duration
        ).set_position(('center', height * 0.75)).set_opacity(0.7)
        
        name_text = TextClip(
            product_name,
            fontsize=min(60, width // 15),
            color='white',
            font='Arial-Bold' if os.path.exists('/System/Library/Fonts/Arial.ttf') else 'Arial'
        ).set_position(('center', height * 0.75 + 15)).set_duration(duration)
        
        # Price with accent color
        price_text = TextClip(
            price,
            fontsize=min(48, width // 20),
            color=brand_color,
            font='Arial-Bold' if os.path.exists('/System/Library/Fonts/Arial.ttf') else 'Arial'
        ).set_position(('center', height * 0.85)).set_duration(duration)
        
        # Shop now call-to-action
        cta_text = TextClip(
            "TAP TO SHOP",
            fontsize=min(32, width // 30),
            color='white',
            font='Arial'
        ).set_position(('center', height * 0.92)).set_duration(duration)
        
        clips.extend([name_bg, name_text, price_text, cta_text])
        return clips
    
    def _minimal_style_overlay(self, product_name: str, price: str, duration: float, width: int, height: int) -> list:
        """Minimal style with bottom text only"""
        
        clips = []
        
        # Single line at bottom
        text_content = f"{product_name} • {price}"
        
        # Semi-transparent background
        text_bg = ColorClip(
            size=(width, 60),
            color=(0, 0, 0),
            duration=duration
        ).set_position((0, height - 60)).set_opacity(0.5)
        
        # Clean white text
        text_clip = TextClip(
            text_content,
            fontsize=min(36, width // 25),
            color='white',
            font='Arial'
        ).set_position(('center', height - 40)).set_duration(duration)
        
        clips.extend([text_bg, text_clip])
        return clips
    
    def _premium_style_overlay(self, product_name: str, price: str, duration: float, width: int, height: int, brand_color: str) -> list:
        """Premium style with elegant typography and effects"""
        
        clips = []
        
        # Elegant gradient background for text
        gradient_height = 120
        gradient_bg = ColorClip(
            size=(width, gradient_height),
            color=(20, 20, 20),
            duration=duration
        ).set_position((0, height - gradient_height)).set_opacity(0.8)
        
        # Product name with serif font feel
        name_text = TextClip(
            product_name,
            fontsize=min(52, width // 18),
            color='#F5F5F5',
            font='Arial'  # Would use serif if available
        ).set_position(('center', height - 90)).set_duration(duration)
        
        # Price with gold color
        price_text = TextClip(
            price,
            fontsize=min(42, width // 22),
            color='#FFD700',  # Gold
            font='Arial'
        ).set_position(('center', height - 50)).set_duration(duration)
        
        # Subtle "EXCLUSIVE" tag
        exclusive_text = TextClip(
            "SHOP EXCLUSIVE",
            fontsize=min(24, width // 35),
            color='#CCCCCC',
            font='Arial'
        ).set_position(('center', height - 20)).set_duration(duration)
        
        clips.extend([gradient_bg, name_text, price_text, exclusive_text])
        return clips
    
    def _bold_style_overlay(self, product_name: str, price: str, duration: float, width: int, height: int, brand_color: str) -> list:
        """Bold style with large text and strong colors"""
        
        clips = []
        
        # Large bold product name
        name_text = TextClip(
            product_name.upper(),
            fontsize=min(72, width // 12),
            color=brand_color,
            font='Arial-Bold' if os.path.exists('/System/Library/Fonts/Arial.ttf') else 'Arial'
        ).set_position(('center', height * 0.7)).set_duration(duration)
        
        # Bold price with contrasting background
        price_bg = ColorClip(
            size=(len(price) * 40, 60),
            color=tuple(int(brand_color[i:i+2], 16) for i in (1, 3, 5)),  # Convert hex to RGB
            duration=duration
        ).set_position(('center', height * 0.82)).set_opacity(0.9)
        
        price_text = TextClip(
            price,
            fontsize=min(56, width // 16),
            color='white',
            font='Arial-Bold' if os.path.exists('/System/Library/Fonts/Arial.ttf') else 'Arial'
        ).set_position(('center', height * 0.82 + 5)).set_duration(duration)
        
        # Call to action
        cta_text = TextClip(
            "🔥 GET YOURS NOW",
            fontsize=min(38, width // 25),
            color='white',
            font='Arial-Bold' if os.path.exists('/System/Library/Fonts/Arial.ttf') else 'Arial'
        ).set_position(('center', height * 0.93)).set_duration(duration)
        
        clips.extend([name_text, price_bg, price_text, cta_text])
        return clips
    
    def _export_video(self, final_video: CompositeVideoClip, original_path: str, style: str) -> str:
        """Export video with social media optimized settings"""
        
        # Generate output filename
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        output_filename = f"{base_name}_{style}_overlay.mp4"
        output_path = os.path.join("generated_videos", output_filename)
        
        # Ensure output directory exists
        os.makedirs("generated_videos", exist_ok=True)
        
        # Export with optimized settings for social media
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac' if final_video.audio else None,
            temp_audiofile='temp-audio.m4a' if final_video.audio else None,
            remove_temp=True,
            fps=30,
            preset='medium',  # Good balance of quality/speed
            ffmpeg_params=['-crf', '23']  # Good quality compression
        )
        
        return output_path
    
    def _get_font_path(self) -> Optional[str]:
        """Get system font path"""
        import platform
        
        system = platform.system()
        
        font_paths = {
            "Windows": [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf"
            ],
            "Darwin": [  # macOS
                "/System/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc"
            ],
            "Linux": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/TTF/arial.ttf"
            ]
        }
        
        # Try to find available font
        for font_path in font_paths.get(system, []):
            if os.path.exists(font_path):
                return font_path
        
        # Fallback to system default
        return None
    
    def add_animated_elements(self, video_path: str, animation_type: str = "fade_in") -> str:
        """Add animated elements to video (optional enhancement)"""
        
        video = VideoFileClip(video_path)
        
        if animation_type == "fade_in":
            # Fade in text elements
            video = video.fadein(0.5)
        elif animation_type == "zoom_effect":
            # Add slight zoom effect
            video = video.resize(lambda t: 1 + 0.02 * t)
        
        # Export with animation
        output_path = video_path.replace('.mp4', '_animated.mp4')
        video.write_videofile(
            output_path,
            codec='libx264',
            fps=30,
            preset='fast'
        )
        
        video.close()
        return output_path