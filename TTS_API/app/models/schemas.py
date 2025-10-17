from typing import List, Optional
from pydantic import BaseModel, Field, root_validator


class TTSRequest(BaseModel):
    text: Optional[str] = Field(None, description="Plain text to synthesize")
    ssml: Optional[str] = Field(None, description="SSML input; mutually exclusive with text")
    language_code: str = Field("ar-XA")
    voice_name: Optional[str] = None
    gender: Optional[str] = Field(None, description="MALE|FEMALE|NEUTRAL")
    audio_encoding: str = Field("MP3", description="MP3|LINEAR16|OGG_OPUS")
    speaking_rate: Optional[float] = Field(None, ge=0.25, le=4.0)
    pitch: Optional[float] = Field(None, ge=-20.0, le=20.0)
    effects_profile_ids: Optional[List[str]] = None
    voice_gender_choice: Optional[str] = Field(
        None, description="male|female; if provided, chooses from preferred two-voice list"
    )

    @root_validator
    def validate_exclusive(cls, values):
        text, ssml = values.get("text"), values.get("ssml")
        if not text and not ssml:
            raise ValueError("Either text or ssml must be provided")
        if text and ssml:
            raise ValueError("Provide only one of text or ssml")
        return values


class TTSResponse(BaseModel):
    file_url: str
    voice_used: str
    language_code: str


class VoicesResponse(BaseModel):
    name: str
    language_codes: List[str]
    gender: str


