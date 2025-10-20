"""
Pydantic models for Orchestrator
Defines all message schemas and data structures
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class MessageType(str, Enum):
    """Message types for WebSocket communication"""
    READY = "ready"
    AUDIO_CHUNK = "audio_chunk"
    AUDIO_END = "audio_end"
    TRANSCRIPT = "transcript"
    RAG_RESPONSE = "rag_response"
    AUDIO_CHUNK_TTS = "audio_chunk_tts"
    COMPLETE = "complete"
    ERROR = "error"
    STATE_UPDATE = "state_update"


class ConversationState(str, Enum):
    """Conversation states"""
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    IDLE = "idle"
    ERROR = "error"


class AudioConfig(BaseModel):
    """Audio configuration for ASR"""
    language_code: str = Field(default="ar-EG", description="Language code for transcription")
    sample_rate_hertz: int = Field(default=16000, description="Audio sample rate")
    encoding: str = Field(default="LINEAR16", description="Audio encoding format")
    channels: int = Field(default=1, description="Number of audio channels")


class TranscriptMessage(BaseModel):
    """Transcription message from ASR"""
    type: MessageType = MessageType.TRANSCRIPT
    text: str = Field(description="Transcribed text")
    is_final: bool = Field(description="Whether this is a final transcription")
    confidence: Optional[float] = Field(default=None, description="Confidence score")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RAGResponseMessage(BaseModel):
    """RAG response message"""
    type: MessageType = MessageType.RAG_RESPONSE
    text: str = Field(description="Generated response text")
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="Source documents")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in milliseconds")
    model_used: Optional[str] = Field(default=None, description="Model used for generation")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AudioChunkMessage(BaseModel):
    """TTS audio chunk message"""
    type: MessageType = MessageType.AUDIO_CHUNK_TTS
    audio_data: bytes = Field(description="Audio data bytes")
    chunk_index: Optional[int] = Field(default=None, description="Chunk index for ordering")
    is_final_chunk: bool = Field(default=False, description="Whether this is the final chunk")
    sentence_index: Optional[int] = Field(default=None, description="Sentence index")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorMessage(BaseModel):
    """Error message"""
    type: MessageType = MessageType.ERROR
    error_code: str = Field(description="Error code")
    detail: str = Field(description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StateMessage(BaseModel):
    """Conversation state update message"""
    type: MessageType = MessageType.STATE_UPDATE
    state: ConversationState = Field(description="Current conversation state")
    previous_state: Optional[ConversationState] = Field(default=None, description="Previous state")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReadyMessage(BaseModel):
    """Ready message sent when client connects"""
    type: MessageType = MessageType.READY
    session_id: str = Field(description="Session identifier")
    audio_config: AudioConfig = Field(description="Audio configuration")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CompleteMessage(BaseModel):
    """Completion message"""
    type: MessageType = MessageType.COMPLETE
    session_id: str = Field(description="Session identifier")
    total_processing_time_ms: Optional[int] = Field(default=None, description="Total processing time")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AudioEndMessage(BaseModel):
    """Message to signal end of audio input"""
    type: MessageType = MessageType.AUDIO_END
    session_id: Optional[str] = Field(default=None, description="Session identifier")


# ASR Client Models
class ASRConfigRequest(BaseModel):
    """ASR configuration request"""
    language_code: str = Field(default="ar-EG")
    sample_rate_hertz: int = Field(default=16000)
    encoding: str = Field(default="LINEAR16")


class ASRTranscriptResponse(BaseModel):
    """ASR transcript response"""
    type: str = Field(description="Message type")
    text: Optional[str] = Field(default=None, description="Transcribed text")
    is_final: Optional[bool] = Field(default=None, description="Whether transcription is final")
    confidence: Optional[float] = Field(default=None, description="Confidence score")


# RAG Client Models
class RAGQueryRequest(BaseModel):
    """RAG query request"""
    query: str = Field(description="User query")
    max_results: int = Field(default=5, description="Maximum number of results")
    include_history: bool = Field(default=True, description="Include conversation history")


class RAGQueryResponse(BaseModel):
    """RAG query response"""
    answer: str = Field(description="Generated answer")
    sources: List[Dict[str, Any]] = Field(description="Source documents")
    processing_time_ms: int = Field(description="Processing time in milliseconds")
    model_used: str = Field(description="Model used for generation")


# TTS Client Models
class TTSRequest(BaseModel):
    """TTS request"""
    text: str = Field(description="Text to synthesize")
    language_code: str = Field(default="ar-XA", description="Language code")
    voice_name: Optional[str] = Field(default=None, description="Specific voice name")
    voice_gender_choice: Optional[str] = Field(default="male", description="Voice gender preference")
    audio_encoding: str = Field(default="MP3", description="Audio encoding format")
    speaking_rate: Optional[float] = Field(default=1.0, description="Speaking rate")
    pitch: Optional[float] = Field(default=0.0, description="Voice pitch")


class TTSMetadataResponse(BaseModel):
    """TTS metadata response"""
    type: str = Field(description="Message type")
    voice_used: Optional[str] = Field(default=None, description="Voice used for synthesis")
    language_code: Optional[str] = Field(default=None, description="Language code used")
    total_chunks: Optional[int] = Field(default=None, description="Total number of chunks")


class TTSCompleteResponse(BaseModel):
    """TTS completion response"""
    type: str = Field(description="Message type")
    successful_chunks: int = Field(description="Number of successful chunks")
    failed_chunks: int = Field(description="Number of failed chunks")


# Session Models
class ConversationTurn(BaseModel):
    """Single conversation turn"""
    user_query: str = Field(description="User's query")
    assistant_response: str = Field(description="Assistant's response")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time")


class SessionData(BaseModel):
    """Session data structure"""
    session_id: str = Field(description="Session identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    conversation_history: List[ConversationTurn] = Field(default_factory=list)
    current_state: ConversationState = Field(default=ConversationState.IDLE)
    audio_config: AudioConfig = Field(default_factory=AudioConfig)


# WebSocket Message Union Type
WebSocketMessage = Union[
    ReadyMessage,
    TranscriptMessage,
    RAGResponseMessage,
    AudioChunkMessage,
    ErrorMessage,
    StateMessage,
    CompleteMessage,
    AudioEndMessage
]
