# Orchestrator Integration Guide

A comprehensive guide for integrating with the Orchestrator Conversational AI System - the central coordination service that manages the complete conversational flow.

## 🏗️ Overview

The Orchestrator is the **central hub** that coordinates three microservices to provide a complete conversational AI experience:

```
Client (Audio) → Orchestrator (8004) → ASR (8001) → RAG (8002) → TTS (8003) → Client (Audio)
```

### **What the Orchestrator Does**
- **Manages WebSocket connections** for real-time communication
- **Coordinates ASR, RAG, and TTS services** in sequence
- **Handles session management** and conversation history
- **Provides error recovery** and retry mechanisms
- **Streams responses** back to clients in real-time

## 🚀 Quick Start

### **1. Prerequisites**
Ensure all dependent services are running:
```bash
# Check service health
curl http://localhost:8001/health  # ASR API
curl http://localhost:8002/health  # RAG System  
curl http://localhost:8003/health  # TTS API
```

### **2. Start the Orchestrator**
```bash
cd Orchestrator
conda activate orchestrator
python run.py
```

### **3. Test Connection**
```bash
curl http://localhost:8004/health
```

## 🌐 Integration Methods

### **Method 1: WebSocket Integration (Recommended)**

The Orchestrator provides a WebSocket endpoint for real-time conversational AI:

#### **WebSocket URL**
```
ws://localhost:8004/ws/conversation
```

#### **Connection Flow**
1. **Connect** to WebSocket
2. **Receive ready message** with session ID
3. **Send audio chunks** (binary data)
4. **Send audio_end signal** when done
5. **Receive responses** (transcript, RAG response, TTS audio)

#### **JavaScript Integration**
```javascript
class OrchestratorClient {
    constructor(url = 'ws://localhost:8004/ws/conversation') {
        this.url = url;
        this.ws = null;
        this.sessionId = null;
        this.audioContext = null;
        this.mediaRecorder = null;
        this.isRecording = false;
    }

    async connect() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => {
                console.log('Connected to Orchestrator');
                resolve();
            };
            
            this.ws.onmessage = (event) => {
                this.handleMessage(event);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };
            
            this.ws.onclose = () => {
                console.log('Disconnected from Orchestrator');
            };
        });
    }

    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('Received:', data);
            
            switch(data.type) {
                case 'ready':
                    this.sessionId = data.session_id;
                    console.log('Session ready:', this.sessionId);
                    this.onReady(data.audio_config);
                    break;
                    
                case 'transcript':
                    this.onTranscript(data.text, data.is_final, data.confidence);
                    break;
                    
                case 'rag_response':
                    this.onRAGResponse(data.text, data.sources);
                    break;
                    
                case 'audio_chunk_tts':
                    this.onTTSAudio(data.audio_data, data.chunk_index, data.is_final_chunk);
                    break;
                    
                case 'state_update':
                    this.onStateUpdate(data.state, data.previous_state);
                    break;
                    
                case 'complete':
                    this.onComplete(data.total_processing_time_ms);
                    break;
                    
                case 'error':
                    this.onError(data.error_code, data.detail);
                    break;
            }
        } catch (e) {
            // Binary audio data
            console.log('Received binary audio data:', event.data.length, 'bytes');
            this.onBinaryAudio(event.data);
        }
    }

    // Event handlers (override these in your implementation)
    onReady(audioConfig) {
        console.log('Audio config:', audioConfig);
    }

    onTranscript(text, isFinal, confidence) {
        console.log('Transcript:', text, isFinal ? '(final)' : '(interim)');
    }

    onRAGResponse(text, sources) {
        console.log('RAG Response:', text);
        if (sources) console.log('Sources:', sources);
    }

    onTTSAudio(audioData, chunkIndex, isFinalChunk) {
        console.log('TTS Audio chunk:', chunkIndex, isFinalChunk ? '(final)' : '');
        // Play audio chunk
        this.playAudioChunk(audioData);
    }

    onStateUpdate(state, previousState) {
        console.log('State changed:', previousState, '→', state);
    }

    onComplete(totalTime) {
        console.log('Conversation complete in', totalTime, 'ms');
    }

    onError(errorCode, detail) {
        console.error('Error:', errorCode, detail);
    }

    onBinaryAudio(audioData) {
        console.log('Binary audio data received');
    }

    // Audio recording methods
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0 && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(event.data);
                }
            };
            
            this.mediaRecorder.start(100); // Send chunks every 100ms
            this.isRecording = true;
            console.log('Recording started');
        } catch (error) {
            console.error('Error starting recording:', error);
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Send audio end signal
            this.ws.send(JSON.stringify({ type: 'audio_end' }));
            console.log('Recording stopped');
        }
    }

    // Audio playback methods
    playAudioChunk(audioData) {
        // Convert base64 to audio and play
        const audio = new Audio(`data:audio/mp3;base64,${audioData}`);
        audio.play().catch(console.error);
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage example
const client = new OrchestratorClient();

// Override event handlers
client.onReady = (audioConfig) => {
    document.getElementById('status').textContent = 'Ready to talk';
    document.getElementById('startBtn').disabled = false;
};

client.onTranscript = (text, isFinal) => {
    const transcriptDiv = document.getElementById('transcript');
    if (isFinal) {
        transcriptDiv.innerHTML += `<div class="final">${text}</div>`;
    } else {
        transcriptDiv.innerHTML = `<div class="interim">${text}</div>`;
    }
};

client.onRAGResponse = (text) => {
    document.getElementById('response').textContent = text;
};

client.onTTSAudio = (audioData) => {
    const audio = new Audio(`data:audio/mp3;base64,${audioData}`);
    audio.play();
};

// Connect and start
client.connect().then(() => {
    document.getElementById('startBtn').onclick = () => client.startRecording();
    document.getElementById('stopBtn').onclick = () => client.stopRecording();
});
```

