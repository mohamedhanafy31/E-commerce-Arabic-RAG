from pydantic import BaseSettings, AnyHttpUrl
from typing import List, Optional
import os


class Settings(BaseSettings):
    app_name: str = "TTS API"
    log_level: str = os.getenv("LOG_LEVEL", "info")
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
        env_file = ".env"


settings = Settings()

def get_preferred_voice_list() -> list[str]:
    raw = settings.preferred_voice_names or ""
    items = [s.strip() for s in raw.split(",") if s.strip()]
    return items


