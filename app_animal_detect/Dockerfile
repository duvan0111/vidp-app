FROM python:3.10-slim

# Install system dependencies including FFmpeg and OpenCV dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy YOLO model (cached layer if model doesn't change)
COPY yolov8n.pt /app/yolov8n.pt

# Copy application code
COPY . .

# Note: No persistent directories needed - uses temporary files only

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8004/')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
