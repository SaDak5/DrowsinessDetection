# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and other libraries
RUN apt-get update && apt-get install -y \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY templates/ ./templates/
COPY models/ ./models/

# Set environment variables
ENV PORT=8080
ENV TF_CPP_MIN_LOG_LEVEL=3
ENV MODEL_PATH=models/best_model_mobilenetv2.h5
ENV THRESHOLD=0.5

# Run Flask app with Gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --worker-class gthread --threads 2 --timeout 600 main:app
