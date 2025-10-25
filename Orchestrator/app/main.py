"""
Main FastAPI application for Orchestrator
Handles WebSocket connections and HTTP endpoints
"""

import asyncio
import json
import time
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings, get_settings
from app.core.logging import configure_logging, get_logger, log_operation, log_error, log_performance
from app.middleware.error_handler import ErrorHandlerMiddleware, RequestLoggingMiddleware
from app.models.schemas import (
    ReadyMessage, AudioConfig, AudioEndMessage, ErrorMessage,
    MessageType, ConversationState, StateMessage
)
from app.services.orchestrator import get_orchestrator_service
from app.utils.session_manager import get_session_manager

# Configure logging
configure_logging()
logger = get_logger("main")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Orchestrator for Conversational AI System",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware (order matters - first added is outermost)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.cors_origins == "*" else settings.cors_origins.split(","),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get services
orchestrator_service = get_orchestrator_service()
session_manager = get_session_manager()


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Server will run on {settings.host}:{settings.port}")
    logger.info(f"ASR Service: {settings.asr_service_url}")
    logger.info(f"RAG Service: {settings.rag_service_url}")
    logger.info(f"TTS Service: {settings.tts_service_url}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down Orchestrator service")
    await orchestrator_service.cleanup_all_sessions()


@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "endpoints": {
            "websocket": "/ws/conversation",
            "health": "/health",
            "stats": "/stats",
            "docs": "/docs"
        },
        "configuration": {
            "max_concurrent_sessions": settings.max_concurrent_sessions,
            "session_timeout_seconds": settings.session_timeout_seconds,
            "audio_format": settings.audio_format,
            "audio_sample_rate": settings.audio_sample_rate,
            "default_language": settings.default_language_code
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # Would use datetime.utcnow().isoformat()
            "services": {
                "orchestrator": "healthy",
                "session_manager": "healthy"
            },
            "active_sessions": len(orchestrator_service.active_sessions),
            "max_sessions": settings.max_concurrent_sessions
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        session_stats = await session_manager.get_session_stats()
        
        stats = {
            "sessions": session_stats,
            "active_conversations": len(orchestrator_service.active_sessions),
            "configuration": {
                "max_concurrent_sessions": settings.max_concurrent_sessions,
                "session_timeout_seconds": settings.session_timeout_seconds,
                "audio_sample_rate": settings.audio_sample_rate,
                "audio_format": settings.audio_format,
                "default_language_code": settings.default_language_code,
                "tts_language_code": settings.tts_language_code,
                "enable_conversation_history": settings.enable_conversation_history,
                "enable_sentence_streaming": settings.enable_sentence_streaming
            }
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@app.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    """
    Main WebSocket endpoint for conversational AI
    
    Protocol:
    1. Client connects
    2. Server sends ready message with session_id
    3. Client sends audio chunks (binary data)
    4. Client sends {"type": "audio_end"} to signal end of speech
    5. Server processes: ASR -> RAG -> TTS
    6. Server streams responses back to client
    7. Server sends completion message
    """
    start_time = time.time()
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    log_operation(logger, "websocket_connection_started", 
                 client_ip=client_ip)
    
    await websocket.accept()
    logger.info("WebSocket connection accepted", extra={
        'operation': 'websocket_accepted',
        'client_ip': client_ip
    })
    
    session_id = None
    conversation_session = None
    
    try:
        # Create session with default audio config
        audio_config = AudioConfig(
            language_code=settings.default_language_code,
            sample_rate_hertz=settings.audio_sample_rate,
            encoding=settings.audio_format,
            channels=settings.audio_channels
        )
        
        log_operation(logger, "session_creation_started", 
                     audio_config=audio_config.dict())
        
        session_id = await orchestrator_service.create_session(websocket, audio_config)
        if not session_id:
            log_error(logger, Exception("Session creation failed"), "session_creation")
            error_msg = ErrorMessage(
                error_code="session_creation_failed",
                detail="Failed to create conversation session"
            )
            await websocket.send_text(error_msg.json())
            await websocket.close()
            return
        
        log_operation(logger, "session_created", 
                     session_id=session_id, 
                     audio_config=audio_config.dict())
        
        # Send ready message
        ready_msg = ReadyMessage(
            session_id=session_id,
            audio_config=audio_config
        )
        await websocket.send_text(ready_msg.json())
        
        # Signal client to begin recording (backend-driven auto-start)
        try:
            state_msg = StateMessage(
                state=ConversationState.LISTENING,
                previous_state=ConversationState.IDLE
            )
            await websocket.send_text(state_msg.json())
        except Exception as e:
            logger.warning(f"Failed to send initial state_update: {e}")
        
        logger.info(f"Session {session_id} ready for conversation", extra={
            'operation': 'session_ready',
            'session_id': session_id
        })
        
        # Get conversation session
        conversation_session = await orchestrator_service.get_session(session_id)
        if not conversation_session:
            log_error(logger, Exception("Failed to get conversation session"), 
                     "session_retrieval", session_id=session_id)
            return
        
        # Main message loop
        message_count = 0
        audio_chunks_received = 0
        
        while True:
            try:
                # Receive message
                message = await websocket.receive()
                message_count += 1
                
                if message["type"] == "websocket.receive":
                    if "bytes" in message:
                        # Binary audio data
                        audio_data = message["bytes"]
                        audio_chunks_received += 1
                        
                        # log_operation(logger, "audio_chunk_received", 
                        #            session_id=session_id,
                        #            chunk_size=len(audio_data),
                        #            chunk_number=audio_chunks_received)
                        
                        # Process audio chunk
                        success = await conversation_session.process_audio_chunk(audio_data)
                        if not success:
                            log_error(logger, Exception("Failed to process audio chunk"), 
                                     "audio_chunk_processing", session_id=session_id)
                            break
                            
                    elif "text" in message:
                        # Text message
                        try:
                            data = json.loads(message["text"])
                            message_type = data.get("type")
                            
                            log_operation(logger, "text_message_received", 
                                       session_id=session_id,
                                       message_type=message_type)
                            
                            if message_type == "audio_end":
                                # End of audio input
                                log_operation(logger, "audio_end_received", 
                                           session_id=session_id,
                                           total_chunks=audio_chunks_received)
                                
                                success = await conversation_session.end_audio_input()
                                if not success:
                                    log_error(logger, Exception("Failed to end audio input"), 
                                             "audio_end_processing", session_id=session_id)
                                    break
                                    
                            else:
                                logger.warning(f"Unknown message type: {message_type}", extra={
                                    'operation': 'unknown_message_type',
                                    'session_id': session_id,
                                    'message_type': message_type
                                })
                                
                        except json.JSONDecodeError as e:
                            log_error(logger, e, "json_decode", 
                                     session_id=session_id,
                                     message_text=message['text'][:100])  # First 100 chars
                        except Exception as e:
                            log_error(logger, e, "text_message_processing", 
                                     session_id=session_id)
                            
                elif message["type"] == "websocket.disconnect":
                    logger.info("Client disconnected", extra={
                        'operation': 'client_disconnect',
                        'session_id': session_id
                    })
                    break
                    
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected", extra={
                    'operation': 'websocket_disconnect',
                    'session_id': session_id
                })
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                break
                
    except Exception as e:
        log_error(logger, e, "websocket_error", session_id=session_id)
        try:
            error_msg = ErrorMessage(
                error_code="websocket_error",
                detail=str(e)
            )
            await websocket.send_text(error_msg.json())
        except:
            pass
    finally:
        # Cleanup and performance logging
        if session_id:
            duration_ms = (time.time() - start_time) * 1000
            log_performance(logger, "websocket_session_completed", duration_ms,
                          session_id=session_id,
                          total_messages=message_count,
                          audio_chunks_received=audio_chunks_received)
            
            await orchestrator_service.close_session(session_id)
            logger.info(f"Cleaned up session: {session_id}", extra={
                'operation': 'session_cleanup',
                'session_id': session_id,
                'duration_ms': duration_ms
            })