#### **Python Integration**
```python
import asyncio
import websockets
import json
import base64
from typing import Optional

class OrchestratorClient:
    def __init__(self, uri: str = "ws://localhost:8004/ws/conversation"):
        self.uri = uri
        self.websocket = None
        self.session_id = None
        
    async def connect(self):
        """Connect to the Orchestrator WebSocket"""
        self.websocket = await websockets.connect(self.uri)
        print("Connected to Orchestrator")
        
    async def handle_messages(self):
        """Handle incoming messages"""
        async for message in self.websocket:
            try:
                data = json.loads(message)
                await self.handle_json_message(data)
            except json.JSONDecodeError:
                # Binary audio data
                await self.handle_binary_audio(message)
                
    async def handle_json_message(self, data: dict):
        """Handle JSON messages"""
        message_type = data.get('type')
        
        if message_type == 'ready':
            self.session_id = data['session_id']
            print(f"Session ready: {self.session_id}")
            await self.on_ready(data['audio_config'])
            
        elif message_type == 'transcript':
            await self.on_transcript(
                data['text'], 
                data.get('is_final', False),
                data.get('confidence')
            )
            
        elif message_type == 'rag_response':
            await self.on_rag_response(
                data['text'],
                data.get('sources', [])
            )
            
        elif message_type == 'audio_chunk_tts':
            await self.on_tts_audio(
                data['audio_data'],
                data.get('chunk_index'),
                data.get('is_final_chunk', False)
            )
            
        elif message_type == 'state_update':
            await self.on_state_update(
                data['state'],
                data.get('previous_state')
            )
            
        elif message_type == 'complete':
            await self.on_complete(data.get('total_processing_time_ms'))
            
        elif message_type == 'error':
            await self.on_error(data['error_code'], data['detail'])
            
    async def handle_binary_audio(self, audio_data: bytes):
        """Handle binary audio data"""
        print(f"Received binary audio: {len(audio_data)} bytes")
        await self.on_binary_audio(audio_data)
        
    async def send_audio_chunk(self, audio_data: bytes):
        """Send audio chunk to Orchestrator"""
        if self.websocket:
            await self.websocket.send(audio_data)
            
    async def end_audio_input(self):
        """Signal end of audio input"""
        if self.websocket:
            await self.websocket.send(json.dumps({"type": "audio_end"}))
            
    # Event handlers (override these)
    async def on_ready(self, audio_config: dict):
        print("Audio config:", audio_config)
        
    async def on_transcript(self, text: str, is_final: bool, confidence: Optional[float]):
        status = "final" if is_final else "interim"
        print(f"Transcript ({status}): {text}")
        
    async def on_rag_response(self, text: str, sources: list):
        print(f"RAG Response: {text}")
        if sources:
            print(f"Sources: {sources}")
            
    async def on_tts_audio(self, audio_data: str, chunk_index: Optional[int], is_final_chunk: bool):
        print(f"TTS Audio chunk {chunk_index}: {'final' if is_final_chunk else 'continuing'}")
        # Play audio chunk
        await self.play_audio_chunk(audio_data)
        
    async def on_state_update(self, state: str, previous_state: Optional[str]):
        print(f"State changed: {previous_state} → {state}")
        
    async def on_complete(self, total_time: Optional[int]):
        print(f"Conversation complete in {total_time}ms")
        
    async def on_error(self, error_code: str, detail: str):
        print(f"Error {error_code}: {detail}")
        
    async def on_binary_audio(self, audio_data: bytes):
        print("Binary audio data received")
        
    async def play_audio_chunk(self, audio_data: str):
        """Play audio chunk (implement based on your audio library)"""
        # Example using pygame
        # import pygame
        # pygame.mixer.init()
        # audio_bytes = base64.b64decode(audio_data)
        # pygame.mixer.music.load(io.BytesIO(audio_bytes))
        # pygame.mixer.music.play()
        pass
        
    async def disconnect(self):
        """Disconnect from Orchestrator"""
        if self.websocket:
            await self.websocket.close()

# Usage example
async def main():
    client = OrchestratorClient()
    
    # Override event handlers
    async def on_transcript(text, is_final, confidence):
        if is_final:
            print(f"Final transcript: {text}")
        else:
            print(f"Interim transcript: {text}")
    
    async def on_rag_response(text, sources):
        print(f"Assistant: {text}")
    
    # Set custom handlers
    client.on_transcript = on_transcript
    client.on_rag_response = on_rag_response
    
    # Connect and start
    await client.connect()
    
    # Start message handling
    message_task = asyncio.create_task(client.handle_messages())
    
    # Example: Send some audio chunks
    # audio_chunks = [b'audio_data_here']  # Your audio data
    # for chunk in audio_chunks:
    #     await client.send_audio_chunk(chunk)
    # await client.end_audio_input()
    
    # Wait for messages
    await message_task

if __name__ == "__main__":
    asyncio.run(main())
```

