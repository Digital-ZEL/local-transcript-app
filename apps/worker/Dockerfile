# Worker Service Dockerfile
# =========================
# Local Transcript App - Transcription Worker
#
# Supports both CPU and GPU (NVIDIA CUDA)

# Use NVIDIA CUDA base for GPU support, or python:3.11-slim for CPU-only
ARG BASE_IMAGE=python:3.11-slim

FROM ${BASE_IMAGE}

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash worker
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set ownership
RUN chown -R worker:worker /app

# Switch to non-root user
USER worker

# Create data directories
RUN mkdir -p /app/data/uploads /app/data/outputs /app/data/youtube_temp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import faster_whisper; print('OK')" || exit 1

# Default command
CMD ["python", "main.py"]
