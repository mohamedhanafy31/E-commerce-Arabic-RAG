# E-commerce Arabic RAG System

A complete conversational AI system for Arabic e-commerce applications featuring real-time speech recognition, intelligent document retrieval, and natural language generation with Egyptian dialect support.

## 🏗️ System Architecture

This project consists of **4 microservices** that work together to provide a complete conversational AI experience:

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

### **Complete Flow**: `Audio Input → ASR → RAG → TTS → Audio Output`

## 🚀 Features

### **Core Capabilities**
- **Real-time Speech Recognition**: Arabic speech-to-text using Google Cloud Speech-to-Text
- **Intelligent Document Retrieval**: Arabic BERT embeddings with FAISS vector search
- **Natural Language Generation**: Context-aware responses using Gemini API
- **Text-to-Speech**: Arabic voice synthesis with streaming audio output
- **كيمو (Kimo)**: Egyptian dialect AI assistant with cultural responses

### **Technical Features**
- **GPU Optimization**: Forced CUDA usage with compatibility handling
- **WebSocket Streaming**: Low-latency real-time communication
- **Session Management**: Multiple concurrent conversations
- **Error Recovery**: Robust error handling with retry mechanisms
- **Unity Integration**: Ready-to-use Unity client for ASR
- **Docker Support**: Containerized deployment options

## 📁 Project Structure

```
E-commerce-Arabic-RAG-main/
├── simple-rag/              # RAG System (Port 8002)
│   ├── core/               # Core components
│   │   ├── embeddings.py   # Arabic BERT embeddings
│   │   ├── chunker.py     # Arabic text chunking
│   │   ├── vector_store.py # FAISS vector database
│   │   ├── generator.py    # Gemini API integration
│   │   └── file_processor.py # Document processing
│   ├── data/               # Vector store and documents
│   ├── logs/               # System logs
│   └── static/             # Web interface
├── ASR_API/                # Speech Recognition (Port 8001)
│   ├── app/                # FastAPI application
│   ├── docs/unity/         # Unity integration
│   └── pages/              # Web interface
├── TTS_API/                # Text-to-Speech (Port 8003)
│   ├── app/                # FastAPI application
│   └── test1/, test2/      # Audio samples
├── Orchestrator/           # Main coordinator (Port 8004)
│   ├── app/                # FastAPI application
│   ├── services/           # Service clients
│   └── static/             # Test client
└── README.md               # This file
```

## 🛠️ Prerequisites

### **System Requirements**
- **Python 3.8+**
- **Conda** (recommended for environment management)
- **GPU** (CUDA-compatible, mandatory as per user rules)
- **4GB+ RAM** (8GB+ recommended)
- **Google Cloud Account** (for ASR and TTS services)

### **Required Services**
- **Google Cloud Speech-to-Text API**
- **Google Cloud Text-to-Speech API**
- **Gemini API** (for text generation)

## 🔧 Installation

### **1. Clone the Repository**
```bash
git clone <repository-url>
cd E-commerce-Arabic-RAG-main
```

### **2. Set Up Conda Environments**

The project uses separate conda environments for each service:

```bash
# Check available environments
conda env list

# Available environments:
# - rag (or ecomrag)     # For RAG System
# - ASR                 # For ASR API
# - TTS-API             # For TTS API
# - orchestrator         # For Orchestrator
```

### **3. Configure Google Cloud Services**

#### **ASR API Setup**
```bash
cd ASR_API
# Place your Google Cloud credentials file as 'tts-key.json'
# Ensure Speech-to-Text API is enabled
```

#### **TTS API Setup**
```bash
cd TTS_API
# Place your Google Cloud credentials file as 'tts-key.json'
# Ensure Text-to-Speech API is enabled
```

#### **RAG System Setup**
```bash
cd simple-rag
# Get Gemini API key from: https://makersuite.google.com/app/apikey
cp env.example .env
# Edit .env with your Gemini API key
```

### **4. Install Dependencies**

#### **RAG System**
```bash
cd simple-rag
conda activate rag  # or ecomrag
pip install -r requirements.txt
```

#### **ASR API**
```bash
cd ASR_API
conda activate ASR
pip install -r requirements.txt
```

#### **TTS API**
```bash
cd TTS_API
conda activate TTS-API
pip install -r requirements.txt
```

