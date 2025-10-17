import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from typing import List, Optional

from ..models.schemas import TTSRequest, VoicesResponse, StreamingTTSRequest, StreamError
from ..services.gcp_tts import GoogleTTSService
from ..services.streaming_tts import StreamingTTSService
from ..services.filename import build_audio_filename


router = APIRouter()


def get_tts_service() -> GoogleTTSService:
    return GoogleTTSService()


def get_streaming_tts_service() -> StreamingTTSService:
    return StreamingTTSService()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/voices", response_model=List[VoicesResponse])
def list_voices(
    language_code: Optional[str] = Query(None),
    name_contains: Optional[str] = Query(None),
    tts: GoogleTTSService = Depends(get_tts_service),
):
    voices = tts.list_voices(language_code=language_code)
    out: List[VoicesResponse] = []
    for v in voices:
        if name_contains and name_contains.lower() not in v.name.lower():
            continue
        out.append(VoicesResponse(name=v.name, language_codes=list(v.language_codes), gender=v.ssml_gender.name))
    return out


@router.get("/", response_class=HTMLResponse)
def index_page():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pages", "index.html"))
    return FileResponse(path)


@router.post("/tts")
def synthesize(req: TTSRequest, tts: GoogleTTSService = Depends(get_tts_service)):
    text_payload = req.text or ""
    if len(text_payload) > 5000:
        raise HTTPException(status_code=413, detail="Text too long (max 5000 chars)")

    audio_content, voice_used, lang_used = tts.synthesize(
        text=req.text,
        ssml=req.ssml,
        language_code=req.language_code,
        voice_name=req.voice_name,
        gender=req.gender,
        audio_encoding=req.audio_encoding,
        speaking_rate=req.speaking_rate,
        pitch=req.pitch,
        effects_profile_ids=req.effects_profile_ids,
        voice_gender_choice=req.voice_gender_choice,
    )

    # Determine content type based on requested encoding
    encoding = (req.audio_encoding or "MP3").upper()
    if encoding == "OGG_OPUS":
        content_type = "audio/ogg"
        ext = "ogg"
    elif encoding == "LINEAR16":
        # Note: Google returns raw PCM for LINEAR16 (no WAV header). Many players expect WAV.
        # We expose as audio/wav for convenience, but clients should be aware it's PCM data.
        content_type = "audio/wav"
        ext = "wav"
    else:
        content_type = "audio/mpeg"
        ext = "mp3"

    # Build a suggestive filename (not saved locally)
    filename = build_audio_filename(voice_used or req.voice_name or "voice", req.text or req.ssml or "", extension=ext)

    headers = {
        "X-Voice-Used": voice_used or (req.voice_name or ""),
        "X-Language-Code": lang_used,
        "Content-Disposition": f"inline; filename=\"{filename}\"",
    }

    return StreamingResponse(iter([audio_content]), media_type=content_type, headers=headers)


@router.websocket("/ws/tts-stream")
async def websocket_tts_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming TTS audio.
    
    Message Protocol:
    1. Client sends JSON: {"text": "...", "language_code": "ar-XA", ...}
    2. Server sends metadata: {"type": "metadata", "voice_used": "...", "total_chunks": 5}
    3. Server sends audio chunks: binary data (MP3/OGG/WAV bytes)
    4. Server sends completion: {"type": "complete", "successful_chunks": 5, "failed_chunks": 0}
    5. On error: {"type": "error", "detail": "..."}
    """
    await websocket.accept()
    logger = logging.getLogger(__name__)
    
    try:
        # Receive the TTS request
        data = await websocket.receive_json()
        logger.info(f"Received WebSocket TTS request: {data.get('text', '')[:50]}...")
        
        # Validate the request
        try:
            request = StreamingTTSRequest(**data)
        except Exception as e:
            error_msg = StreamError(detail=f"Invalid request: {str(e)}")
            await websocket.send_text(error_msg.json())
            await websocket.close()
            return
        
        # Validate text length
        text_payload = request.text or ""
        if len(text_payload) > 5000:
            error_msg = StreamError(detail="Text too long (max 5000 chars)")
            await websocket.send_text(error_msg.json())
            await websocket.close()
            return
        
        # Get streaming service
        streaming_service = get_streaming_tts_service()
        
        # Start streaming
        async for chunk_type, audio_bytes, metadata in streaming_service.synthesize_streaming(
            text=request.text,
            ssml=request.ssml,
            language_code=request.language_code,
            voice_name=request.voice_name,
            gender=request.gender,
            audio_encoding=request.audio_encoding,
            speaking_rate=request.speaking_rate,
            pitch=request.pitch,
            effects_profile_ids=request.effects_profile_ids,
            voice_gender_choice=request.voice_gender_choice,
        ):
            if chunk_type == "metadata":
                # Send metadata as JSON
                metadata_parts = metadata.split("|")
                metadata_dict = {}
                for part in metadata_parts:
                    if ":" in part:
                        key, value = part.split(":", 1)
                        metadata_dict[key] = value
                
                metadata_msg = {
                    "type": "metadata",
                    "voice_used": metadata_dict.get("voice_used", ""),
                    "language_code": metadata_dict.get("language_code", ""),
                    "total_chunks": int(metadata_dict.get("total_chunks", 0))
                }
                await websocket.send_text(json.dumps(metadata_msg))
                
            elif chunk_type == "audio":
                # Send audio chunk as binary
                await websocket.send_bytes(audio_bytes)
                
            elif chunk_type == "complete":
                # Send completion message
                complete_parts = metadata.split("|")
                complete_dict = {}
                for part in complete_parts:
                    if ":" in part:
                        key, value = part.split(":", 1)
                        complete_dict[key] = int(value) if value.isdigit() else value
                
                complete_msg = {
                    "type": "complete",
                    "successful_chunks": complete_dict.get("successful_chunks", 0),
                    "failed_chunks": complete_dict.get("failed_chunks", 0)
                }
                await websocket.send_text(json.dumps(complete_msg))
                break
                
            elif chunk_type == "error":
                # Send error message
                error_msg = StreamError(detail=metadata)
                await websocket.send_text(error_msg.json())
                break
        
        logger.info("WebSocket TTS streaming completed")
        
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.exception("Error in WebSocket TTS streaming")
        try:
            error_msg = StreamError(detail=f"Server error: {str(e)}")
            await websocket.send_text(error_msg.json())
        except Exception:
            pass  # Client might have already disconnected
    finally:
        try:
            await websocket.close()
        except Exception:
            pass  # Connection might already be closed


