# RAG System - Optimized Multi-Stage Build Dockerfile
# Stage 1: Base image with dependencies and model
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies including uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    curl \
    libstdc++6 \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies using uv
# Optional build arg to install CUDA-enabled PyTorch wheels
ARG ENABLE_CUDA=false

RUN if [ "$ENABLE_CUDA" = "true" ]; then \
      uv pip install --system --extra-index-url https://download.pytorch.org/whl/cu121 \
        torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 && \
      uv pip install --system -r requirements.txt; \
    else \
      uv pip install --system -r requirements.txt; \
    fi

# Stage 2: Final runtime image
FROM base as runtime

# Copy application code (this layer changes frequently)
COPY . .

# Pre-download the Arabic BERT model during build to avoid runtime rate limiting
# This ensures the model is available in the runtime stage
# Use Hugging Face token for authentication
ARG HF_TOKEN
RUN python -c "import os; os.environ['HF_TOKEN'] = '$HF_TOKEN'; from sentence_transformers import SentenceTransformer; SentenceTransformer('NAMAA-Space/AraModernBert-Base-V1.0')"

# Create directories and set permissions
RUN mkdir -p /app/data/vector_store /app/data/documents /app/temp /app/logs && \
    chmod 755 /app/data/vector_store /app/data/documents /app/temp /app/logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash raguser && \
    chown -R raguser:raguser /app
USER raguser

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["python", "main.py"]