#### **Orchestrator**
```bash
cd Orchestrator
conda activate orchestrator
pip install -r requirements.txt
```

## 🚀 Running the System

### **Start Services (in order)**

#### **1. Start RAG System**
```bash
cd simple-rag
conda activate rag
python main.py
```
- **URL**: http://localhost:8002
- **Features**: Document upload, Arabic text querying, كيمو AI assistant

#### **2. Start ASR API**
```bash
cd ASR_API
conda activate ASR
python run.py
```
- **URL**: http://localhost:8001
- **Features**: Speech recognition, WebSocket streaming

#### **3. Start TTS API**
```bash
cd TTS_API
conda activate TTS-API
python run.py
```
- **URL**: http://localhost:8003
- **Features**: Text-to-speech, Arabic voice synthesis

#### **4. Start Orchestrator**
```bash
cd Orchestrator
conda activate orchestrator
python run.py
```
- **URL**: http://localhost:8004
- **Features**: Complete conversational flow coordination

### **Service URLs**
- **RAG System**: http://localhost:8002
- **ASR API**: http://localhost:8001
- **TTS API**: http://localhost:8003
- **Orchestrator**: http://localhost:8004

## 🎯 Usage Examples

### **1. Upload Documents to RAG System**
```bash
curl -X POST "http://localhost:8002/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
```

### **2. Query Documents**
```bash
curl -X POST "http://localhost:8002/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "ما هو موضوع هذا المستند؟",
       "max_results": 5
     }'
```

### **3. Test ASR (File Upload)**
```bash
curl -X POST "http://localhost:8001/asr" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@audio.wav" \
     -F "language_code=ar-EG"
```

### **4. Test TTS**
```bash
curl -X POST "http://localhost:8003/tts" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "مرحبا بك في خدمة تحويل النص إلى كلام.",
       "language_code": "ar-XA",
       "voice_name": "ar-XA-Chirp3-HD-Achernar"
     }'
```

### **5. Complete Conversational Flow (WebSocket)**
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

## 🎮 Unity Integration

Complete Unity integration is available for ASR:

### **Files Location**
- `ASR_API/docs/unity/UnityASRClient.cs` - WebSocket client
- `ASR_API/docs/unity/ASRUI.cs` - UI controller
- `ASR_API/docs/unity/UNITY_INTEGRATION_GUIDE.md` - Complete guide

### **Quick Setup**
1. Import Unity scripts into your project
2. Configure WebSocket URL to `ws://localhost:8001/ws/asr-stream`
3. Set up audio recording permissions
4. Test with the provided UI controller

## 🔧 Configuration

### **Environment Variables**

#### **RAG System (.env)**
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8002

# Model Configuration
EMBEDDING_MODEL=NAMAA-Space/AraModernBert-Base-V1.0
GENERATION_MODEL=gemini

# GPU Configuration (mandatory)
FORCE_GPU=true
GPU_DEVICE=cuda

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

#### **ASR API**
```env
GOOGLE_APPLICATION_CREDENTIALS=./tts-key.json
DEFAULT_LANGUAGE_CODE=ar-EG
DEFAULT_SAMPLE_RATE_HERTZ=16000
```

#### **TTS API**
```env
GOOGLE_APPLICATION_CREDENTIALS=./tts-key.json
TTS_LANGUAGE_CODE=ar-XA
```

#### **Orchestrator**
```env
ASR_SERVICE_URL=ws://localhost:8001
RAG_SERVICE_URL=http://localhost:8002
TTS_SERVICE_URL=ws://localhost:8003
DEFAULT_LANGUAGE_CODE=ar-EG
TTS_LANGUAGE_CODE=ar-XA
```

## 🧪 Testing

### **Health Checks**
```bash
# Check all services
curl http://localhost:8002/health  # RAG System
curl http://localhost:8001/health  # ASR API
curl http://localhost:8003/health  # TTS API
curl http://localhost:8004/health  # Orchestrator
```

### **Web Interfaces**
- **RAG System**: http://localhost:8002/manage
- **ASR API**: http://localhost:8001/streaming-test
- **TTS API**: http://localhost:8003/
- **Orchestrator**: http://localhost:8004/test

### **GPU Testing**
```bash
cd simple-rag
conda activate rag
python test_gpu.py
```

