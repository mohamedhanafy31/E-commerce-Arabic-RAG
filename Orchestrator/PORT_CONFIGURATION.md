# Port Configuration Summary

## 🚀 Service Port Breakdown

| Service | Port | Protocol | Description |
|---------|------|----------|-------------|
| **ASR API** | 8001 | WebSocket | Speech-to-Text transcription service |
| **RAG System** | 8002 | HTTP | Retrieval-Augmented Generation for Q&A |
| **TTS API** | 8003 | WebSocket | Text-to-Speech synthesis service |
| **Orchestrator** | 8004 | HTTP/WebSocket | Main coordination service |

## 🔗 Service URLs

- **ASR WebSocket**: `ws://localhost:8001/ws/asr-stream`
- **RAG HTTP**: `http://localhost:8002/query`
- **TTS WebSocket**: `ws://localhost:8003/ws/tts-stream`
- **Orchestrator**: `http://localhost:8004` (HTTP) / `ws://localhost:8004/ws/conversation` (WebSocket)

## 🌐 Client Access Points

- **Test Client**: `http://localhost:8004/test`
- **API Documentation**: `http://localhost:8004/docs`
- **Health Check**: `http://localhost:8004/health`
- **WebSocket Endpoint**: `ws://localhost:8004/ws/conversation`

## ⚙️ Configuration Files Updated

- `app/core/config.py` - Service URLs and port settings
- `.env.example` - Environment variable examples
- `.env` - Current environment configuration
- `README.md` - Architecture diagram and documentation
- `static/test_client.html` - WebSocket URL
- `app/main.py` - Fallback HTML WebSocket URL
- `activate_env.sh` - Help text URLs

## 🎯 Ready to Run

All services are now configured with the correct port assignments and the Orchestrator is ready to coordinate the complete conversational flow!
