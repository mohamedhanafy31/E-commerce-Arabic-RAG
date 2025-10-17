import os
import sys
import time
import traceback
import tempfile
import shutil
import json
import base64
import asyncio
from typing import Optional, List
from pathlib import Path

import torch
import torchaudio
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

# Import for model downloading
try:
    from huggingface_hub import snapshot_download
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("⚠️  huggingface_hub not available. Model auto-download disabled.")


# Pydantic models for API requests/responses
class TTSRequest(BaseModel):
    text: str = Field(..., description="Arabic text to convert to speech")
    temperature: float = Field(0.6, ge=0.0, le=1.0, description="Voice variation control (0.0-1.0)")
    language: str = Field("ar", description="Language code (default: ar for Arabic)")
    chunk_size: int = Field(10, ge=3, le=50, description="Maximum words per chunk")
    speaker_file: Optional[str] = Field(None, description="Optional speaker reference file path (relative to repo root)")


class TTSResponse(BaseModel):
    success: bool
    message: str
    audio_file: Optional[str] = None
    processing_time: float
    chunks_processed: int


class StreamingTTSRequest(BaseModel):
    text: str = Field(..., description="Arabic text to convert to speech")
    temperature: float = Field(0.6, ge=0.0, le=1.0, description="Voice variation control (0.0-1.0)")
    language: str = Field("ar", description="Language code (default: ar for Arabic)")
    chunk_size: int = Field(5, ge=2, le=20, description="Maximum words per chunk for streaming")
    speaker_file: Optional[str] = Field(None, description="Optional speaker reference file path")
    stream_chunk_size: int = Field(1024, ge=512, le=4096, description="Audio chunk size for streaming")


class HealthResponse(BaseModel):
    status: str
    cuda_available: bool
    model_loaded: bool
    device: str


# Global variables for model
model = None
gpt_cond_latent = None
speaker_embedding = None
device = None
model_loaded = False