## 🐳 Docker Deployment

### **Individual Services**
Each service includes a Dockerfile for containerized deployment:

```bash
# Build RAG System
cd simple-rag
docker build -t rag-system .

# Build ASR API
cd ASR_API
docker build -t asr-api .

# Build TTS API
cd TTS_API
docker build -t tts-api .

# Build Orchestrator
cd Orchestrator
docker build -t orchestrator .
```

### **Docker Compose**
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
    depends_on:
      - asr-api
      - rag-system
      - tts-api

  asr-api:
    build: ./ASR_API
    ports:
      - "8001:8001"
    volumes:
      - ./ASR_API/tts-key.json:/app/tts-key.json

  rag-system:
    build: ./simple-rag
    ports:
      - "8002:8002"
    volumes:
      - ./simple-rag/.env:/app/.env

  tts-api:
    build: ./TTS_API
    ports:
      - "8003:8003"
    volumes:
      - ./TTS_API/tts-key.json:/app/tts-key.json
```

## 🎯 كيمو (Kimo) - Egyptian AI Assistant

The RAG system features **كيمو**, an Egyptian dialect AI assistant that:

### **Features**
- **Egyptian Dialect**: Responds in natural Egyptian Arabic
- **Cultural Responses**: Handles Egyptian greetings and expressions
- **Context Awareness**: Provides relevant answers from uploaded documents
- **Natural Generation**: Uses Gemini API for fluent responses

### **Example Interactions**
```
User: "عامل إيه؟"
كيمو: "الحمد لله، أنا بخير. إزيك إنت؟"

User: "صباح الخير"
كيمو: "صباح النور! إزيك صباح النهاردة؟"

User: "ما هو موضوع هذا المستند؟"
كيمو: [Provides context-aware answer from uploaded documents]
```

## 🔍 Troubleshooting

### **Common Issues**

#### **1. CUDA Compatibility (Error 804)**
```bash
cd simple-rag
chmod +x fix_cuda_compatibility.sh
./fix_cuda_compatibility.sh
```

#### **2. Service Connection Failed**
- Check if all services are running on correct ports
- Verify environment variables and API keys
- Check firewall settings

#### **3. Google Cloud Authentication**
- Ensure `tts-key.json` files are in correct locations
- Verify API permissions for Speech-to-Text and Text-to-Speech
- Check service account credentials

#### **4. GPU Issues**
- Run `python test_gpu.py` to diagnose GPU problems
- Check CUDA installation and driver compatibility
- System will fallback to CPU if GPU fails

### **Debug Mode**
```bash
# Enable debug logging for all services
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## 📊 Monitoring

### **System Statistics**
```bash
# Get system stats
curl http://localhost:8004/stats

# Response includes:
# - Active sessions
# - Conversation statistics
# - Service health status
# - Configuration details
```

### **Logs**
Each service maintains detailed logs:
- `simple-rag/logs/` - RAG system logs
- `ASR_API/logs/` - ASR service logs
- `TTS_API/logs/` - TTS service logs
- `Orchestrator/logs/` - Orchestrator logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **NAMAA-Space** for the Arabic BERT model
- **Google Cloud** for Speech-to-Text and Text-to-Speech APIs
- **Gemini API** for text generation
- **FAISS** for vector search
- **FastAPI** for the web framework
- **PyTorch** for AI model framework

## 🎯 Quick Start Summary

```bash
# 1. Set up environments
conda activate rag && pip install -r simple-rag/requirements.txt
conda activate ASR && pip install -r ASR_API/requirements.txt
conda activate TTS-API && pip install -r TTS_API/requirements.txt
conda activate orchestrator && pip install -r Orchestrator/requirements.txt

# 2. Configure API keys
# - Place Google Cloud credentials in ASR_API/ and TTS_API/
# - Add Gemini API key to simple-rag/.env

# 3. Start services
conda activate rag && cd simple-rag && python main.py &
conda activate ASR && cd ASR_API && python run.py &
conda activate TTS-API && cd TTS_API && python run.py &
conda activate orchestrator && cd Orchestrator && python run.py &

# 4. Test the system
# Visit http://localhost:8004/test for WebSocket testing
# Visit http://localhost:8002/manage for RAG document management
```

**Ready to experience Arabic conversational AI with كيمو! 🇪🇬**
