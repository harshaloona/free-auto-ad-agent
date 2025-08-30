FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Create necessary directories
RUN mkdir -p models_cache generated_videos temp_uploads

# Set environment variables
ENV PYTHONPATH=/app
ENV TORCH_HOME=/app/models_cache

# Expose port for Railway
EXPOSE 8000

# Start command
CMD ["python", "backend/main.py"]
