# WebSocket Streaming ASR Implementation

## Overview

This document describes the WebSocket streaming implementation for the ASR API, which enables real-time audio transcription using Google Cloud Speech-to-Text streaming API.

## Architecture

### Components

1. **WebSocket Endpoint**: `/ws/asr-stream` - Handles real-time connections
2. **Streaming Service**: `StreamingASRProcessor` - Manages Google Cloud streaming API
3. **Session Management**: `StreamingSession` - Handles individual streaming sessions
4. **Audio Processing**: Converts audio to LINEAR16 PCM format

### Threading Model

- **Main Thread**: Handles WebSocket communication (asyncio)
- **Recognition Thread**: Runs Google Cloud streaming_recognize (blocking call)
- **Queue Bridge**: Transfers audio data between threads safely

## WebSocket Protocol

### Connection Flow

1. **Client connects** to `ws://localhost:8001/ws/asr-stream`
2. **Client sends configuration** as JSON message
3. **Server sends acknowledgment** with status
4. **Client streams audio chunks** as binary data
5. **Server sends transcriptions** as JSON messages
6. **Server sends completion** signal

### Message Formats

#### Configuration Request (Client → Server)
```json
{
    "language_code": "ar-EG",
    "sample_rate_hertz": 16000,
    "encoding": "LINEAR16"
}
```

#### Metadata Acknowledgment (Server → Client)
```json
{
    "type": "metadata",
    "status": "ready",
    "language_code": "ar-EG",
    "sample_rate_hertz": 16000,
    "encoding": "LINEAR16"
}
```

#### Transcript Response (Server → Client)
```json
{
    "type": "transcript",
    "text": "مرحبا بك في نظام التعرف على الكلام",
    "is_final": true,
    "confidence": 0.95
}
```

#### Error Response (Server → Client)
```json
{
    "type": "error",
    "detail": "Invalid audio format"
}
```

#### Completion Signal (Server → Client)
```json
{
    "type": "complete"
}
```

## Audio Format Requirements

### Supported Format
- **Encoding**: LINEAR16 PCM
- **Sample Rate**: 16,000 Hz
- **Channels**: Mono (1 channel)
- **Bit Depth**: 16-bit signed little-endian
- **No Headers**: Raw PCM data only

### Conversion Methods

#### Using pydub (Recommended)
```python
from pydub import AudioSegment

# Load audio file
audio = AudioSegment.from_file("input.mp3")

# Convert to required format
audio = audio.set_channels(1)        # Mono
audio = audio.set_frame_rate(16000)  # 16kHz
audio = audio.set_sample_width(2)    # 16-bit

# Get raw PCM data
pcm_data = audio.raw_data
```

#### Using ffmpeg
```bash
ffmpeg -i input.mp3 -f s16le -ar 16000 -ac 1 output.pcm
```

## Configuration

### Environment Variables

```bash
# Streaming-specific settings
DEFAULT_SAMPLE_RATE_HERTZ=16000
STREAMING_INTERIM_RESULTS=true
ENABLE_AUTOMATIC_PUNCTUATION=true

# Existing settings
DEFAULT_LANGUAGE_CODE=ar-EG
GOOGLE_APPLICATION_CREDENTIALS=tts-key.json
```

### Settings Class

```python
class Settings(BaseSettings):
    # Streaming ASR specific settings
    default_sample_rate_hertz: int = 16000
    streaming_interim_results: bool = True
    enable_automatic_punctuation: bool = True
    
    # Existing settings
    default_language_code: str = "ar-EG"
    google_application_credentials: Optional[str] = None
```

## Usage Examples

### Python Client Example

```python
import asyncio
import websockets
import json
from pydub import AudioSegment

async def stream_audio():
    uri = "ws://localhost:8001/ws/asr-stream"
    
    async with websockets.connect(uri) as websocket:
        # Send configuration
        config = {
            "language_code": "ar-EG",
            "sample_rate_hertz": 16000,
            "encoding": "LINEAR16"
        }
        await websocket.send(json.dumps(config))
        
        # Wait for acknowledgment
        response = await websocket.recv()
        ack = json.loads(response)
        print(f"Server ready: {ack}")
        
        # Convert audio to PCM
        audio = AudioSegment.from_file("speaker_arabic.wav")
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        pcm_data = audio.raw_data
        
        # Send audio in chunks
        chunk_size = 4096
        for i in range(0, len(pcm_data), chunk_size):
            chunk = pcm_data[i:i + chunk_size]
            await websocket.send(chunk)
            await asyncio.sleep(0.1)  # Simulate real-time
        
        # Listen for results
        while True:
            response = await websocket.recv()
            message = json.loads(response)
            
            if message["type"] == "transcript":
                print(f"Transcript: {message['text']}")
            elif message["type"] == "complete":
                break

asyncio.run(stream_audio())
```

