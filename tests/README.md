# 🧪 Unit Testing Suite for E-commerce Arabic RAG System

Comprehensive testing suite for all microservices including HTTP endpoints, WebSocket connections, and integration tests.

## 📋 Overview

This testing suite provides complete coverage for all endpoints of the Arabic RAG System:

- **RAG System** (Port 8002): Document management, query processing, Arabic text generation
- **ASR API** (Port 8001): Speech recognition, WebSocket streaming
- **TTS API** (Port 8003): Text-to-speech, voice synthesis
- **Orchestrator** (Port 8004): Complete conversational flow coordination

## 🚀 Quick Start

### 1. Install Test Dependencies

```bash
# Install testing dependencies
pip install -r tests/requirements.txt

# Or use the test runner
python tests/run_tests.py --install-deps
```

### 2. Start Services (Required for Integration Tests)

```bash
# Option 1: Docker Compose
docker compose up -d

# Option 2: Individual services
conda activate rag && cd simple-rag && python main.py &
conda activate ASR && cd ASR_API && python run.py &
conda activate TTS-API && cd TTS_API && python run.py &
conda activate orchestrator && cd Orchestrator && python run.py &

# Option 3: Use deploy script
./deploy.sh local
```

### 3. Run Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific service tests
python tests/run_tests.py --service rag
python tests/run_tests.py --service asr
python tests/run_tests.py --service tts
python tests/run_tests.py --service orchestrator

# Run WebSocket tests only
python tests/run_tests.py --websocket

# Run integration tests only
python tests/run_tests.py --integration

# Verbose output
python tests/run_tests.py --verbose
```

## 📁 Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── run_tests.py                # Main test runner script
├── websocket_utils.py          # WebSocket testing utilities
├── test_rag_system.py          # RAG System endpoint tests
├── test_asr_api.py             # ASR API endpoint tests
├── test_tts_api.py             # TTS API endpoint tests
├── test_orchestrator.py        # Orchestrator endpoint tests
└── requirements.txt            # Testing dependencies
```

## 🧪 Test Categories

### 1. **Unit Tests** (No Service Required)
- Basic endpoint functionality
- Request/response validation
- Error handling
- Input validation

### 2. **Integration Tests** (Services Required)
- End-to-end workflows
- Service communication
- Data flow validation
- Performance testing

### 3. **WebSocket Tests** (Services Required)
- Real-time communication
- Message protocol validation
- Connection handling
- Streaming functionality

## 📊 Test Coverage

### RAG System Tests (`test_rag_system.py`)

| Endpoint | Method | Test Coverage |
|----------|--------|---------------|
| `/` | GET | ✅ System info, endpoints list |
| `/health` | GET | ✅ Component health status |
| `/stats` | GET | ✅ System statistics |
| `/upload` | POST | ✅ Document upload, file validation |
| `/query` | POST | ✅ Arabic/English queries, كيمو responses |
| `/documents` | GET | ✅ Document listing |
| `/documents` | PUT | ✅ Document update by filename |
| `/documents/{file_id}` | PUT | ✅ Document update by ID |
| `/documents/{file_id}` | DELETE | ✅ Document deletion by ID |
| `/documents` | DELETE | ✅ Document deletion by filename |
| `/reset` | POST | ✅ Store reset functionality |
| `/manage` | GET | ✅ Management UI |
| `/static/*` | GET | ✅ Static files |

**Test Data Used:**
- Document: `large.txt` (Company profile in Arabic)
- Arabic queries: "ما هو موضوع هذا المستند؟"
- English queries: "What is the main topic of this document?"
- General conversation: "عامل إيه؟", "صباح الخير"

### ASR API Tests (`test_asr_api.py`)

| Endpoint | Method | Test Coverage |
|----------|--------|---------------|
| `/` | GET | ✅ Web UI interface |
| `/health` | GET | ✅ Health check |
| `/asr` | POST | ✅ Audio file transcription |
| `/ws/asr-stream` | WS | ✅ Real-time streaming |
| `/streaming-test` | GET | ✅ Streaming test page |

**Test Data Used:**
- Audio file: `ASR_API/speaker.mp3`
- Languages: ar-EG, en-US, fr-FR, de-DE, es-ES
- Chunk durations: 0.1, 0.5, 1.0, 2.0, 5.0 minutes
- Preprocessing options: True/False
- Word timestamps: True/False

### TTS API Tests (`test_tts_api.py`)

| Endpoint | Method | Test Coverage |
|----------|--------|---------------|
| `/` | GET | ✅ Web UI interface |
| `/health` | GET | ✅ Health check |
| `/voices` | GET | ✅ Voice listing, filtering |
| `/tts` | POST | ✅ Text-to-speech synthesis |
| `/ws/tts-stream` | WS | ✅ Streaming TTS |
| `/audio/*` | GET | ✅ Generated audio files |

**Test Data Used:**
- Arabic text: "الدليل ده معمول علشان يوضحلك بالضبط إيه المطلوب في إثبات المهام..."
- English text: "This is a test text for text-to-speech conversion."
- Audio encodings: MP3, OGG_OPUS, LINEAR16
- Voices: ar-XA-Chirp3-HD-* variants
- Speaking rates: 0.5, 1.0, 1.5, 2.0
- Pitch values: -10.0, 0.0, 10.0

### Orchestrator Tests (`test_orchestrator.py`)

