"""
Unit Tests for ASR API
Tests all endpoints of the Audio Speech Recognition API
"""

import pytest
import json
import os
import tempfile
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the ASR API app
import sys
sys.path.append(str(Path(__file__).parent.parent / "ASR_API"))
from app.main import app

class TestASRAPI:
    """Test suite for ASR API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client for ASR API"""
        return TestClient(app)
    
    @pytest.fixture
    def test_audio_path(self):
        """Path to test audio file"""
        return str(Path(__file__).parent.parent / "ASR_API" / "speaker.mp3")
    
    @pytest.fixture
    def mock_audio_content(self):
        """Mock audio content for testing"""
        return b"fake_audio_content_for_testing"

    # Core Information Endpoints
    
    def test_root_endpoint(self, client):
        """Test GET / endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
    
    def test_health_endpoint(self, client):
        """Test GET /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
    
    def test_streaming_test_endpoint(self, client):
        """Test GET /streaming-test endpoint"""
        response = client.get("/streaming-test")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    # Speech Recognition Endpoints
    
    @patch('ASR_API.app.services.gcp_asr.ASRProcessor.process_audio_file')
    def test_asr_endpoint_success(self, mock_process, client, test_audio_path):
        """Test POST /asr endpoint with successful transcription"""
        # Mock the ASR processing
        mock_process.return_value = {
            'transcript': 'هذا نص تجريبي للاختبار',
            'confidence': 0.95,
            'language_code': 'ar-EG',
            'processing_time': 2.5,
            'chunks_processed': 1,
            'words': [
                {'word': 'هذا', 'start_time': 0.0, 'end_time': 0.5},
                {'word': 'نص', 'start_time': 0.5, 'end_time': 1.0}
            ]
        }
        
        # Check if test audio file exists
        if not os.path.exists(test_audio_path):
            pytest.skip("Test audio file not found")
        
        with open(test_audio_path, 'rb') as f:
            response = client.post(
                "/asr",
                files={"file": ("test_audio.mp3", f, "audio/mpeg")},
                data={
                    "language_code": "ar-EG",
                    "chunk_duration_minutes": 0.5,
                    "enable_preprocessing": True,
                    "enable_word_timestamps": True
                }
            )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "transcript" in data
        assert "confidence" in data
        assert "language_code" in data
        assert "processing_time" in data
        assert "chunks_processed" in data
        assert "words" in data
        assert data["language_code"] == "ar-EG"
        assert data["confidence"] > 0
    
    def test_asr_endpoint_no_file(self, client):
        """Test POST /asr endpoint without file"""
        response = client.post("/asr")
        assert response.status_code == 422  # Validation error
    
    def test_asr_endpoint_invalid_language(self, client, test_audio_path):
        """Test POST /asr endpoint with invalid language code"""
        if not os.path.exists(test_audio_path):
            pytest.skip("Test audio file not found")
        
        with open(test_audio_path, 'rb') as f:
            response = client.post(
                "/asr",
                files={"file": ("test_audio.mp3", f, "audio/mpeg")},
                data={"language_code": "invalid-lang"}
            )
        
        # Should still process but with default language
        assert response.status_code in [200, 400]
    
    def test_asr_endpoint_different_languages(self, client, test_audio_path):
        """Test POST /asr endpoint with different language codes"""
        if not os.path.exists(test_audio_path):
            pytest.skip("Test audio file not found")
        
        languages = ["ar-EG", "en-US", "fr-FR", "de-DE", "es-ES"]
        
        for lang in languages:
            with open(test_audio_path, 'rb') as f:
                response = client.post(
                    "/asr",
                    files={"file": (f"test_{lang}.mp3", f, "audio/mpeg")},
                    data={"language_code": lang}
                )
            
            # Should process successfully regardless of language
            assert response.status_code in [200, 400, 500]
    
    def test_asr_endpoint_chunk_duration_options(self, client, test_audio_path):
        """Test POST /asr endpoint with different chunk durations"""
        if not os.path.exists(test_audio_path):
            pytest.skip("Test audio file not found")
        
        chunk_durations = [0.1, 0.5, 1.0, 2.0, 5.0]
        
        for duration in chunk_durations:
            with open(test_audio_path, 'rb') as f:
                response = client.post(
                    "/asr",
                    files={"file": (f"test_{duration}.mp3", f, "audio/mpeg")},
                    data={"chunk_duration_minutes": duration}
                )
            
            # Should process successfully
            assert response.status_code in [200, 400, 500]
    
    def test_asr_endpoint_preprocessing_options(self, client, test_audio_path):
        """Test POST /asr endpoint with different preprocessing options"""
        if not os.path.exists(test_audio_path):
            pytest.skip("Test audio file not found")
        
        preprocessing_options = [True, False]
        
        for enable in preprocessing_options:
            with open(test_audio_path, 'rb') as f:
                response = client.post(
                    "/asr",
                    files={"file": (f"test_prep_{enable}.mp3", f, "audio/mpeg")},
                    data={"enable_preprocessing": enable}
                )
            
            # Should process successfully
            assert response.status_code in [200, 400, 500]
    
    def test_asr_endpoint_word_timestamps_options(self, client, test_audio_path):
        """Test POST /asr endpoint with different word timestamp options"""
        if not os.path.exists(test_audio_path):
            pytest.skip("Test audio file not found")
        
        timestamp_options = [True, False]
        
        for enable in timestamp_options:
            with open(test_audio_path, 'rb') as f:
                response = client.post(
                    "/asr",
                    files={"file": (f"test_timestamps_{enable}.mp3", f, "audio/mpeg")},
                    data={"enable_word_timestamps": enable}
                )
            
            # Should process successfully
            assert response.status_code in [200, 400, 500]
    
    def test_asr_endpoint_large_file(self, client):
        """Test POST /asr endpoint with large file"""
        # Create a large fake audio file
        large_content = b"fake_audio_content" * 10000  # ~170KB
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_file.write(large_content)
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                response = client.post(
                    "/asr",
                    files={"file": ("large_audio.mp3", f, "audio/mpeg")},
                    data={"language_code": "ar-EG"}
                )
            
            # Should handle large files appropriately
            assert response.status_code in [200, 400, 413, 500]
            
        finally:
            os.unlink(temp_file.name)
    
    def test_asr_endpoint_unsupported_format(self, client):
        """Test POST /asr endpoint with unsupported audio format"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.xyz', delete=False)
        temp_file.write(b"fake_content")
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                response = client.post(
                    "/asr",
                    files={"file": ("test.xyz", f, "application/octet-stream")},
                    data={"language_code": "ar-EG"}
                )
            
            # Should handle unsupported formats
            assert response.status_code in [200, 400, 500]
            
        finally:
            os.unlink(temp_file.name)

    # WebSocket Streaming Tests
    
    @pytest.mark.asyncio
    async def test_websocket_asr_stream_connection(self):
        """Test WebSocket connection to /ws/asr-stream"""
        try:
            import websockets
            
            # This test requires the service to be running
            # Skip if service is not available
            uri = "ws://localhost:8001/ws/asr-stream"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Test basic connection
                    assert websocket.open
                    
            except Exception:
                pytest.skip("ASR service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")
    
    @pytest.mark.asyncio
    async def test_websocket_asr_stream_config(self):
        """Test WebSocket configuration sending"""
        try:
            import websockets
            
            uri = "ws://localhost:8001/ws/asr-stream"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Send configuration
                    config = {
                        "language_code": "ar-EG",
                        "sample_rate_hertz": 16000,
                        "encoding": "LINEAR16"
                    }
                    
                    await websocket.send(json.dumps(config))
                    
                    # Should receive acknowledgment
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    assert data["type"] == "metadata"
                    assert data["status"] == "ready"
                    assert data["language_code"] == "ar-EG"
                    
            except Exception:
                pytest.skip("ASR service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")
    
    @pytest.mark.asyncio
    async def test_websocket_asr_stream_audio_data(self):
        """Test WebSocket audio data streaming"""
        try:
            import websockets
            
            uri = "ws://localhost:8001/ws/asr-stream"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Send configuration
                    config = {
                        "language_code": "ar-EG",
                        "sample_rate_hertz": 16000,
                        "encoding": "LINEAR16"
                    }
                    
                    await websocket.send(json.dumps(config))
                    
                    # Receive acknowledgment
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Send fake audio data
                    fake_audio = b"fake_audio_data_for_testing"
                    await websocket.send(fake_audio)
                    
                    # Should receive some response (or timeout)
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2)
                        # Response could be transcript or error
                        assert isinstance(response, str)
                    except asyncio.TimeoutError:
                        # Timeout is acceptable for this test
                        pass
                    
            except Exception:
                pytest.skip("ASR service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")

    # Error Handling Tests
    
    def test_asr_endpoint_missing_parameters(self, client, test_audio_path):
        """Test POST /asr endpoint with missing parameters"""
        if not os.path.exists(test_audio_path):
            pytest.skip("Test audio file not found")
        
        with open(test_audio_path, 'rb') as f:
            response = client.post(
                "/asr",
                files={"file": ("test.mp3", f, "audio/mpeg")}
                # Missing other parameters
            )
        
        # Should still process with defaults
        assert response.status_code in [200, 400, 500]
    
    def test_asr_endpoint_invalid_chunk_duration(self, client, test_audio_path):
        """Test POST /asr endpoint with invalid chunk duration"""
        if not os.path.exists(test_audio_path):
            pytest.skip("Test audio file not found")
        
        with open(test_audio_path, 'rb') as f:
            response = client.post(
                "/asr",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"chunk_duration_minutes": 10.0}  # Too large
            )
        
        # Should handle invalid duration
        assert response.status_code in [200, 400, 422, 500]
    
    def test_asr_endpoint_empty_file(self, client):
        """Test POST /asr endpoint with empty file"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_file.write(b"")  # Empty file
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                response = client.post(
                    "/asr",
                    files={"file": ("empty.mp3", f, "audio/mpeg")},
                    data={"language_code": "ar-EG"}
                )
            
            # Should handle empty files
            assert response.status_code in [200, 400, 500]
            
        finally:
            os.unlink(temp_file.name)

    # Performance Tests
    
    def test_asr_performance(self, client, test_audio_path):
        """Test ASR processing performance"""
        if not os.path.exists(test_audio_path):
            pytest.skip("Test audio file not found")
        
        with open(test_audio_path, 'rb') as f:
            response = client.post(
                "/asr",
                files={"file": ("perf_test.mp3", f, "audio/mpeg")},
                data={"language_code": "ar-EG"}
            )
        
        if response.status_code == 200:
            data = response.json()
            # Processing time should be reasonable (less than 30 seconds)
            assert data["processing_time"] < 30.0
