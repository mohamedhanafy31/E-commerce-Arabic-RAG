# Arabic TTS API Documentation

## Overview

This API provides Arabic Text-to-Speech (TTS) functionality using the XTTS v2 model (EGTTS-V0.1). It supports both traditional REST API endpoints and real-time WebSocket streaming for low-latency audio generation.

## Base URL

```
http://localhost:8000
```

## Authentication

No authentication is required for this API.

---

## 📋 Table of Contents

1. [Health Check](#health-check)
2. [Regular TTS Endpoint](#regular-tts-endpoint)
3. [WebSocket Streaming](#websocket-streaming)
4. [Static Files](#static-files)
5. [Error Handling](#error-handling)
6. [Examples](#examples)
7. [Configuration](#configuration)

---

## 🏥 Health Check

### GET `/health`

Check if the API server is running and CUDA is available.

**Response:**
```json
{
  "status": "healthy",
  "cuda_available": true
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

## 🎤 Regular TTS Endpoint

### POST `/tts`

Generate Arabic speech from text using traditional REST API.

#### Request Body

```json
{
  "text": "مرحبا بك في نظام تحويل النص إلى كلام",
  "temperature": 0.6,
  "language": "ar",
  "chunk_size": 10,
  "speaker_file": "optional_speaker.mp3"
}
```

#### Parameters

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `text` | string | ✅ | - | - | Arabic text to convert to speech |
| `temperature` | float | ❌ | 0.6 | 0.0-1.0 | Voice variation control |
| `language` | string | ❌ | "ar" | - | Language code (Arabic) |
| `chunk_size` | integer | ❌ | 10 | 3-50 | Maximum words per chunk |
| `speaker_file` | string | ❌ | null | - | Optional speaker reference file |

#### Response

**Success (200):**
```json
{
  "success": true,
  "message": "TTS generation completed successfully",
  "audio_file": "arabic_tts_output.wav",
  "processing_time": 2.45,
  "chunks_processed": 3
}
```

**Error (400/500):**
```json
{
  "success": false,
  "message": "Error message describing what went wrong"
}
```

#### Examples

**Basic Usage:**
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "مرحبا بك في نظام تحويل النص إلى كلام"
  }'
```

**With Custom Parameters:**
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "مرحبا بك في نظام تحويل النص إلى كلام",
    "temperature": 0.8,
    "chunk_size": 5,
    "speaker_file": "my_speaker.mp3"
  }'
```

**Python Example:**
```python
import requests

response = requests.post('http://localhost:8000/tts', json={
    "text": "مرحبا بك في نظام تحويل النص إلى كلام",
    "temperature": 0.6,
    "chunk_size": 10
})

if response.status_code == 200:
    result = response.json()
    print(f"Audio file: {result['audio_file']}")
    print(f"Processing time: {result['processing_time']}s")
else:
    print(f"Error: {response.json()['message']}")
```

---

## 🔄 WebSocket Streaming

### WebSocket `/ws/tts-stream`

Real-time streaming TTS with word-level processing for low latency.

#### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tts-stream');
```

#### Message Format

**Client → Server (Configuration):**
```json
{
  "text": "مرحبا بك في نظام تحويل النص إلى كلام",
  "temperature": 0.6,
  "language": "ar",
  "chunk_size": 5,
  "speaker_file": "optional_speaker.mp3",
  "stream_chunk_size": 1024
}
```

**Server → Client (Audio Chunk):**
```json
{
  "type": "audio_chunk",
  "chunk_index": 0,
  "audio_chunk_index": 0,
  "audio_data": "base64_encoded_audio_chunk",
  "total_chunks": 3,
  "total_audio_chunks": 150
}
```

**Server → Client (Chunks Info):**
```json
{
  "type": "chunks_info",
  "total_chunks": 3
}
```

**Server → Client (Error):**
```json
{
  "type": "error",
  "message": "Error description"
}
```

#### Parameters

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `text` | string | ✅ | - | - | Arabic text to convert to speech |
| `temperature` | float | ❌ | 0.6 | 0.0-1.0 | Voice variation control |
| `language` | string | ❌ | "ar" | - | Language code (Arabic) |
| `chunk_size` | integer | ❌ | 5 | 2-20 | Maximum words per chunk |
| `speaker_file` | string | ❌ | null | - | Optional speaker reference file |
| `stream_chunk_size` | integer | ❌ | 1024 | 512-4096 | Audio chunk size for streaming |

#### JavaScript Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tts-stream');

ws.onopen = function() {
    // Send configuration
    const config = {
        text: "مرحبا بك في نظام تحويل النص إلى كلام",
        temperature: 0.6,
        language: "ar",
        chunk_size: 5,
        stream_chunk_size: 1024
    };
    ws.send(JSON.stringify(config));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'audio_chunk') {
        // Decode and play audio chunk
        const audioData = atob(data.audio_data);
        const audioBlob = new Blob([audioData], { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
    } else if (data.type === 'chunks_info') {
        console.log(`Total chunks: ${data.total_chunks}`);
    } else if (data.type === 'error') {
        console.error('Error:', data.message);
    }
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};
```

#### Python Example

```python
import asyncio
import websockets
import json
import base64

async def stream_tts():
    uri = "ws://localhost:8000/ws/tts-stream"
    
    async with websockets.connect(uri) as websocket:
        # Send configuration
        config = {
            "text": "مرحبا بك في نظام تحويل النص إلى كلام",
            "temperature": 0.6,
            "language": "ar",
            "chunk_size": 5,
            "stream_chunk_size": 1024
        }
        await websocket.send(json.dumps(config))
        
        # Receive streaming data
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "audio_chunk":
                # Decode audio chunk
                audio_data = base64.b64decode(data["audio_data"])
                print(f"Received audio chunk {data['audio_chunk_index']} for text chunk {data['chunk_index']}")
                
            elif data["type"] == "chunks_info":
                print(f"Total text chunks: {data['total_chunks']}")
                
            elif data["type"] == "error":
                print(f"Error: {data['message']}")

# Run the streaming client
asyncio.run(stream_tts())
```

---

## 📁 Static Files

### GET `/streaming-client`

Serve the HTML streaming client interface.

**Response:** HTML page with WebSocket streaming client

**Example:**
```bash
curl http://localhost:8000/streaming-client
```

**Browser Access:**
```
http://localhost:8000/streaming-client
```

---

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 404 | Not Found (endpoint doesn't exist) |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "success": false,
  "message": "Detailed error description"
}
```

### Common Errors

#### Model Not Found
```json
{
  "success": false,
  "message": "Model files not found. Please ensure the model is properly downloaded."
}
```

#### Invalid Parameters
```json
{
  "success": false,
  "message": "Invalid temperature value. Must be between 0.0 and 1.0"
}
```

#### Speaker File Not Found
```json
{
  "success": false,
  "message": "Speaker file not found: speaker.mp3"
}
```

#### CUDA Not Available
```json
{
  "success": false,
  "message": "CUDA is not available. Please ensure CUDA is properly installed."
}
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_DIR` | Path to model directory | `./OmarSamir/EGTTS-V0.1` |
| `SPEAKER_FILE` | Default speaker file path | `./speaker.mp3` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

### Model Requirements

- **Model**: XTTS v2 (EGTTS-V0.1)
- **CUDA**: Required for GPU acceleration
- **Memory**: Minimum 4GB GPU memory
- **Storage**: ~2GB for model files

### Speaker File Requirements

- **Format**: MP3, WAV, or other audio formats supported by librosa
- **Duration**: 3-10 seconds recommended
- **Quality**: Clear speech without background noise
- **Language**: Arabic speaker recommended for best results

---

## 📊 Performance Tips

### Optimization Settings

#### For Speed
```json
{
  "chunk_size": 3,
  "temperature": 0.6,
  "stream_chunk_size": 2048
}
```

#### For Quality
```json
{
  "chunk_size": 10,
  "temperature": 0.7,
  "stream_chunk_size": 1024
}
```

#### For Real-time Streaming
```json
{
  "chunk_size": 2,
  "temperature": 0.5,
  "stream_chunk_size": 512
}
```

### Word-Level Streaming Benefits

- **Natural Speech Flow**: Words processed as complete units
- **Better Pronunciation**: Maintains proper Arabic pronunciation
- **Faster Processing**: Smaller chunks process quicker
- **Improved Quality**: Word boundaries ensure audio coherence

---

## 🧪 Testing

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Basic TTS
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "مرحبا"}'

# Streaming client
open http://localhost:8000/streaming-client
```

### Test WebSocket Streaming

```bash
# Using wscat (install with: npm install -g wscat)
wscat -c ws://localhost:8000/ws/tts-stream

# Send configuration
{"text": "مرحبا بك", "chunk_size": 3}
```

---

## 📝 Notes

### Word-Level Processing

The API now uses word-level chunking instead of character-level:

- **Before**: Text split by characters (max 300 chars)
- **After**: Text split by words (max 10 words for regular, 5 for streaming)
- **Benefit**: More natural speech flow and better pronunciation

### Audio Format

- **Format**: WAV (16-bit PCM, 22kHz, mono)
- **Encoding**: Base64 for WebSocket transmission
- **Chunking**: Configurable audio chunk sizes for streaming

### Browser Compatibility

- **WebSocket**: Modern browsers (Chrome, Firefox, Safari, Edge)
- **Audio**: Web Audio API for seamless playback
- **Base64**: Native browser support

---

## 🆘 Support

For issues or questions:

1. Check the server logs for detailed error messages
2. Verify CUDA installation and GPU availability
3. Ensure model files are properly downloaded
4. Test with the provided HTML streaming client
5. Check browser console for WebSocket errors

---

## 📄 License

This API uses the XTTS v2 model (EGTTS-V0.1) from OmarSamir on Hugging Face.
