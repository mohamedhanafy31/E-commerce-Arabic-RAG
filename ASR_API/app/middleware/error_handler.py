import logging
import time
import traceback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..services.gcp_asr import ASRError, AudioProcessingError, TranscriptionError, CredentialsError
from ..core.logging import get_logger, log_error, log_performance

logger = get_logger("middleware")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware for ASR API"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        
        except CredentialsError as e:
            logger.error(f"❌ Credentials error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Credentials Error",
                    "detail": str(e),
                    "type": "credentials_error",
                    "solutions": [
                        "Check GOOGLE_APPLICATION_CREDENTIALS environment variable",
                        "Ensure tts-key.json file exists and is valid",
                        "Verify Google Cloud service account permissions"
                    ]
                }
            )
        
        except AudioProcessingError as e:
            logger.error(f"❌ Audio processing error: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Audio Processing Error",
                    "detail": str(e),
                    "type": "audio_processing_error",
                    "solutions": [
                        "Check audio file format (MP3, WAV, FLAC supported)",
                        "Ensure file size is within limits",
                        "Install ffmpeg for advanced audio processing"
                    ]
                }
            )
        
        except TranscriptionError as e:
            logger.error(f"❌ Transcription error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Transcription Error",
                    "detail": str(e),
                    "type": "transcription_error",
                    "solutions": [
                        "Check Google Cloud Speech-to-Text API quota",
                        "Verify audio quality and language settings",
                        "Try with a different audio file"
                    ]
                }
            )
        
        except ASRError as e:
            logger.error(f"❌ ASR error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "ASR Error",
                    "detail": str(e),
                    "type": "asr_error"
                }
            )
        
        except HTTPException as e:
            # Re-raise HTTP exceptions as they are already properly formatted
            raise e
        
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": "An unexpected error occurred",
                    "type": "internal_error",
                    "request_id": getattr(request.state, "request_id", None)
                }
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all requests"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Generate request ID
        import uuid
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        logger.info(f"Request started: {request.method} {request.url.path}", extra={
            'operation': 'request_started',
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'client_ip': request.client.host if request.client else "unknown",
            'user_agent': request.headers.get("user-agent", "unknown")
        })
        
        response = await call_next(request)
        
        # Log request completion
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Request completed: {request.method} {request.url.path} - {response.status_code}", extra={
            'operation': 'request_completed',
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'duration_ms': duration_ms
        })
        
        return response
