
FROM python:3.10-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install minimal requirements first
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p models_cache generated_videos temp_uploads

# Set environment variables
ENV PYTHONPATH=/app
ENV TORCH_HOME=/app/models_cache

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "backend/main.py"]