| Endpoint | Method | Test Coverage |
|----------|--------|---------------|
| `/` | GET | ✅ System info, configuration |
| `/health` | GET | ✅ Health check, session info |
| `/stats` | GET | ✅ Statistics, configuration |
| `/ws/conversation` | WS | ✅ Complete conversational flow |
| `/test` | GET | ✅ WebSocket test client |
| `/static/*` | GET | ✅ Static files |
| `/docs` | GET | ✅ Swagger UI |
| `/redoc` | GET | ✅ ReDoc documentation |

**WebSocket Protocol Tests:**
- Connection establishment
- Ready message reception
- State message handling
- Audio chunk processing
- Audio end signaling
- Complete conversation flow
- Error handling

## 🔌 WebSocket Testing

### Specialized Test Classes

1. **ASRStreamTester**: Tests ASR WebSocket streaming
   - Configuration sending
   - Audio data streaming
   - Transcript reception

2. **TTSStreamTester**: Tests TTS WebSocket streaming
   - Request sending
   - Metadata reception
   - Audio chunk collection
   - Completion handling

3. **ConversationTester**: Tests Orchestrator conversation flow
   - Ready message handling
   - State management
   - Complete conversation workflow
   - Response collection

### WebSocket Test Example

```python
async def test_asr_streaming():
    tester = ASRStreamTester()
    results = await tester.test_basic_flow()
    
    assert results["connection"] == True
    assert results["config_sent"] == True
    assert results["config_ack"] == True
    assert results["audio_sent"] == True
```

## 🛠️ Test Configuration

### Pytest Configuration (`pytest.ini`)

- **Async Support**: Automatic async test detection
- **Markers**: service_required, websocket, integration, slow
- **Timeout**: 300 seconds per test
- **Warnings**: Filtered deprecation warnings

### Test Fixtures (`conftest.py`)

- **test_config**: Test configuration data
- **test_utils**: Utility functions
- **test_document_path**: Path to test document
- **test_audio_path**: Path to test audio file
- **arabic_text**: Arabic test text
- **arabic_query**: Arabic test query
- **english_query**: English test query

## 📈 Running Tests

### Individual Test Execution

```bash
# Run specific test file
pytest tests/test_rag_system.py -v

# Run specific test method
pytest tests/test_rag_system.py::TestRAGSystem::test_upload_document -v

# Run tests with specific marker
pytest -m "websocket" -v

# Run tests excluding slow tests
pytest -m "not slow" -v
```

### Parallel Test Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto tests/
```

### Coverage Analysis

```bash
# Install pytest-cov
pip install pytest-cov

# Run with coverage
pytest --cov=. --cov-report=html tests/
```

## 🚨 Error Handling Tests

### Common Error Scenarios

1. **File Upload Errors**
   - Unsupported file types
   - Empty files
   - Large files
   - Corrupted files

2. **API Errors**
   - Invalid parameters
   - Missing required fields
   - Malformed requests
   - Service unavailable

3. **WebSocket Errors**
   - Connection failures
   - Invalid message formats
   - Malformed JSON
   - Timeout handling

## 📊 Performance Testing

### Response Time Validation

- **RAG Queries**: < 10 seconds
- **Document Upload**: < 30 seconds
- **ASR Processing**: < 30 seconds
- **TTS Synthesis**: < 15 seconds
- **WebSocket Responses**: < 10 seconds

### Load Testing

```python
# Example performance test
def test_query_performance(client):
    start_time = time.time()
    response = client.post("/query", json={"query": "test"})
    duration = time.time() - start_time
    
    assert response.status_code == 200
    assert duration < 10.0  # Less than 10 seconds
```

## 🔧 Troubleshooting

### Common Issues

1. **Service Not Running**
   ```bash
   # Check service health
   curl http://localhost:8002/health
   curl http://localhost:8001/health
   curl http://localhost:8003/health
   curl http://localhost:8004/health
   ```

2. **WebSocket Connection Failed**
   - Ensure services are running
   - Check firewall settings
   - Verify WebSocket support

3. **Test Dependencies Missing**
   ```bash
   pip install -r tests/requirements.txt
   ```

4. **Permission Issues**
   ```bash
   chmod +x tests/run_tests.py
   ```

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run tests with debug output
pytest -v -s tests/
```

## 📄 Test Reports

### HTML Report

```bash
pytest --html=report.html --self-contained-html tests/
```

### JSON Report

```bash
pytest --json-report --json-report-file=report.json tests/
```

### Coverage Report

```bash
pytest --cov=. --cov-report=html --cov-report=term tests/
```

## 🤝 Contributing

### Adding New Tests

1. **Follow naming conventions**
   - Test files: `test_*.py`
   - Test classes: `Test*`
   - Test methods: `test_*`

2. **Use appropriate markers**
   ```python
   @pytest.mark.websocket
   @pytest.mark.integration
   @pytest.mark.slow
   ```

3. **Add proper docstrings**
   ```python
   def test_upload_document(self, client):
       """Test POST /upload endpoint with valid document"""
   ```

4. **Use fixtures for common data**
   ```python
   def test_query(self, client, arabic_query):
       """Test query with Arabic text"""
   ```

### Test Data Management

- Use `large.txt` for document tests
- Use `speaker.mp3` for audio tests
- Create temporary files for specific test cases
- Clean up resources in `finally` blocks

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [WebSocket Testing](https://websockets.readthedocs.io/)
- [Async Testing](https://pytest-asyncio.readthedocs.io/)

---

**Ready to test your Arabic conversational AI system! 🇪🇬🤖**
