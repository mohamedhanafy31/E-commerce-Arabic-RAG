# ASR API - Speech Recognition Service

A FastAPI-based speech recognition service with real-time WebSocket streaming support using Google Cloud Speech-to-Text API.

## 🚀 Features

- **File Upload ASR**: Upload audio files for transcription
- **Real-time Streaming**: WebSocket-based live audio transcription
- **Multi-language Support**: Arabic, English, French, German, Spanish
- **Google Cloud Integration**: Powered by Google Cloud Speech-to-Text
- **Web Interface**: Built-in testing interface
- **Unity Integration**: Complete Unity client implementation

## 📁 Project Structure

```
ASR_API/
├── app/                    # Main application code
│   ├── api/               # API routes
│   ├── core/              # Configuration and logging
│   ├── middleware/        # Error handling
│   ├── models/           # Pydantic schemas
│   └── services/         # ASR services
├── docs/                  # Documentation
│   ├── unity/            # Unity integration guides
│   └── STREAMING_IMPLEMENTATION.md
├── pages/                 # Web interface
├── data/                  # Audio data directory
├── requirements.txt       # Python dependencies
├── run.py                # Application entry point
└── speaker_arabic.wav    # Sample audio file
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ASR_API
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Google Cloud credentials**
   - Place your `tts-key.json` file in the root directory
   - Ensure the service account has Speech-to-Text API access

4. **Run the server**
   ```bash
   python run.py
   ```

## 🌐 API Endpoints

### File Upload ASR
- **POST** `/asr` - Upload audio file for transcription
- **GET** `/health` - Health check endpoint

### WebSocket Streaming
- **WS** `/ws/asr-stream` - Real-time audio streaming transcription

### Web Interface
- **GET** `/` - Main test page
- **GET** `/streaming-test` - WebSocket streaming test interface

## 🎤 Usage Examples

### File Upload
```bash
curl -X POST "http://localhost:8001/asr" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav" \
  -F "language_code=ar-EG"
```

### WebSocket Streaming
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/asr-stream');

// Send configuration
ws.send(JSON.stringify({
  language_code: "ar-EG",
  sample_rate_hertz: 16000,
  encoding: "LINEAR16"
}));

// Send audio data
ws.send(audioData);
```

## 🎮 Unity Integration

Complete Unity integration is available in the `docs/unity/` directory:

- **UnityASRClient.cs** - Ready-to-use Unity WebSocket client
- **ASRUI.cs** - Unity UI controller
- **UNITY_INTEGRATION_GUIDE.md** - Complete technical guide
- **UNITY_QUICK_SETUP.md** - 5-minute setup guide

## 🔧 Configuration

### Environment Variables
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to Google Cloud credentials
- `DEFAULT_LANGUAGE_CODE` - Default language (default: ar-EG)
- `DEFAULT_SAMPLE_RATE_HERTZ` - Default sample rate (default: 16000)
- `STREAMING_INTERIM_RESULTS` - Enable interim results (default: true)
- `ENABLE_AUTOMATIC_PUNCTUATION` - Enable punctuation (default: true)

### Supported Languages
- Arabic (Egypt): `ar-EG`
- English (US): `en-US`
- English (UK): `en-GB`
- French: `fr-FR`
- German: `de-DE`
- Spanish: `es-ES`

## 🧪 Testing

### Web Interface
1. Navigate to `http://localhost:8001/streaming-test`
2. Click "Connect" to establish WebSocket connection
3. Click "Start Recording" to begin audio capture
4. Speak into your microphone
5. Watch real-time transcriptions appear

### API Testing
```bash
# Health check
curl http://localhost:8001/health

# File upload test
curl -X POST "http://localhost:8001/asr" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@speaker_arabic.wav" \
  -F "language_code=ar-EG"
```

## 📚 Documentation

- [Streaming Implementation](docs/STREAMING_IMPLEMENTATION.md)
- [Unity Integration Guide](docs/unity/UNITY_INTEGRATION_GUIDE.md)
- [Unity Quick Setup](docs/unity/UNITY_QUICK_SETUP.md)
- [Unity Scene Setup](docs/unity/UNITY_SCENE_SETUP.md)

## 🐛 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Ensure ASR server is running on port 8001
   - Check firewall settings
   - Verify WebSocket URL

2. **Google Cloud Authentication Error**
   - Verify `tts-key.json` file exists
   - Check service account permissions
   - Ensure Speech-to-Text API is enabled

3. **Audio Quality Issues**
   - Use 16kHz sample rate for optimal performance
   - Ensure mono audio (single channel)
   - Check microphone permissions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Cloud Speech-to-Text API
- FastAPI framework
- WebSocket implementation
- Unity community
