"""
Configuration module for Orchestrator
Handles all configuration settings for the conversational system
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Configuration settings for the Orchestrator"""
    
    # Application Configuration
    app_name: str = "Orchestrator Conversational System"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server Configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8004"))
    reload: bool = os.getenv("RELOAD", "true").lower() == "true"
    
    # Service URLs
    asr_service_url: str = os.getenv("ASR_SERVICE_URL", "ws://localhost:8001")
    rag_service_url: str = os.getenv("RAG_SERVICE_URL", "http://localhost:8002")
    tts_service_url: str = os.getenv("TTS_SERVICE_URL", "ws://localhost:8003")
    
    # Audio Configuration
    audio_sample_rate: int = int(os.getenv("AUDIO_SAMPLE_RATE", "48000"))
    audio_channels: int = int(os.getenv("AUDIO_CHANNELS", "1"))
    audio_format: str = os.getenv("AUDIO_FORMAT", "OGG_OPUS")
    audio_chunk_size: int = int(os.getenv("AUDIO_CHUNK_SIZE", "1024"))
    
    # Language Configuration
    default_language_code: str = os.getenv("DEFAULT_LANGUAGE_CODE", "ar-EG")
    tts_language_code: str = os.getenv("TTS_LANGUAGE_CODE", "ar-XA")
    tts_voice_gender: str = os.getenv("TTS_VOICE_GENDER", "male")
    
    # Session Configuration
    max_session_history: int = int(os.getenv("MAX_SESSION_HISTORY", "10"))
    session_timeout_seconds: int = int(os.getenv("SESSION_TIMEOUT_SECONDS", "300"))
    max_concurrent_sessions: int = int(os.getenv("MAX_CONCURRENT_SESSIONS", "100"))
    
    # Timeout Configuration
    asr_timeout_seconds: int = int(os.getenv("ASR_TIMEOUT_SECONDS", "30"))
    rag_timeout_seconds: int = int(os.getenv("RAG_TIMEOUT_SECONDS", "60"))
    tts_timeout_seconds: int = int(os.getenv("TTS_TIMEOUT_SECONDS", "30"))
    websocket_timeout_seconds: int = int(os.getenv("WEBSOCKET_TIMEOUT_SECONDS", "300"))
    
    # Retry Configuration
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    retry_delay_seconds: float = float(os.getenv("RETRY_DELAY_SECONDS", "1.0"))
    exponential_backoff: bool = os.getenv("EXPONENTIAL_BACKOFF", "true").lower() == "true"
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "%(asctime)s %(levelname)s [%(name)s] %(message)s")
    
    # CORS Configuration
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    cors_allow_credentials: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    
    # Audio Processing Configuration
    silence_detection_threshold: float = float(os.getenv("SILENCE_DETECTION_THRESHOLD", "0.1"))
    silence_duration_seconds: float = float(os.getenv("SILENCE_DURATION_SECONDS", "2.0"))
    max_audio_duration_seconds: int = int(os.getenv("MAX_AUDIO_DURATION_SECONDS", "60"))
    
    # Performance Configuration
    enable_audio_preprocessing: bool = os.getenv("ENABLE_AUDIO_PREPROCESSING", "true").lower() == "true"
    enable_sentence_streaming: bool = os.getenv("ENABLE_SENTENCE_STREAMING", "true").lower() == "true"
    enable_conversation_history: bool = os.getenv("ENABLE_CONVERSATION_HISTORY", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings
