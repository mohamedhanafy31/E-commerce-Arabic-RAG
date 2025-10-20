import os
import tempfile
import logging
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from typing import Optional

from ..models.schemas import (
    ASRRequest, ASRResponse, HealthResponse, StreamingConfigRequest
)
from ..services.gcp_asr import ASRProcessor, get_asr_service, ASRError, AudioProcessingError, TranscriptionError
from ..services.streaming_asr import StreamingASRProcessor, get_streaming_asr_service, StreamingASRError
from ..core.config import settings

router = APIRouter()
logger = logging.getLogger("asr")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(status="ok")


@router.post("/asr", response_model=ASRResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language_code: str = Form(default="ar-EG", description="Language code for transcription"),
    chunk_duration_minutes: float = Form(default=0.5, ge=0.1, le=5.0, description="Chunk duration in minutes"),
    enable_preprocessing: bool = Form(default=True, description="Enable audio preprocessing"),
    enable_word_timestamps: bool = Form(default=True, description="Enable word-level timestamps"),
    asr_service: ASRProcessor = Depends(get_asr_service)
) -> ASRResponse:
    """
    Transcribe an uploaded audio file
    
    Args:
        file: Audio file to transcribe
        language_code: Language code for transcription
        chunk_duration_minutes: Duration of each chunk in minutes
        enable_preprocessing: Whether to preprocess audio
        enable_word_timestamps: Whether to include word-level timestamps
        asr_service: ASR processor service
        
    Returns:
        ASRResponse with transcription results
    """
    logger.info(f"📁 Received audio file: {file.filename}")
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=413,
            detail={
                "error": f"File too large ({file_size_mb:.2f} MB)",
                "max_size_mb": settings.max_file_size_mb,
                "solutions": [
                    "Install ffmpeg for audio chunking",
                    f"Use files smaller than {settings.max_file_size_mb}MB",
                    "Split audio before uploading"
                ]
            }
        )
    
    # Save uploaded file to temporary location
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
    try:
        temp_file.write(file_content)
        temp_file.close()
        
        # Process the audio file
        result = asr_service.process_audio_file(
            audio_file_path=temp_file.name,
            language_code=language_code,
            chunk_duration_minutes=chunk_duration_minutes,
            enable_preprocessing=enable_preprocessing,
            enable_word_timestamps=enable_word_timestamps
        )
        
        return ASRResponse(
            transcript=result['transcript'],
            confidence=result['confidence'],
            language_code=result['language_code'],
            processing_time=result['processing_time'],
            chunks_processed=result['chunks_processed'],
            words=result['words']
        )
        
    except AudioProcessingError as e:
        logger.error(f"❌ Audio processing error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Audio processing error: {str(e)}")
    except TranscriptionError as e:
        logger.error(f"❌ Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")
    except ASRError as e:
        logger.error(f"❌ ASR error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ASR error: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Cleanup temporary file
        try:
            os.unlink(temp_file.name)
        except Exception:
            pass


@router.get("/streaming-test", response_class=HTMLResponse)
def streaming_test_page():
    """Serve the streaming test HTML page"""
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pages", "streaming_test.html"))
    if os.path.exists(path):
        return FileResponse(path)
    else:
        return HTMLResponse("""
        <html>
            <head><title>ASR Streaming Test</title></head>
            <body>
                <h1>ASR Streaming Test</h1>
                <p>Streaming test page not found.</p>
                <p>Available endpoints:</p>
                <ul>
                    <li>POST /asr - Upload audio file for transcription</li>
                    <li>GET /health - Health check</li>
                    <li>WS /ws/asr-stream - Real-time audio streaming transcription</li>
                </ul>
            </body>
        </html>
        """)


@router.get("/", response_class=HTMLResponse)
def index_page():
    """Serve the test HTML page"""
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pages", "index.html"))
    if os.path.exists(path):
        return FileResponse(path)
    else:
        return HTMLResponse("""
        <html>
            <head><title>ASR API</title></head>
            <body>
                <h1>ASR API</h1>
                <p>Audio Speech Recognition API is running!</p>
                <p>Endpoints:</p>
                <ul>
                    <li>POST /asr - Upload audio file for transcription</li>
                    <li>GET /health - Health check</li>
                    <li>WS /ws/asr-stream - Real-time audio streaming transcription</li>
                </ul>
            </body>
        </html>
        """)


@router.websocket("/ws/asr-stream")
async def stream_asr(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio streaming transcription
    
    Protocol:
    1. Client connects to WebSocket
    2. Client sends JSON config: {"language_code": "ar-EG", "sample_rate_hertz": 16000, "encoding": "LINEAR16"}
    3. Server sends acknowledgment: {"type": "metadata", "status": "ready"}
    4. Client streams binary audio chunks (LINEAR16 PCM, 16kHz, mono)
    5. Server sends transcriptions: {"type": "transcript", "text": "...", "is_final": true/false, "confidence": 0.95}
    6. Server sends completion: {"type": "complete"}
    """
    await websocket.accept()
    logger.info("🔌 WebSocket connection accepted")
    
    session = None
    loop = asyncio.get_event_loop()
    
    try:
        # Receive initial configuration
        config_data = await websocket.receive_text()
        logger.info(f"📋 Received config: {config_data}")
        
        try:
            config_dict = json.loads(config_data)
            config_request = StreamingConfigRequest(**config_dict)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"❌ Invalid config format: {str(e)}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "detail": f"Invalid configuration format: {str(e)}"
            }))
            await websocket.close()
            return
        
        # Initialize streaming service
        try:
            streaming_service = get_streaming_asr_service()
            session = streaming_service.start_streaming_session(config_request)
        except StreamingASRError as e:
            logger.error(f"❌ Streaming service error: {str(e)}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "detail": f"Streaming service error: {str(e)}"
            }))
            await websocket.close()
            return
        
        # Send acknowledgment
        await websocket.send_text(json.dumps({
            "type": "metadata",
            "status": "ready",
            "language_code": config_request.language_code,
            "sample_rate_hertz": config_request.sample_rate_hertz,
            "encoding": config_request.encoding
        }))
        logger.info("✅ Configuration accepted, ready for audio")
        
        # Start recognition thread
        session.start_recognition(websocket, loop)
        
        # Process audio chunks
        while True:
            try:
                # Receive binary audio data
                audio_chunk = await websocket.receive_bytes()
                session.add_audio_chunk(audio_chunk)
                logger.debug(f"📦 Received audio chunk: {len(audio_chunk)} bytes")
                
            except WebSocketDisconnect:
                logger.info("🔌 Client disconnected")
                break
            except Exception as e:
                logger.error(f"❌ Error receiving audio: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "detail": f"Error receiving audio: {str(e)}"
                }))
                break
    
    except Exception as e:
        logger.error(f"❌ WebSocket error: {str(e)}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "detail": f"WebSocket error: {str(e)}"
            }))
        except:
            pass
    
    finally:
        # Cleanup
        if session:
            session.stop_recognition()
        try:
            await websocket.close()
        except:
            pass
        logger.info("🔌 WebSocket connection closed")
