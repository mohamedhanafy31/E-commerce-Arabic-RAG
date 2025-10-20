# syntax=docker/dockerfile:1

# Base: slim Python 3.10 to match env
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system deps (faiss and common build tools)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    libstdc++6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for better caching
COPY requirements.txt ./

# Install Python deps
# Optional build arg to install CUDA-enabled PyTorch wheels
ARG ENABLE_CUDA=false

RUN pip install --upgrade pip && \
    if [ "$ENABLE_CUDA" = "true" ]; then \
      pip install --extra-index-url https://download.pytorch.org/whl/cu121 \
        torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 && \
      pip install -r requirements.txt; \
    else \
      pip install -r requirements.txt; \
    fi

# Copy app code
COPY . .

# Expose API port
EXPOSE 8000

# Default envs (can be overridden)
ENV RAG_API_HOST=0.0.0.0 \
    RAG_API_PORT=8000 \
    RAG_VECTOR_STORE_PATH=./data/vector_store \
    RAG_DOCUMENTS_PATH=./data/documents \
    RAG_TEMP_PATH=./temp

# Create runtime dirs
RUN mkdir -p ./data/vector_store ./data/documents ./temp

# Healthcheck (optional): FastAPI root
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD curl -f http://localhost:8000/ || exit 1

# Run with uvicorn (reload off in containers)
CMD ["python", "main.py"]


