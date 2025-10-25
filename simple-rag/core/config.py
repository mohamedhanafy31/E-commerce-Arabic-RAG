"""
Configuration module for Simple Arabic RAG System
"""

import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config(BaseModel):
    """Configuration settings for the RAG system"""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    
    # Model Configuration
    embedding_model: str = "NAMAA-Space/AraModernBert-Base-V1.0"
    generation_model: str = "gemini"  # Only Gemini supported
    
    # GPU Configuration
    force_gpu: bool = True  # Force GPU usage as per user rules
    gpu_device: str = "cuda"  # GPU device to use
    fallback_to_cpu: bool = True  # Fallback to CPU if GPU fails
    
    # Gemini Configuration
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    gemini_model: str = "gemini-2.5-flash"
    
    # Hugging Face Configuration
    hf_token: Optional[str] = os.getenv("HF_TOKEN")
    
    # Storage Configuration
    vector_store_path: str = "./data/vector_store"
    documents_path: str = "./data/documents"
    temp_path: str = "./temp"
    
    # Chunking Configuration
    sentences_per_chunk: int = 7
    sentence_overlap: int = 5
    
    # Retrieval Configuration
    max_results: int = 5
    similarity_threshold: float = 0.7
    
    # Generation Configuration
    max_tokens: int = 1024
    temperature: float = 0.3
    
    # File Processing Configuration
    max_file_size_mb: int = 10
    allowed_extensions: set = {'.txt', '.pdf', '.docx', '.md'}
    
    class Config:
        env_prefix = "RAG_"


# Global config instance
config = Config()

# Create necessary directories
os.makedirs(config.vector_store_path, exist_ok=True)
os.makedirs(config.documents_path, exist_ok=True)
os.makedirs(config.temp_path, exist_ok=True)
