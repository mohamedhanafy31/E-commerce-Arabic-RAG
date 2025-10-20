import hashlib
import re
from datetime import datetime


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def build_audio_filename(voice_name: str, text: str, extension: str = "mp3") -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    base = f"{timestamp}_{sanitize_filename(voice_name)}_{text_hash}.{extension}"
    return base


