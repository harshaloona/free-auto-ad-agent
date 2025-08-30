# Environment configuration for Free AI Video Ad Generator
# Save as: .env.example
# Copy this to .env and fill in your values

# =============================================================================
# AI MODEL SETTINGS
# =============================================================================

# Device for PyTorch (cuda for GPU, cpu for CPU only)
TORCH_DEVICE=cuda

# Model cache directory (where downloaded models are stored)
MODEL_CACHE_DIR=./models_cache

# Video generation quality (fast=30s, balanced=2min, high=5min per video)
VIDEO_QUALITY=fast

# Batch size for processing (lower = less memory usage)
BATCH_SIZE=1

# =============================================================================
# META ADS INTEGRATION (Optional - for publishing ads)
# =============================================================================

# Meta long-lived access token (from Facebook Developer Console)
META_ACCESS_TOKEN=your_long_lived_access_token_here

# Your Meta Ad Account ID (found in Meta Ads Manager, format: act_1234567890)
META_AD_ACCOUNT_ID=act_your_account_id_here

# Your Facebook Page ID (found in Page Settings)
META_PAGE_ID=your_page_id_here

# Your Instagram Business Account ID
META_INSTAGRAM_ACTOR_ID=your_instagram_id_here

# Sandbox mode (true = test mode, false = real ads with budget)
META_SANDBOX_MODE=true

# Default daily budget for ads (in cents, 1000 = $10.00)
DEFAULT_AD_BUDGET=1000

# =============================================================================
# STORAGE SETTINGS
# =============================================================================

# Storage type (local for testing, s3 for production)
STORAGE_TYPE=local

# Local storage path for generated videos
LOCAL_STORAGE_PATH=./generated_videos

# S3 settings (optional, for production)
S3_BUCKET=your-bucket-name
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_ENDPOINT=https://s3.amazonaws.com
S3_REGION=us-east-1

# =============================================================================
# DATABASE & QUEUE SETTINGS
# =============================================================================

# Redis URL (for task queue)
REDIS_URL=redis://localhost:6379/0

# PostgreSQL URL (for metadata storage)
DATABASE_URL=postgresql://user:password@localhost:5432/adagent

# =============================================================================
# SERVER SETTINGS
# =============================================================================

# Server host and port
HOST=0.0.0.0
PORT=8000

# Debug mode (true for development)
DEBUG=false

# Max file upload size (in MB)
MAX_UPLOAD_SIZE=10

# =============================================================================
# PERFORMANCE TUNING
# =============================================================================

# Number of inference steps for video generation
# Lower = faster, Higher = better quality
INFERENCE_STEPS_FAST=15
INFERENCE_STEPS_BALANCED=25
INFERENCE_STEPS_HIGH=35

# Guidance scale (how closely to follow the prompt)
GUIDANCE_SCALE_FAST=3.0
GUIDANCE_SCALE_BALANCED=7.5
GUIDANCE_SCALE_HIGH=12.0

# Video frame count (more frames = longer videos but slower processing)
VIDEO_FRAMES=14

# Enable memory optimizations (recommended for GPUs with <12GB VRAM)
ENABLE_CPU_OFFLOAD=true
ENABLE_VAE_SLICING=true
ENABLE_ATTENTION_SLICING=true

# =============================================================================
# LOGGING & MONITORING
# =============================================================================

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Enable performance monitoring
ENABLE_MONITORING=true

# =============================================================================
# FEATURE FLAGS
# =============================================================================

# Enable experimental features
ENABLE_BATCH_PROCESSING=false
ENABLE_CUSTOM_MOTIONS=false
ENABLE_AUTO_ENHANCEMENT=true

# =============================================================================
# RAILWAY SPECIFIC SETTINGS (Auto-detected when deployed)
# =============================================================================

# Railway automatically provides these:
# RAILWAY_ENVIRONMENT=production
# RAILWAY_SERVICE_NAME=backend
# PORT=8000 (Railway sets this automatically)