# TTS API - Optimized Multi-Stage Build Dockerfile
# Stage 1: Base image with dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies including uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies using uv
RUN uv pip install --system -r requirements.txt

# Stage 2: Final runtime image
FROM base as runtime

# Copy application code (this layer changes frequently)
COPY . .

# Create directories and set permissions
RUN mkdir -p /data/audio /app/data/audio /app/logs && \
    chmod 755 /data/audio /app/data/audio /app/logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash ttsuser && \
    chown -R ttsuser:ttsuser /app /data

# Ensure credentials file has correct permissions for the user
RUN if [ -f /app/tts-key.json ]; then \
        chmod 644 /app/tts-key.json && \
        chown ttsuser:ttsuser /app/tts-key.json && \
        echo "✅ Credentials file permissions set successfully"; \
    else \
        echo "⚠️  tts-key.json not found in /app"; \
    fi

USER ttsuser

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the application
CMD ["python", "run.py"]