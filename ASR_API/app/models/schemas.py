from typing import List, Optional
from pydantic import BaseModel, Field


class WordInfo(BaseModel):
    """Word-level timestamp information"""
    word: str
    start_time: float
    end_time: float
    confidence: Optional[float] = None


class ASRRequest(BaseModel):
    """Request model for ASR transcription"""
    language_code: str = Field("ar-EG", description="Language code for transcription")
    chunk_duration_minutes: float = Field(0.5, ge=0.1, le=5.0, description="Chunk duration in minutes")
    enable_preprocessing: bool = Field(True, description="Enable audio preprocessing")
    enable_word_timestamps: bool = Field(True, description="Enable word-level timestamps")


class ASRResponse(BaseModel):
    """Response model for ASR transcription"""
    transcript: str
    confidence: float
    language_code: str
    processing_time: float
    chunks_processed: int
    words: Optional[List[WordInfo]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str = "ASR API"
    version: str = "1.0.0"


class StreamingConfigRequest(BaseModel):
    """WebSocket streaming configuration request"""
    language_code: str = "ar-EG"
    sample_rate_hertz: int = 16000
    encoding: str = "LINEAR16"


class StreamingTranscriptResponse(BaseModel):
    """WebSocket streaming transcript response"""
    type: str
    text: Optional[str] = None
    is_final: bool
    confidence: Optional[float] = None


class StreamingErrorResponse(BaseModel):
    """WebSocket streaming error response"""
    type: str = "error"
    detail: str


class StreamingCompleteResponse(BaseModel):
    """WebSocket streaming completion response"""
    type: str = "complete"