# Initialize FastAPI app
app = FastAPI(
    title="Arabic TTS API",
    description="API for Arabic Text-to-Speech using XTTS v2 model",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (will be set after get_repo_root is defined)


def assert_file_exists(path: str, description: str) -> None:
    """Check if file exists, raise error if not."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing {description}: {path}")


def get_repo_root() -> str:
    """Get the repository root directory."""
    return os.path.abspath(os.path.dirname(__file__))


# Mount static files after get_repo_root is defined
app.mount("/static", StaticFiles(directory=get_repo_root()), name="static")


def download_model_if_needed(model_dir: str) -> bool:
    """Download the EGTTS-V0.1 model if it doesn't exist."""
    if not HF_AVAILABLE:
        print("❌ huggingface_hub not available. Cannot download model.")
        return False
    
    config_path = os.path.join(model_dir, "config.json")
    if os.path.exists(config_path):
        print("✅ Model files already exist.")
        return True
    
    print("📥 Model files not found. Downloading EGTTS-V0.1 model...")
    print("This may take a few minutes depending on your internet connection...")
    
    try:
        # Create the directory structure
        os.makedirs(model_dir, exist_ok=True)
        
        # Download all files from the repository
        snapshot_download(
            repo_id="OmarSamir/EGTTS-V0.1",
            local_dir=model_dir,
            local_dir_use_symlinks=False
        )
        
        print("✅ Model downloaded successfully!")
        
        # Verify essential files were downloaded
        essential_files = ["config.json", "vocab.json", "model.pth"]
        for file in essential_files:
            file_path = os.path.join(model_dir, file)
            if not os.path.exists(file_path):
                print(f"❌ Essential file missing after download: {file}")
                return False
        
        print("✅ All essential model files verified.")
        return True
        
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        return False


def split_text_into_chunks(text: str, max_words: int = 10) -> List[str]:
    """Split text into word-based chunks for natural speech flow."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for word in words:
        if current_word_count >= max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_word_count = 1
        else:
            current_chunk.append(word)
            current_word_count += 1
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks


def get_speaker_latents(speaker_path: Optional[str] = None):
    """Get speaker conditioning latents from a speaker file."""
    global model, device
    
    if speaker_path is None:
        # Use default speaker file
        repo_root = get_repo_root()
        speaker_path = os.path.join(repo_root, "speaker.mp3")
    
    # Check if speaker file exists
    if not os.path.exists(speaker_path):
        raise FileNotFoundError(f"Speaker file not found: {speaker_path}")
    
    print(f"Computing speaker conditioning latents from: {speaker_path}")
    with torch.inference_mode():
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[speaker_path])
    
    return gpt_cond_latent, speaker_embedding


def generate_audio_chunk(text_chunk: str, language: str, gpt_cond_latent, speaker_embedding, temperature: float):
    """Generate audio for a single text chunk."""
    global model
    
    with torch.inference_mode():
        out = model.inference(
            text_chunk,
            language,
            gpt_cond_latent,
            speaker_embedding,
            temperature=temperature,
        )
    
    wav = torch.tensor(out["wav"]).unsqueeze(0)
    return wav


def create_wav_header(sample_rate: int = 24000, channels: int = 1, bits_per_sample: int = 16, data_size: int = 0):
    """Create WAV file header."""
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    
    header = bytearray()
    # RIFF header
    header.extend(b'RIFF')
    header.extend((36 + data_size).to_bytes(4, 'little'))
    header.extend(b'WAVE')
    
    # fmt chunk
    header.extend(b'fmt ')
    header.extend((16).to_bytes(4, 'little'))  # fmt chunk size
    header.extend((1).to_bytes(2, 'little'))   # PCM format
    header.extend(channels.to_bytes(2, 'little'))
    header.extend(sample_rate.to_bytes(4, 'little'))
    header.extend(byte_rate.to_bytes(4, 'little'))
    header.extend(block_align.to_bytes(2, 'little'))
    header.extend(bits_per_sample.to_bytes(2, 'little'))
    
    # data chunk
    header.extend(b'data')
    header.extend(data_size.to_bytes(4, 'little'))
    
    return header


def audio_to_base64_chunks(wav_tensor, chunk_size: int = 1024):
    """Convert audio tensor to base64 encoded WAV chunks for streaming."""
    # Convert to numpy and flatten
    audio_data = wav_tensor.squeeze().cpu().numpy()
    
    # Convert to 16-bit PCM
    audio_int16 = (audio_data * 32767).astype('int16')
    audio_bytes = audio_int16.tobytes()
    
    # Create WAV header
    wav_header = create_wav_header(data_size=len(audio_bytes))
    
    # Combine header and audio data
    full_wav = wav_header + audio_bytes
    
    print(f"🔍 DEBUG: Full WAV size: {len(full_wav)} bytes")
    print(f"🔍 DEBUG: WAV header size: {len(wav_header)} bytes")
    print(f"🔍 DEBUG: Audio data size: {len(audio_bytes)} bytes")
    print(f"🔍 DEBUG: Chunk size: {chunk_size} bytes")
    
    # Split into chunks with proper base64 encoding
    chunks = []
    for i in range(0, len(full_wav), chunk_size):
        chunk = full_wav[i:i + chunk_size]
        chunk_b64 = base64.b64encode(chunk).decode('utf-8')
        chunks.append(chunk_b64)
        
        if i == 0:
            print(f"🔍 DEBUG: First chunk: binary={len(chunk)} bytes, base64={len(chunk_b64)} chars")
        if i + chunk_size >= len(full_wav):
            print(f"🔍 DEBUG: Last chunk: binary={len(chunk)} bytes, base64={len(chunk_b64)} chars")
            print(f"🔍 DEBUG: Last chunk sample: {chunk_b64[:20]}...{chunk_b64[-20:]}")
    
    print(f"🔍 DEBUG: Total chunks created: {len(chunks)}")
    
    # Validate all chunks can be decoded
    for i, chunk_b64 in enumerate(chunks):
        try:
            decoded = base64.b64decode(chunk_b64)
            if i == len(chunks) - 1:
                print(f"🔍 DEBUG: Last chunk validation: {len(decoded)} bytes decoded successfully")
        except Exception as e:
            print(f"🔍 DEBUG: Chunk {i} validation failed: {e}")
    
    return chunks


def load_model():
    """Load the XTTS model and compute speaker conditioning latents."""
    global model, gpt_cond_latent, speaker_embedding, device, model_loaded
    
    if model_loaded:
        return
    
    print("Loading EGTTS (XTTS v2) model...")
    
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available. Please run with a CUDA-enabled PyTorch build and GPU drivers."
        )
    
    device = torch.device("cuda")
    
    repo_root = get_repo_root()
    model_dir = os.path.join(repo_root, "OmarSamir", "EGTTS-V0.1")
    
    # Try to download model if it doesn't exist
    if not download_model_if_needed(model_dir):
        raise RuntimeError("Failed to download or verify model files")
    
    config_path = os.path.join(model_dir, "config.json")
    vocab_path = os.path.join(model_dir, "vocab.json")
    checkpoint_dir = model_dir  # contains model.pth
    speaker_wav = os.path.join(repo_root, "speaker.mp3")
    
    # Check if all required files exist (after download)
    assert_file_exists(config_path, "config.json")
    assert_file_exists(vocab_path, "vocab.json")
    assert_file_exists(os.path.join(checkpoint_dir, "model.pth"), "model.pth")
    
    # Load model
    config = XttsConfig()
    config.load_json(config_path)
    model = Xtts.init_from_config(config)
    
    use_deepspeed = False
    try:
        import deepspeed  # noqa: F401
        use_deepspeed = True
    except Exception:
        print("deepspeed not found; continuing without it.")
    
    model.load_checkpoint(
        config,
        checkpoint_dir=checkpoint_dir,
        use_deepspeed=use_deepspeed,
        vocab_path=vocab_path,
    )
    
    model.to(device)
    model.eval()
    
    # Don't compute speaker latents here - do it dynamically per request
    print("Model loaded successfully!")
    model_loaded = True


# Load model during module initialization
print("Initializing API server...")
try:
    load_model()
    print("✅ Model loaded successfully during initialization!")
except Exception as e:
    print(f"❌ Failed to load model during initialization: {e}")
    traceback.print_exc()
    print("⚠️  Server will start but TTS functionality will be unavailable until model is loaded.")


@app.post("/download-model")
async def download_model_endpoint():
    """Download the EGTTS-V0.1 model from Hugging Face."""
    if not HF_AVAILABLE:
        raise HTTPException(status_code=503, detail="huggingface_hub not available")
    
    repo_root = get_repo_root()
    model_dir = os.path.join(repo_root, "OmarSamir", "EGTTS-V0.1")
    
    try:
        success = download_model_if_needed(model_dir)
        if success:
            return {"message": "Model downloaded successfully", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to download model")
    except Exception as e:
        error_msg = f"Failed to download model: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/load-model")
async def manual_load_model():
    """Manually load the model (useful if initialization failed)."""
    global model_loaded
    
    if model_loaded:
        return {"message": "Model is already loaded", "status": "success"}
    
    try:
        load_model()
        return {"message": "Model loaded successfully", "status": "success"}
    except Exception as e:
        error_msg = f"Failed to load model: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check the health status of the API."""
    return HealthResponse(
        status="healthy" if model_loaded else "unhealthy",
        cuda_available=torch.cuda.is_available(),
        model_loaded=model_loaded,
        device=str(device) if device else "unknown"
    )


@app.websocket("/ws/tts-stream")
async def websocket_tts_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming TTS."""
    await websocket.accept()
    
    if not model_loaded:
        await websocket.send_json({
            "type": "error",
            "message": "Model not loaded"
        })
        await websocket.close()
        return
    
    try:
        # Receive initial configuration
        config_data = await websocket.receive_json()
        
        # Parse configuration
        text = config_data.get("text", "")
        temperature = config_data.get("temperature", 0.6)
        language = config_data.get("language", "ar")
        chunk_size = config_data.get("chunk_size", 100)
        speaker_file = config_data.get("speaker_file")
        stream_chunk_size = config_data.get("stream_chunk_size", 1024)
        
        if not text:
            await websocket.send_json({
                "type": "error",
                "message": "No text provided"
            })
            await websocket.close()
            return
        
        # Get speaker latents
        speaker_path = None
        if speaker_file:
            repo_root = get_repo_root()
            speaker_path = os.path.join(repo_root, speaker_file)
        
        try:
            gpt_cond_latent, speaker_embedding = get_speaker_latents(speaker_path)
        except FileNotFoundError as e:
            await websocket.send_json({
                "type": "error",
                "message": f"Speaker file not found: {str(e)}"
            })
            await websocket.close()
            return
        
        # Send initial metadata
        await websocket.send_json({
            "type": "metadata",
            "sample_rate": 24000,
            "channels": 1,
            "format": "pcm_16",
            "total_chunks": 0
        })
        
            # Split text into word-based chunks
        text_chunks = split_text_into_chunks(text, chunk_size)
        
        # Send total chunks info
        await websocket.send_json({
            "type": "chunks_info",
            "total_chunks": len(text_chunks)
        })
        
        # Process each chunk and stream audio
        for i, chunk in enumerate(text_chunks):
            try:
                # Generate audio for this chunk
                wav_tensor = generate_audio_chunk(
                    chunk, language, gpt_cond_latent, speaker_embedding, temperature
                )
                
                # Convert to base64 chunks
                audio_chunks = audio_to_base64_chunks(wav_tensor, stream_chunk_size)
                
                # Send chunk metadata
                await websocket.send_json({
                    "type": "chunk_start",
                    "chunk_index": i,
                    "text": chunk,
                    "audio_chunks": len(audio_chunks)
                })
                
                # Stream audio chunks
                for j, audio_chunk in enumerate(audio_chunks):
                    # Debug logging
                    if j == 0:
                        print(f"🔍 DEBUG: First chunk for text chunk {i}: length={len(audio_chunk)}, sample={audio_chunk[:20]}")
                    if j == len(audio_chunks) - 1:
                        print(f"🔍 DEBUG: Last chunk for text chunk {i}: length={len(audio_chunk)}, sample={audio_chunk[-20:]}")
                    
                    await websocket.send_json({
                        "type": "audio_chunk",
                        "chunk_index": i,
                        "audio_index": j,
                        "data": audio_chunk,
                        "data_length": len(audio_chunk)
                    })
                
                # Send chunk complete
                await websocket.send_json({
                    "type": "chunk_complete",
                    "chunk_index": i
                })
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing chunk {i}: {str(e)}"
                })
                break
        
        # Send completion signal
        await websocket.send_json({
            "type": "complete",
            "message": "All chunks processed successfully"
        })
        
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Server error: {str(e)}"
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@app.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """Convert Arabic text to speech."""
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    start_time = time.time()
    
    try:
        # Get speaker latents (use provided speaker file or default)
        speaker_path = None
        if request.speaker_file:
            repo_root = get_repo_root()
            speaker_path = os.path.join(repo_root, request.speaker_file)
        
        try:
            gpt_cond_latent, speaker_embedding = get_speaker_latents(speaker_path)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=f"Speaker file not found: {str(e)}")
        
        # Split text into chunks
        text_chunks = split_text_into_chunks(request.text, request.chunk_size)
        print(f"Split text into {len(text_chunks)} chunks")
        
        # Create temporary directory for audio files
        temp_dir = tempfile.mkdtemp()
        all_audio_files = []
        
        # Process each chunk
        for i, chunk in enumerate(text_chunks):
            print(f"Processing chunk {i+1}/{len(text_chunks)}: {chunk[:50]}...")
            
            with torch.inference_mode():
                out = model.inference(
                    chunk,
                    request.language,
                    gpt_cond_latent,
                    speaker_embedding,
                    temperature=request.temperature,
                )
            
            wav = torch.tensor(out["wav"]).unsqueeze(0)
            sample_rate = 24000
            
            # Save chunk audio
            chunk_filename = f"chunk_{i+1:02d}.wav"
            chunk_path = os.path.join(temp_dir, chunk_filename)
            torchaudio.save(chunk_path, wav.cpu(), sample_rate)
            all_audio_files.append(chunk_path)
        
        # Concatenate all audio files
        print("Concatenating all audio chunks...")
        concatenated_wav = None
        
        for file_path in all_audio_files:
            wav_data, sample_rate = torchaudio.load(file_path)
            if concatenated_wav is None:
                concatenated_wav = wav_data
            else:
                concatenated_wav = torch.cat([concatenated_wav, wav_data], dim=1)
        
        # Save final audio file
        final_filename = "arabic_tts_output.wav"
        final_path = os.path.join(temp_dir, final_filename)
        torchaudio.save(final_path, concatenated_wav, sample_rate)
        
        # Move to a permanent location
        repo_root = get_repo_root()
        permanent_path = os.path.join(repo_root, final_filename)
        
        # Handle filename conflicts
        counter = 1
        original_path = permanent_path
        while os.path.exists(permanent_path):
            name, ext = os.path.splitext(original_path)
            permanent_path = f"{name}_{counter}{ext}"
            counter += 1
        
        shutil.move(final_path, permanent_path)
        
        processing_time = time.time() - start_time
        
        return TTSResponse(
            success=True,
            message=f"Successfully generated speech from {len(text_chunks)} chunks",
            audio_file=os.path.basename(permanent_path),
            processing_time=processing_time,
            chunks_processed=len(text_chunks)
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Error during TTS processing: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        
        return TTSResponse(
            success=False,
            message=error_msg,
            audio_file=None,
            processing_time=processing_time,
            chunks_processed=0
        )


@app.get("/download/{filename}")
async def download_audio(filename: str):
    """Download generated audio file."""
    repo_root = get_repo_root()
    file_path = os.path.join(repo_root, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="audio/wav"
    )


@app.post("/tts/upload-speaker")
async def upload_speaker_reference(file: UploadFile = File(...)):
    """Upload a new speaker reference audio file."""
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    repo_root = get_repo_root()
    speaker_path = os.path.join(repo_root, "speaker.mp3")
    
    # Save uploaded file
    with open(speaker_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"message": "Speaker reference updated successfully", "filename": file.filename, "path": "speaker.mp3"}


@app.post("/upload-speaker/{filename}")
async def upload_speaker_with_name(filename: str, file: UploadFile = File(...)):
    """Upload a speaker reference audio file with custom filename."""
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # Validate filename
    if not filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    repo_root = get_repo_root()
    speaker_path = os.path.join(repo_root, filename)
    
    # Save uploaded file
    with open(speaker_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"message": "Speaker reference uploaded successfully", "filename": filename, "path": filename}


@app.get("/streaming-client")
async def streaming_client():
    """Serve the streaming TTS client."""
    return FileResponse(os.path.join(get_repo_root(), "streaming_client.html"))


@app.get("/docs")
async def api_documentation():
    """Serve the API documentation."""
    return FileResponse(os.path.join(get_repo_root(), "API_DOCUMENTATION.md"))


@app.get("/documentation")
async def html_documentation():
    """Serve the HTML API documentation."""
    return FileResponse(os.path.join(get_repo_root(), "docs.html"))


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Arabic TTS API",
        "version": "1.0.0",
        "model_status": "loaded" if model_loaded else "not_loaded",
        "auto_download": HF_AVAILABLE,
        "speaker_file_optional": True,
        "streaming_supported": True,
        "endpoints": {
            "health": "/health",
            "download_model": "/download-model",
            "load_model": "/load-model",
            "tts": "/tts",
            "tts_streaming": "/ws/tts-stream",
            "streaming_client": "/streaming-client",
            "download": "/download/{filename}",
            "upload_speaker_default": "/tts/upload-speaker",
            "upload_speaker_custom": "/upload-speaker/{filename}",
            "documentation_html": "/documentation",
            "documentation_raw": "/docs"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
