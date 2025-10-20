from pydantic_settings import BaseSettings
from typing import Optional
import os


ENV_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


class Settings(BaseSettings):
    app_name: str = "ASR API"
    log_level: str = os.getenv("LOG_LEVEL", "info")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8001"))
    reload: bool = os.getenv("RELOAD", "true").lower() == "true"
    audio_dir: str = os.getenv("AUDIO_DIR", "data/audio")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    api_key: Optional[str] = os.getenv("API_KEY")
    google_application_credentials: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # ASR specific settings
    default_language_code: str = os.getenv("DEFAULT_LANGUAGE_CODE", "ar-EG")
    default_chunk_duration: float = float(os.getenv("DEFAULT_CHUNK_DURATION", "0.5"))
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    enable_preprocessing: bool = os.getenv("ENABLE_PREPROCESSING", "true").lower() == "true"
    enable_word_timestamps: bool = os.getenv("ENABLE_WORD_TIMESTAMPS", "true").lower() == "true"
    
    # Streaming ASR specific settings
    default_sample_rate_hertz: int = int(os.getenv("DEFAULT_SAMPLE_RATE_HERTZ", "16000"))
    streaming_interim_results: bool = os.getenv("STREAMING_INTERIM_RESULTS", "true").lower() == "true"
    enable_automatic_punctuation: bool = os.getenv("ENABLE_AUTOMATIC_PUNCTUATION", "true").lower() == "true"

    class Config:
        # Resolve .env relative to the project root (ASR_API/.env), regardless of CWD
        env_file = ENV_FILE_PATH
        env_file_encoding = "utf-8"


settings = Settings()