### JavaScript Client Example

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/asr-stream');

ws.onopen = function() {
    // Send configuration
    const config = {
        language_code: "ar-EG",
        sample_rate_hertz: 16000,
        encoding: "LINEAR16"
    };
    ws.send(JSON.stringify(config));
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    if (message.type === 'metadata') {
        console.log('Server ready:', message);
    } else if (message.type === 'transcript') {
        console.log('Transcript:', message.text);
    } else if (message.type === 'complete') {
        console.log('Transcription complete');
    }
};

// Send audio data (assuming you have PCM data)
function sendAudioChunk(pcmData) {
    ws.send(pcmData);
}
```

## Error Handling

### Common Errors

1. **Invalid Configuration**
   - Missing required fields
   - Invalid language code
   - Unsupported encoding

2. **Audio Format Issues**
   - Wrong sample rate
   - Invalid PCM format
   - Corrupted audio data

3. **Connection Issues**
   - WebSocket disconnection
   - Network timeouts
   - Server errors

### Error Response Format

```json
{
    "type": "error",
    "detail": "Specific error message"
}
```

## Testing

### Test Clients

1. **`test_streaming_websocket.py`** - Comprehensive test client
2. **`working_test_streaming_client.py`** - ffmpeg-based client
3. **`enhanced_test_streaming_client.py`** - pydub-based client
4. **`simple_test_streaming_client.py`** - Basic test client
5. **`debug_test_streaming_client.py`** - Debug-focused client

### Running Tests

```bash
# Start the ASR API server
python run.py

# Run comprehensive tests
python test_streaming_websocket.py

# Run specific test clients
python working_test_streaming_client.py
python enhanced_test_streaming_client.py
```

### Test Audio Files

- **`speaker_arabic.wav`** - Arabic audio for testing
- **`speaker.mp3`** - English audio for testing
- **`speaker_pcm.wav`** - Pre-converted PCM audio

## Performance Considerations

### Audio Chunk Size
- **Recommended**: 4096 bytes (256ms at 16kHz)
- **Minimum**: 1024 bytes (64ms at 16kHz)
- **Maximum**: 16384 bytes (1s at 16kHz)

### Latency
- **Network**: Depends on connection quality
- **Processing**: ~100-500ms per chunk
- **Total**: 200-1000ms end-to-end

### Memory Usage
- **Per Session**: ~10-50MB (depending on audio length)
- **Server**: Scales with concurrent connections

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if server is running on port 8001
   - Verify WebSocket endpoint URL

2. **Configuration Rejected**
   - Check JSON format
   - Verify required fields are present
   - Ensure language code is supported

3. **No Transcription Results**
   - Verify audio format (LINEAR16 PCM, 16kHz, mono)
   - Check audio quality and volume
   - Ensure Google Cloud credentials are valid

4. **High Latency**
   - Reduce chunk size
   - Check network connection
   - Monitor server resources

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Server Logs

Monitor server logs for detailed information:
```bash
# Run with debug logging
LOG_LEVEL=debug python run.py
```

## Security Considerations

1. **Authentication**: Currently none (add API key if needed)
2. **Rate Limiting**: Implement if required
3. **Input Validation**: Validate audio format and size
4. **Resource Limits**: Monitor memory and CPU usage

## Future Enhancements

1. **Authentication**: Add API key support
2. **Rate Limiting**: Implement connection limits
3. **Audio Formats**: Support more input formats
4. **Compression**: Add audio compression support
5. **Monitoring**: Add metrics and health checks
6. **Load Balancing**: Support multiple server instances

## API Reference

### WebSocket Endpoint

- **URL**: `ws://localhost:8001/ws/asr-stream`
- **Protocol**: WebSocket
- **Authentication**: None (currently)
- **Rate Limiting**: None (currently)

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `language_code` | string | "ar-EG" | Language for transcription |
| `sample_rate_hertz` | integer | 16000 | Audio sample rate |
| `encoding` | string | "LINEAR16" | Audio encoding format |

### Response Types

| Type | Description | Fields |
|------|-------------|--------|
| `metadata` | Configuration acknowledgment | `status`, `language_code`, `sample_rate_hertz`, `encoding` |
| `transcript` | Transcription result | `text`, `is_final`, `confidence` |
| `error` | Error message | `detail` |
| `complete` | Completion signal | None |

## Support

For issues and questions:
1. Check server logs for error details
2. Verify audio format requirements
3. Test with provided test clients
4. Review this documentation
5. Check Google Cloud Speech-to-Text API status
