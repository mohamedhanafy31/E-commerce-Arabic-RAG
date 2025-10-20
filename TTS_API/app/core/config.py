from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List, Optional
import os


ENV_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


class Settings(BaseSettings):
    app_name: str = "TTS API"
    log_level: str = os.getenv("LOG_LEVEL", "info")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8003"))
    reload: bool = os.getenv("RELOAD", "true").lower() == "true"
    audio_dir: str = os.getenv("AUDIO_DIR", "/data/audio")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    api_key: Optional[str] = os.getenv("API_KEY")
    google_application_credentials: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    preferred_voice_names: Optional[str] = os.getenv(
        "PREFERRED_VOICE_NAMES",
        "ar-XA-Chirp3-HD-Algenib,ar-XA-Chirp3-HD-Despina",
    )

    class Config:
        # Resolve .env relative to the project root (TTS_API/.env), regardless of CWD
        env_file = ENV_FILE_PATH
        env_file_encoding = "utf-8"


settings = Settings()

def get_preferred_voice_list() -> list[str]:
    raw = settings.preferred_voice_names or ""
    items = [s.strip() for s in raw.split(",") if s.strip()]
    return items