### **Method 2: HTTP API Integration**

The Orchestrator also provides HTTP endpoints for system management:

#### **Health Check**
```bash
curl http://localhost:8004/health
```

#### **System Statistics**
```bash
curl http://localhost:8004/stats
```

#### **System Information**
```bash
curl http://localhost:8004/
```

## 📡 WebSocket Protocol Details

### **Message Types**

#### **1. Ready Message (Server → Client)**
```json
{
  "type": "ready",
  "session_id": "uuid-here",
  "audio_config": {
    "language_code": "ar-EG",
    "sample_rate_hertz": 16000,
    "encoding": "LINEAR16",
    "channels": 1
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### **2. Audio Chunk (Client → Server)**
- **Type**: Binary data
- **Format**: Raw audio bytes
- **Frequency**: Send chunks every 100-200ms

#### **3. Audio End Signal (Client → Server)**
```json
{
  "type": "audio_end"
}
```

#### **4. Transcript Message (Server → Client)**
```json
{
  "type": "transcript",
  "text": "مرحبا بك",
  "is_final": true,
  "confidence": 0.95,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### **5. RAG Response (Server → Client)**
```json
{
  "type": "rag_response",
  "text": "أهلاً وسهلاً! كيف يمكنني مساعدتك اليوم؟",
  "sources": [
    {
      "filename": "document.pdf",
      "chunk_index": 0,
      "similarity_score": 0.85,
      "preview": "مرحبا بك في نظام..."
    }
  ],
  "processing_time_ms": 1200,
  "model_used": "kimo_gemini",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### **6. TTS Audio Chunk (Server → Client)**
```json
{
  "type": "audio_chunk_tts",
  "audio_data": "base64-encoded-audio",
  "chunk_index": 0,
  "is_final_chunk": false,
  "sentence_index": 0,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### **7. State Update (Server → Client)**
```json
{
  "type": "state_update",
  "state": "speaking",
  "previous_state": "processing",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### **8. Error Message (Server → Client)**
```json
{
  "type": "error",
  "error_code": "asr_failed",
  "detail": "ASR service unavailable",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### **9. Complete Message (Server → Client)**
```json
{
  "type": "complete",
  "session_id": "uuid-here",
  "total_processing_time_ms": 5000,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### **Conversation States**
- **`idle`**: Ready for new conversation
- **`listening`**: Receiving audio input
- **`processing`**: Processing ASR → RAG → TTS
- **`speaking`**: Playing TTS audio
- **`error`**: Error occurred

## ⚙️ Configuration

### **Environment Variables**

Create a `.env` file in the Orchestrator directory:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8004
DEBUG=false
RELOAD=true

# Service URLs
ASR_SERVICE_URL=ws://localhost:8001
RAG_SERVICE_URL=http://localhost:8002
TTS_SERVICE_URL=ws://localhost:8003

# Audio Configuration
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
AUDIO_FORMAT=LINEAR16
AUDIO_CHUNK_SIZE=1024

# Language Configuration
DEFAULT_LANGUAGE_CODE=ar-EG
TTS_LANGUAGE_CODE=ar-XA
TTS_VOICE_GENDER=male

# Session Configuration
MAX_SESSION_HISTORY=10
SESSION_TIMEOUT_SECONDS=300
MAX_CONCURRENT_SESSIONS=100

# Timeout Configuration
ASR_TIMEOUT_SECONDS=30
RAG_TIMEOUT_SECONDS=60
TTS_TIMEOUT_SECONDS=30
WEBSOCKET_TIMEOUT_SECONDS=300

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY_SECONDS=1.0
EXPONENTIAL_BACKOFF=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s %(levelname)s [%(name)s] %(message)s

# CORS Configuration
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=true

# Audio Processing Configuration
SILENCE_DETECTION_THRESHOLD=0.1
SILENCE_DURATION_SECONDS=2.0
MAX_AUDIO_DURATION_SECONDS=60

# Performance Configuration
ENABLE_AUDIO_PREPROCESSING=true
ENABLE_SENTENCE_STREAMING=true
ENABLE_CONVERSATION_HISTORY=true
```

## 🧪 Testing

### **1. Web Interface Test**
Visit `http://localhost:8004/test` for a built-in test client.

### **2. Health Check**
```bash
curl http://localhost:8004/health
```

### **3. Statistics**
```bash
curl http://localhost:8004/stats
```

### **4. WebSocket Test**
```javascript
// Simple WebSocket test
const ws = new WebSocket('ws://localhost:8004/ws/conversation');
ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Received:', event.data);
ws.onerror = (error) => console.error('Error:', error);
```

## 🔧 Advanced Integration

### **Custom Event Handlers**

You can extend the Orchestrator client with custom event handlers:

```javascript
class CustomOrchestratorClient extends OrchestratorClient {
    onTranscript(text, isFinal, confidence) {
        // Custom transcript handling
        if (isFinal) {
            this.updateTranscriptDisplay(text);
            this.analyzeSentiment(text);
        }
    }
    
    onRAGResponse(text, sources) {
        // Custom RAG response handling
        this.updateResponseDisplay(text);
        this.highlightSources(sources);
        this.logConversation(text);
    }
    
    onStateUpdate(state, previousState) {
        // Custom state handling
        this.updateUIState(state);
        this.showProgressIndicator(state);
    }
    
    // Custom methods
    updateTranscriptDisplay(text) {
        document.getElementById('transcript').textContent = text;
    }
    
    analyzeSentiment(text) {
        // Implement sentiment analysis
    }
    
    updateResponseDisplay(text) {
        document.getElementById('response').textContent = text;
    }
    
    highlightSources(sources) {
        // Highlight relevant document sources
    }
    
    logConversation(text) {
        // Log conversation for analytics
    }
    
    updateUIState(state) {
        document.body.className = `state-${state}`;
    }
    
    showProgressIndicator(state) {
        const indicator = document.getElementById('progress');
        indicator.style.display = state === 'processing' ? 'block' : 'none';
    }
}
```

### **Error Handling**

```javascript
class RobustOrchestratorClient extends OrchestratorClient {
    constructor(url) {
        super(url);
        this.retryCount = 0;
        this.maxRetries = 3;
        this.retryDelay = 1000;
    }
    
    async connect() {
        try {
            await super.connect();
            this.retryCount = 0; // Reset on successful connection
        } catch (error) {
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                console.log(`Connection failed, retrying in ${this.retryDelay}ms (attempt ${this.retryCount})`);
                await this.delay(this.retryDelay);
                return this.connect();
            } else {
                throw new Error(`Failed to connect after ${this.maxRetries} attempts`);
            }
        }
    }
    
    onError(errorCode, detail) {
        console.error(`Orchestrator error: ${errorCode} - ${detail}`);
        
        switch (errorCode) {
            case 'asr_failed':
                this.handleASRError(detail);
                break;
            case 'rag_failed':
                this.handleRAGError(detail);
                break;
            case 'tts_failed':
                this.handleTTSError(detail);
                break;
            default:
                this.handleGenericError(errorCode, detail);
        }
    }
    
    handleASRError(detail) {
        console.log('ASR service error, attempting recovery...');
        // Implement ASR error recovery
    }
    
    handleRAGError(detail) {
        console.log('RAG service error, attempting recovery...');
        // Implement RAG error recovery
    }
    
    handleTTSError(detail) {
        console.log('TTS service error, attempting recovery...');
        // Implement TTS error recovery
    }
    
    handleGenericError(errorCode, detail) {
        console.log('Generic error, showing user message...');
        this.showErrorMessage(`Error: ${detail}`);
    }
    
    showErrorMessage(message) {
        // Show user-friendly error message
        const errorDiv = document.getElementById('error');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        // Hide after 5 seconds
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

## 🐳 Docker Integration

### **Docker Compose Example**

```yaml
version: '3.8'
services:
  orchestrator:
    build: ./Orchestrator
    ports:
      - "8004:8004"
    environment:
      - ASR_SERVICE_URL=ws://asr-api:8001
      - RAG_SERVICE_URL=http://rag-system:8002
      - TTS_SERVICE_URL=ws://tts-api:8003
      - DEBUG=false
      - LOG_LEVEL=INFO
    depends_on:
      - asr-api
      - rag-system
      - tts-api
    restart: unless-stopped
    networks:
      - conversational-ai

  asr-api:
    build: ./ASR_API
    ports:
      - "8001:8001"
    networks:
      - conversational-ai

  rag-system:
    build: ./simple-rag
    ports:
      - "8002:8002"
    networks:
      - conversational-ai

  tts-api:
    build: ./TTS_API
    ports:
      - "8003:8003"
    networks:
      - conversational-ai

networks:
  conversational-ai:
    driver: bridge
```

### **Docker Run Command**

```bash
docker run -d --name orchestrator \
  -p 8004:8004 \
  -e ASR_SERVICE_URL=ws://host.docker.internal:8001 \
  -e RAG_SERVICE_URL=http://host.docker.internal:8002 \
  -e TTS_SERVICE_URL=ws://host.docker.internal:8003 \
  orchestrator
```

## 📊 Monitoring and Analytics

### **Session Tracking**

```javascript
class AnalyticsOrchestratorClient extends OrchestratorClient {
    constructor(url) {
        super(url);
        this.sessionData = {
            startTime: null,
            endTime: null,
            transcriptCount: 0,
            responseCount: 0,
            errorCount: 0,
            totalProcessingTime: 0
        };
    }
    
    onReady(audioConfig) {
        super.onReady(audioConfig);
        this.sessionData.startTime = new Date();
        this.trackEvent('session_started', { audioConfig });
    }
    
    onTranscript(text, isFinal, confidence) {
        super.onTranscript(text, isFinal, confidence);
        if (isFinal) {
            this.sessionData.transcriptCount++;
            this.trackEvent('transcript_final', { 
                text, 
                confidence,
                length: text.length 
            });
        }
    }
    
    onRAGResponse(text, sources) {
        super.onRAGResponse(text, sources);
        this.sessionData.responseCount++;
        this.trackEvent('rag_response', { 
            text, 
            sourcesCount: sources.length,
            responseLength: text.length 
        });
    }
    
    onComplete(totalTime) {
        super.onComplete(totalTime);
        this.sessionData.endTime = new Date();
        this.sessionData.totalProcessingTime = totalTime;
        
        this.trackEvent('session_completed', this.sessionData);
        this.sendAnalytics();
    }
    
    onError(errorCode, detail) {
        super.onError(errorCode, detail);
        this.sessionData.errorCount++;
        this.trackEvent('error_occurred', { errorCode, detail });
    }
    
    trackEvent(eventName, data) {
        // Send to analytics service
        console.log(`Analytics: ${eventName}`, data);
        // Implement your analytics tracking here
    }
    
    sendAnalytics() {
        // Send session analytics to your analytics service
        console.log('Session Analytics:', this.sessionData);
    }
}
```

## 🔍 Troubleshooting

### **Common Issues**

#### **1. WebSocket Connection Failed**
```bash
# Check if Orchestrator is running
curl http://localhost:8004/health

# Check port availability
netstat -tulpn | grep 8004

# Check firewall settings
sudo ufw status
```

#### **2. Service Dependencies Not Available**
```bash
# Check all services
curl http://localhost:8001/health  # ASR
curl http://localhost:8002/health  # RAG
curl http://localhost:8003/health  # TTS
```

#### **3. Audio Processing Issues**
- Ensure audio format is LINEAR16, 16kHz, mono
- Check audio chunk size (recommended: 100-200ms)
- Verify microphone permissions

#### **4. Session Timeout**
- Increase `SESSION_TIMEOUT_SECONDS` in configuration
- Check for long-running operations
- Monitor session cleanup

### **Debug Mode**

Enable debug logging:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python run.py
```

### **Log Analysis**

Check logs for detailed information:

```bash
tail -f logs/orchestrator.log
tail -f logs/websocket.log
tail -f logs/errors.log
```

## 🚀 Production Deployment

### **Load Balancing**

Use multiple Orchestrator instances behind a load balancer:

```nginx
upstream orchestrator_backend {
    server orchestrator1:8004;
    server orchestrator2:8004;
    server orchestrator3:8004;
}

server {
    listen 80;
    location / {
        proxy_pass http://orchestrator_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **Session Persistence**

For multi-instance deployments, use Redis for session storage:

```python
# In your Orchestrator configuration
REDIS_URL=redis://redis:6379/0
SESSION_STORAGE_TYPE=redis
```

### **Monitoring**

Add Prometheus metrics and Grafana dashboards:

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
websocket_connections = Gauge('websocket_connections_total', 'Total WebSocket connections')
conversation_duration = Histogram('conversation_duration_seconds', 'Conversation duration')
errors_total = Counter('errors_total', 'Total errors', ['error_type'])
```

## 📚 Additional Resources

- **Orchestrator README**: `Orchestrator/README.md`
- **Port Configuration**: `Orchestrator/PORT_CONFIGURATION.md`
- **API Documentation**: `http://localhost:8004/docs`
- **Test Client**: `http://localhost:8004/test`

## 🤝 Support

For integration support:
1. Check the troubleshooting section
2. Review the logs for error details
3. Test with the built-in test client
4. Verify all service dependencies are running

**Ready to integrate with the Orchestrator! 🚀**
