# Orchestrator Conversational System

A FastAPI-based orchestration service that manages the complete conversational flow: **Audio Input → ASR (streaming transcription) → RAG (text response) → TTS (streaming audio output)**.

## 🏗️ Architecture Overview

The Orchestrator coordinates three existing APIs to create a seamless conversational experience:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │───▶│   Orchestrator  │───▶│   ASR API       │
│   (Audio)       │    │   (Port 8004)   │    │   (Port 8001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   RAG System    │
                       │   (Port 8002)   │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   TTS API       │
                       │   (Port 8003)   │
                       └─────────────────┘
```

### Flow Description

1. **Audio Streaming**: Client sends audio chunks via WebSocket
2. **ASR Processing**: Real-time transcription using Google Cloud Speech-to-Text
3. **RAG Generation**: Context-aware text generation using Gemini API
4. **TTS Synthesis**: Text-to-speech conversion with Arabic voice support
5. **Audio Streaming**: Real-time audio response back to client

## 🚀 Features

- **Real-time Audio Processing**: Stream audio input and output for low latency
- **Arabic Language Support**: Optimized for Arabic speech recognition and synthesis
- **Conversation History**: Maintains context across multiple turns
- **Session Management**: Handles multiple concurrent conversations
- **Error Recovery**: Robust error handling with retry mechanisms
- **WebSocket Protocol**: Efficient bidirectional communication
- **Docker Support**: Easy deployment and scaling

## 📁 Project Structure

```
Orchestrator/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app and WebSocket endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration settings
│   │   └── logging.py             # Logging setup
│   ├── services/
│   │   ├── __init__.py
│   │   ├── asr_client.py          # ASR WebSocket client
│   │   ├── rag_client.py          # RAG HTTP client
│   │   ├── tts_client.py          # TTS WebSocket client
│   │   └── orchestrator.py        # Main orchestration logic
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic models
│   └── utils/
│       ├── __init__.py
│       └── session_manager.py     # Conversation history management
├── .env.example
├── requirements.txt
├── run.py
├── Dockerfile
└── README.md
```

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- Docker (optional)
- Running ASR API (port 8001)
- Running RAG System (port 8000)
- Running TTS API (port 8003)

### Local Installation

1. **Clone and navigate to the project:**
   ```bash
   cd Orchestrator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application:**
   ```bash
   python run.py
   ```

### Docker Installation

1. **Build the image:**
   ```bash
   docker build -t orchestrator .
   ```

2. **Run the container:**
   ```bash
   docker run -d --name orchestrator \
     -p 8004:8004 \
     -e ASR_SERVICE_URL=ws://host.docker.internal:8001 \
     -e RAG_SERVICE_URL=http://host.docker.internal:8000 \
     -e TTS_SERVICE_URL=ws://host.docker.internal:8003 \
     orchestrator
   ```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8004` | Server port |
| `ASR_SERVICE_URL` | `ws://localhost:8001` | ASR API WebSocket URL |
| `RAG_SERVICE_URL` | `http://localhost:8000` | RAG System HTTP URL |
| `TTS_SERVICE_URL` | `ws://localhost:8003` | TTS API WebSocket URL |
| `AUDIO_SAMPLE_RATE` | `16000` | Audio sample rate |
| `AUDIO_FORMAT` | `LINEAR16` | Audio format |
| `DEFAULT_LANGUAGE_CODE` | `ar-EG` | Default language for ASR |
| `TTS_LANGUAGE_CODE` | `ar-XA` | Language for TTS |
| `MAX_CONCURRENT_SESSIONS` | `100` | Maximum concurrent sessions |
| `SESSION_TIMEOUT_SECONDS` | `300` | Session timeout |

### Service Port Configuration

**Important**: The RAG System and TTS API both default to port 8000. You need to change one of them:

**Option 1**: Change TTS API port to 8003
```bash
# In TTS API
export PORT=8003
```

**Option 2**: Change RAG System port to 8001
```bash
# In RAG System
export PORT=8001
```

## 🌐 API Endpoints

### WebSocket Endpoint

- **URL**: `ws://localhost:8004/ws/conversation`
- **Protocol**: WebSocket with JSON and binary messages

### HTTP Endpoints

- **GET** `/` - System information
- **GET** `/health` - Health check
- **GET** `/stats` - System statistics
- **GET** `/test` - Simple test page
- **GET** `/docs` - API documentation

## 📡 WebSocket Protocol

### Connection Flow

1. **Client connects** to WebSocket
2. **Server sends ready message**:
   ```json
   {
     "type": "ready",
     "session_id": "uuid-here",
     "audio_config": {
       "language_code": "ar-EG",
       "sample_rate_hertz": 16000,
       "encoding": "LINEAR16",
       "channels": 1
     }
   }
   ```

3. **Client sends audio chunks** (binary data)
4. **Client sends end signal**:
   ```json
   {"type": "audio_end"}
   ```

5. **Server streams responses**:
   - Transcript messages
   - RAG response messages
   - Audio chunks (TTS output)
   - State updates
   - Completion message

### Message Types

#### Transcript Message
```json
{
  "type": "transcript",
  "text": "مرحبا بك",
  "is_final": true,
  "confidence": 0.95
}
```

#### RAG Response Message
```json
{
  "type": "rag_response",
  "text": "أهلاً وسهلاً! كيف يمكنني مساعدتك اليوم؟",
  "sources": [...],
  "processing_time_ms": 1200
}
```

#### Audio Chunk Message
```json
{
  "type": "audio_chunk_tts",
  "audio_data": "base64-encoded-audio",
  "chunk_index": 0,
  "is_final_chunk": false
}
```

#### State Update Message
```json
{
  "type": "state_update",
  "state": "speaking",
  "previous_state": "processing"
}
```

#### Error Message
```json
{
  "type": "error",
  "error_code": "asr_failed",
  "detail": "ASR service unavailable"
}
```

#### Complete Message
```json
{
  "type": "complete",
  "session_id": "uuid-here",
  "total_processing_time_ms": 5000
}
```

## 🎯 Usage Examples

### JavaScript Client Example

```javascript
const ws = new WebSocket('ws://localhost:8004/ws/conversation');

ws.onopen = function() {
    console.log('Connected to Orchestrator');
};

ws.onmessage = function(event) {
    try {
        const data = JSON.parse(event.data);
        console.log('Received:', data);
        
        switch(data.type) {
            case 'ready':
                console.log('Session ready:', data.session_id);
                break;
            case 'transcript':
                console.log('Transcript:', data.text);
                break;
            case 'rag_response':
                console.log('RAG Response:', data.text);
                break;
            case 'audio_chunk_tts':
                // Play audio chunk
                playAudioChunk(data.audio_data);
                break;
            case 'complete':
                console.log('Conversation complete');
                break;
        }
    } catch (e) {
        // Binary audio data
        console.log('Received binary data:', event.data.length, 'bytes');
    }
};

// Send audio chunk
function sendAudioChunk(audioData) {
    ws.send(audioData);
}

// End audio input
function endAudioInput() {
    ws.send(JSON.stringify({type: 'audio_end'}));
}
```

### Python Client Example

```python
import asyncio
import websockets
import json

async def orchestrator_client():
    uri = "ws://localhost:8004/ws/conversation"
    
    async with websockets.connect(uri) as websocket:
        # Receive ready message
        ready_msg = await websocket.recv()
        ready_data = json.loads(ready_msg)
        session_id = ready_data['session_id']
        print(f"Session ready: {session_id}")
        
        # Send audio chunks (example)
        audio_chunks = [b'audio_data_here']  # Your audio data
        
        for chunk in audio_chunks:
            await websocket.send(chunk)
        
        # End audio input
        await websocket.send(json.dumps({"type": "audio_end"}))
        
        # Receive responses
        while True:
            try:
                message = await websocket.recv()
                
                try:
                    data = json.loads(message)
                    print(f"Received: {data}")
                except json.JSONDecodeError:
                    print(f"Received binary data: {len(message)} bytes")
                    
            except websockets.exceptions.ConnectionClosed:
                break

# Run client
asyncio.run(orchestrator_client())
```

## 🔧 Development

### Running in Development Mode

```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with auto-reload
python run.py
```

### Testing

1. **Health Check**:
   ```bash
   curl http://localhost:8004/health
   ```

2. **WebSocket Test**:
   Visit `http://localhost:8004/test` for a simple test interface

3. **Statistics**:
   ```bash
   curl http://localhost:8004/stats
   ```

### Logging

The system uses structured logging with different levels:

- **DEBUG**: Detailed debugging information
- **INFO**: General information about system operation
- **WARNING**: Warning messages for non-critical issues
- **ERROR**: Error messages for failures

Logs include session IDs for tracking individual conversations.

## 🐛 Troubleshooting

### Common Issues

1. **Service Connection Failed**:
   - Check if ASR, RAG, and TTS services are running
   - Verify port configurations
   - Check network connectivity

2. **WebSocket Connection Failed**:
   - Ensure port 8004 is available
   - Check firewall settings
   - Verify WebSocket URL

3. **Audio Processing Issues**:
   - Verify audio format (LINEAR16, 16kHz, mono)
   - Check audio chunk size
   - Ensure proper audio encoding

4. **Session Timeout**:
   - Increase `SESSION_TIMEOUT_SECONDS`
   - Check for long-running operations
   - Monitor session cleanup

### Debug Mode

Enable debug mode for detailed logging:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python run.py
```

### Service Dependencies

Ensure all required services are running:

```bash
# Check ASR API
curl http://localhost:8001/health

# Check RAG System
curl http://localhost:8000/health

# Check TTS API
curl http://localhost:8003/health
```

## 📊 Monitoring

### Health Endpoint

```bash
curl http://localhost:8004/health
```

Response:
```json
{
  "status": "healthy",
  "services": {
    "orchestrator": "healthy",
    "session_manager": "healthy",
    "asr_client_manager": "healthy",
    "rag_client_manager": "healthy",
    "tts_client_manager": "healthy"
  },
  "active_sessions": 5,
  "max_sessions": 100
}
```

### Statistics Endpoint

```bash
curl http://localhost:8004/stats
```

Response:
```json
{
  "sessions": {
    "total_sessions": 10,
    "total_conversation_turns": 45,
    "state_distribution": {
      "idle": 8,
      "listening": 1,
      "processing": 1
    }
  },
  "active_conversations": 2,
  "configuration": {
    "max_concurrent_sessions": 100,
    "session_timeout_seconds": 300,
    "audio_sample_rate": 16000
  }
}
```

## 🚀 Deployment

### Docker Compose Example

```yaml
version: '3.8'
services:
  orchestrator:
    build: ./Orchestrator
    ports:
      - "8004:8004"
    environment:
      - ASR_SERVICE_URL=ws://asr-api:8001
      - RAG_SERVICE_URL=http://rag-system:8000
      - TTS_SERVICE_URL=ws://tts-api:8003
    depends_on:
      - asr-api
      - rag-system
      - tts-api
    restart: unless-stopped

  asr-api:
    build: ./ASR_API
    ports:
      - "8001:8001"
    restart: unless-stopped

  rag-system:
    build: ./simple-rag
    ports:
      - "8000:8000"
    restart: unless-stopped

  tts-api:
    build: ./TTS_API
    ports:
      - "8003:8003"
    restart: unless-stopped
```

### Production Considerations

1. **Load Balancing**: Use multiple Orchestrator instances behind a load balancer
2. **Session Persistence**: Consider Redis for session storage in multi-instance deployments
3. **Monitoring**: Add Prometheus metrics and Grafana dashboards
4. **Security**: Implement authentication and rate limiting
5. **Scaling**: Use Kubernetes for container orchestration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- FastAPI team for the web framework
- Google Cloud for ASR and TTS services
- Gemini API for text generation
- WebSocket community for real-time communication standards