# Mount static files for test client
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Advanced test client for WebSocket connection"""
    import os
    test_client_path = os.path.join("static", "test_client.html")
    if os.path.exists(test_client_path):
        with open(test_client_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(f.read())
    else:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Orchestrator Test</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>Orchestrator Conversational AI Test</h1>
            <div id="status">Disconnected</div>
            <div id="messages"></div>
            <button id="connect">Connect</button>
            <button id="disconnect" disabled>Disconnect</button>
            
            <script>
                let ws = null;
                const status = document.getElementById('status');
                const messages = document.getElementById('messages');
                const connectBtn = document.getElementById('connect');
                const disconnectBtn = document.getElementById('disconnect');
                
                function addMessage(text) {
                    const div = document.createElement('div');
                    div.textContent = new Date().toLocaleTimeString() + ': ' + text;
                    messages.appendChild(div);
                }
                
                connectBtn.onclick = function() {
                    ws = new WebSocket('ws://localhost:8004/ws/conversation');
                    
                    ws.onopen = function() {
                        status.textContent = 'Connected';
                        connectBtn.disabled = true;
                        disconnectBtn.disabled = false;
                        addMessage('Connected to Orchestrator');
                    };
                    
                    ws.onmessage = function(event) {
                        try {
                            const data = JSON.parse(event.data);
                            addMessage('Received: ' + JSON.stringify(data, null, 2));
                        } catch (e) {
                            addMessage('Received binary data: ' + event.data.length + ' bytes');
                        }
                    };
                    
                    ws.onclose = function() {
                        status.textContent = 'Disconnected';
                        connectBtn.disabled = false;
                        disconnectBtn.disabled = true;
                        addMessage('Disconnected');
                    };
                    
                    ws.onerror = function(error) {
                        addMessage('Error: ' + error);
                    };
                };
                
                disconnectBtn.onclick = function() {
                    if (ws) {
                        ws.close();
                    }
                };
            </script>
        </body>
        </html>
        """)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
