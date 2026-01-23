FROM ultralytics/ultralytics:latest-cpu

WORKDIR /app

# Copy and install only the necessary requirements
# ultralytics, opencv-python, and their heavy dependencies are already in the base image
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy YOLO model (cached layer if model doesn't change)
COPY yolov8n.pt /app/yolov8n.pt

# Copy application code
COPY . .

# Expose port
EXPOSE 8004

# Health check - updated to use curl and the /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8004/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
