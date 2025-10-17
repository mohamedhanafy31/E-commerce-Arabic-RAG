# Arabic TTS API

A FastAPI-based REST API for Arabic Text-to-Speech using XTTS v2 model.

## Features

- Convert Arabic text to speech
- **Real-time streaming TTS with WebSockets**
- Configurable voice parameters (temperature, language)
- Automatic text chunking for long texts
- Speaker reference audio upload
- Health monitoring
- Audio file download
- Interactive web client for streaming

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have the required model files in the `OmarSamir/EGTTS-V0.1/` directory:
   - `config.json`
   - `vocab.json`
   - `model.pth`

3. Place your speaker reference audio as `speaker.mp3` in the root directory

4. Run the API server:
```bash
python api_server.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- **GET** `/health`
- Returns API status and model information

### Text-to-Speech
- **POST** `/tts`
- Converts Arabic text to speech
- Request body:
```json
{
  "text": "مرحبا بك في نظام تحويل النص إلى كلام",
  "temperature": 0.6,
  "language": "ar",
  "chunk_size": 10,
  "speaker_file": "optional_speaker.mp3"
}
```

**Note**: The `speaker_file` parameter is optional. If not provided, the system will use the default `speaker.mp3` file. If no default speaker file exists, you must provide one.

### Download Audio
- **GET** `/download/{filename}`
- Downloads generated audio files

### Real-time Streaming TTS
- **WebSocket** `/ws/tts-stream`
- Real-time streaming TTS with low latency
- Sends audio chunks as they are generated
- Configuration sent as initial JSON message

### Upload Speaker Reference
- **POST** `/tts/upload-speaker`
- Upload new speaker reference audio file (saves as `speaker.mp3`)
- Form data with audio file

- **POST** `/upload-speaker/{filename}`
- Upload speaker reference audio file with custom filename
- Form data with audio file

### Streaming Client
- **GET** `/streaming-client`
- Interactive web client for testing streaming TTS
- Real-time audio playback

## Usage Examples

### Using curl

```bash
# Generate speech with default speaker
curl -X POST "http://localhost:8000/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "مرحبا بك في نظام تحويل النص إلى كلام",
    "temperature": 0.6,
    "language": "ar"
  }'

# Generate speech with custom speaker file
curl -X POST "http://localhost:8000/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "مرحبا بك في نظام تحويل النص إلى كلام",
    "temperature": 0.6,
    "language": "ar",
    "speaker_file": "my_speaker.mp3"
  }'

# Upload speaker file
curl -X POST "http://localhost:8000/upload-speaker/my_speaker.mp3" \
  -F "file=@/path/to/speaker.mp3"

# Download audio file
curl -O "http://localhost:8000/download/arabic_tts_output.wav"
```

### Using Python requests

```python
import requests

# Generate speech
response = requests.post("http://localhost:8000/tts", json={
    "text": "مرحبا بك في نظام تحويل النص إلى كلام",
    "temperature": 0.6,
    "language": "ar"
})

result = response.json()
print(f"Generated: {result['audio_file']}")
print(f"Processing time: {result['processing_time']:.2f}s")

# Download audio
audio_response = requests.get(f"http://localhost:8000/download/{result['audio_file']}")
with open("output.wav", "wb") as f:
    f.write(audio_response.content)
```

### Using WebSocket for Streaming

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
                # Decode and process audio chunk
                audio_data = base64.b64decode(data["data"])
                print(f"Received audio chunk {data['audio_index']} for text chunk {data['chunk_index']}")
                
            elif data["type"] == "complete":
                print("Streaming complete!")
                break

# Run the streaming client
asyncio.run(stream_tts())
```

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Configuration

- **Temperature**: Controls voice variation (0.0-1.0)
- **Language**: Language code (default: "ar" for Arabic)
- **Chunk Size**: Maximum words per processing chunk (3-50)
- **Stream Chunk Size**: Audio chunk size for streaming (512-4096 bytes)

## Streaming Features

- **Low Latency**: Audio chunks streamed as soon as they're generated
- **Real-time Playback**: Start playing audio before the entire text is processed
- **Word-level Processing**: Text split by words for natural speech flow
- **WebSocket Protocol**: Efficient bidirectional communication
- **Base64 Encoding**: Audio data encoded for reliable transmission

### Word-Level Streaming Benefits

- **Natural Speech Flow**: Words are processed as complete units, maintaining natural pauses
- **Better Pronunciation**: Each word chunk maintains proper Arabic pronunciation
- **Faster Processing**: Smaller word chunks process faster than character-based chunks
- **Improved Quality**: Word boundaries ensure better audio quality and coherence

## Requirements

- CUDA-enabled GPU
- Python 3.8+
- PyTorch with CUDA support
- TTS library
- FastAPI and dependencies
