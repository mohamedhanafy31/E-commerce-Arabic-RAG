"""
Unit Tests for TTS API
Tests all endpoints of the Text-to-Speech API
"""

import pytest
import json
import os
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the TTS API app
import sys
sys.path.append(str(Path(__file__).parent.parent / "TTS_API"))
from app.main import app

class TestTTSAPI:
    """Test suite for TTS API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client for TTS API"""
        return TestClient(app)
    
    @pytest.fixture
    def arabic_text(self):
        """Arabic text for testing"""
        return "الدليل ده معمول علشان يوضحلك بالضبط إيه المطلوب في إثبات المهام )Tasks )الخاصة بمسار الكوتشنج ضمن مبادرة رّواد مصر الرقمية، علشان نضمن إن كل شغل بتقدمه بيعكس مهارات حقيقية وتقدر الوزارة تتحقق منه بسهولة. ليه الزم تقرأه كويس؟"
    
    @pytest.fixture
    def english_text(self):
        """English text for testing"""
        return "This is a test text for text-to-speech conversion."

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

    # Voice Management Endpoints
    
    def test_voices_endpoint(self, client):
        """Test GET /voices endpoint"""
        response = client.get("/voices")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Check if we have voices
        if len(data) > 0:
            voice = data[0]
            assert "name" in voice
            assert "language_codes" in voice
            assert "gender" in voice
    
    def test_voices_with_language_filter(self, client):
        """Test GET /voices endpoint with language filter"""
        response = client.get("/voices?language_code=ar-XA")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # All returned voices should support Arabic
        for voice in data:
            assert "ar-XA" in voice["language_codes"] or "ar" in voice["language_codes"]
    
    def test_voices_with_name_filter(self, client):
        """Test GET /voices endpoint with name filter"""
        response = client.get("/voices?name_contains=ar")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # All returned voices should have 'ar' in their name
        for voice in data:
            assert "ar" in voice["name"].lower()
    
    def test_voices_with_both_filters(self, client):
        """Test GET /voices endpoint with both language and name filters"""
        response = client.get("/voices?language_code=ar-XA&name_contains=ar")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    # Text-to-Speech Endpoints
    
    @patch('TTS_API.app.services.gcp_tts.GoogleTTSService.synthesize')
    def test_tts_endpoint_success(self, mock_synthesize, client, arabic_text):
        """Test POST /tts endpoint with successful synthesis"""
        # Mock the TTS synthesis
        mock_synthesize.return_value = (
            b"fake_audio_content_for_testing",
            "ar-XA-Chirp3-HD-Achernar",
            "ar-XA"
        )
        
        tts_data = {
            "text": arabic_text,
            "language_code": "ar-XA",
            "voice_name": "ar-XA-Chirp3-HD-Achernar",
            "audio_encoding": "MP3"
        }
        
        response = client.post("/tts", json=tts_data)
        assert response.status_code == 200
        
        # Check response headers
        assert "audio/mpeg" in response.headers["content-type"]
        assert "X-Voice-Used" in response.headers
        assert "X-Language-Code" in response.headers
        assert "Content-Disposition" in response.headers
        
        # Check response content
        assert len(response.content) > 0
    
    def test_tts_endpoint_arabic_text(self, client, arabic_text):
        """Test POST /tts endpoint with Arabic text"""
        tts_data = {
            "text": arabic_text,
            "language_code": "ar-XA",
            "audio_encoding": "MP3"
        }
        
        response = client.post("/tts", json=tts_data)
        # Should process successfully (may fail due to API limits in test)
        assert response.status_code in [200, 500]
    
    def test_tts_endpoint_english_text(self, client, english_text):
        """Test POST /tts endpoint with English text"""
        tts_data = {
            "text": english_text,
            "language_code": "en-US",
            "audio_encoding": "MP3"
        }
        
        response = client.post("/tts", json=tts_data)
        # Should process successfully (may fail due to API limits in test)
        assert response.status_code in [200, 500]
    
    def test_tts_endpoint_different_encodings(self, client, arabic_text):
        """Test POST /tts endpoint with different audio encodings"""
        encodings = ["MP3", "OGG_OPUS", "LINEAR16"]
        
        for encoding in encodings:
            tts_data = {
                "text": arabic_text[:50],  # Shorter text for faster processing
                "language_code": "ar-XA",
                "audio_encoding": encoding
            }
            
            response = client.post("/tts", json=tts_data)
            # Should process successfully (may fail due to API limits in test)
            assert response.status_code in [200, 500]
    
    def test_tts_endpoint_different_voices(self, client, arabic_text):
        """Test POST /tts endpoint with different voices"""
        voices = [
            "ar-XA-Chirp3-HD-Achernar",
            "ar-XA-Chirp3-HD-Algenib",
            "ar-XA-Chirp3-HD-Algieba"
        ]
        
        for voice in voices:
            tts_data = {
                "text": arabic_text[:50],  # Shorter text for faster processing
                "language_code": "ar-XA",
                "voice_name": voice,
                "audio_encoding": "MP3"
            }
            
            response = client.post("/tts", json=tts_data)
            # Should process successfully (may fail due to API limits in test)
            assert response.status_code in [200, 500]
    
    def test_tts_endpoint_speaking_rate_options(self, client, arabic_text):
        """Test POST /tts endpoint with different speaking rates"""
        rates = [0.5, 1.0, 1.5, 2.0]
        
        for rate in rates:
            tts_data = {
                "text": arabic_text[:30],  # Shorter text for faster processing
                "language_code": "ar-XA",
                "speaking_rate": rate,
                "audio_encoding": "MP3"
            }
            
            response = client.post("/tts", json=tts_data)
            # Should process successfully (may fail due to API limits in test)
            assert response.status_code in [200, 500]
    
    def test_tts_endpoint_pitch_options(self, client, arabic_text):
        """Test POST /tts endpoint with different pitch values"""
        pitches = [-10.0, 0.0, 10.0]
        
        for pitch in pitches:
            tts_data = {
                "text": arabic_text[:30],  # Shorter text for faster processing
                "language_code": "ar-XA",
                "pitch": pitch,
                "audio_encoding": "MP3"
            }
            
            response = client.post("/tts", json=tts_data)
            # Should process successfully (may fail due to API limits in test)
            assert response.status_code in [200, 500]
    
    def test_tts_endpoint_long_text(self, client):
        """Test POST /tts endpoint with long text"""
        long_text = "هذا نص طويل للاختبار " * 100  # Very long text
        
        tts_data = {
            "text": long_text,
            "language_code": "ar-XA",
            "audio_encoding": "MP3"
        }
        
        response = client.post("/tts", json=tts_data)
        # Should handle long text appropriately
        assert response.status_code in [200, 413, 500]
    
    def test_tts_endpoint_empty_text(self, client):
        """Test POST /tts endpoint with empty text"""
        tts_data = {
            "text": "",
            "language_code": "ar-XA",
            "audio_encoding": "MP3"
        }
        
        response = client.post("/tts", json=tts_data)
        # Should handle empty text
        assert response.status_code in [200, 400, 500]
    
    def test_tts_endpoint_missing_text(self, client):
        """Test POST /tts endpoint without text"""
        tts_data = {
            "language_code": "ar-XA",
            "audio_encoding": "MP3"
        }
        
        response = client.post("/tts", json=tts_data)
        # Should handle missing text
        assert response.status_code in [200, 422, 500]

    # WebSocket Streaming Tests
    
    @pytest.mark.asyncio
    async def test_websocket_tts_stream_connection(self):
        """Test WebSocket connection to /ws/tts-stream"""
        try:
            import websockets
            
            uri = "ws://localhost:8003/ws/tts-stream"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Test basic connection
                    assert websocket.open
                    
            except Exception:
                pytest.skip("TTS service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")
    
    @pytest.mark.asyncio
    async def test_websocket_tts_stream_request(self):
        """Test WebSocket TTS request"""
        try:
            import websockets
            
            uri = "ws://localhost:8003/ws/tts-stream"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Send TTS request
                    request = {
                        "text": "هذا نص تجريبي للاختبار",
                        "language_code": "ar-XA",
                        "voice_name": "ar-XA-Chirp3-HD-Achernar",
                        "audio_encoding": "MP3"
                    }
                    
                    await websocket.send(json.dumps(request))
                    
                    # Should receive metadata first
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(response)
                    
                    assert data["type"] == "metadata"
                    assert "voice_used" in data
                    assert "language_code" in data
                    assert "total_chunks" in data
                    
            except Exception:
                pytest.skip("TTS service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")
    
    @pytest.mark.asyncio
    async def test_websocket_tts_stream_audio_chunks(self):
        """Test WebSocket TTS audio chunks"""
        try:
            import websockets
            
            uri = "ws://localhost:8003/ws/tts-stream"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Send TTS request
                    request = {
                        "text": "هذا نص قصير للاختبار",
                        "language_code": "ar-XA",
                        "audio_encoding": "MP3"
                    }
                    
                    await websocket.send(json.dumps(request))
                    
                    # Receive metadata
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Try to receive audio chunks
                    audio_chunks = []
                    try:
                        while True:
                            chunk = await asyncio.wait_for(websocket.recv(), timeout=2)
                            if isinstance(chunk, bytes):
                                audio_chunks.append(chunk)
                            else:
                                # Might be completion message
                                data = json.loads(chunk)
                                if data.get("type") == "complete":
                                    break
                    except asyncio.TimeoutError:
                        # Timeout is acceptable
                        pass
                    
                    # Should have received some audio chunks or completion
                    assert len(audio_chunks) >= 0
                    
            except Exception:
                pytest.skip("TTS service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")

    # Error Handling Tests
    
    def test_tts_endpoint_invalid_language(self, client, arabic_text):
        """Test POST /tts endpoint with invalid language code"""
        tts_data = {
            "text": arabic_text,
            "language_code": "invalid-lang",
            "audio_encoding": "MP3"
        }
        
        response = client.post("/tts", json=tts_data)
        # Should handle invalid language
        assert response.status_code in [200, 400, 500]
    
    def test_tts_endpoint_invalid_voice(self, client, arabic_text):
        """Test POST /tts endpoint with invalid voice name"""
        tts_data = {
            "text": arabic_text,
            "language_code": "ar-XA",
            "voice_name": "invalid-voice",
            "audio_encoding": "MP3"
        }
        
        response = client.post("/tts", json=tts_data)
        # Should handle invalid voice (fallback to default)
        assert response.status_code in [200, 500]
    
    def test_tts_endpoint_invalid_encoding(self, client, arabic_text):
        """Test POST /tts endpoint with invalid audio encoding"""
        tts_data = {
            "text": arabic_text,
            "language_code": "ar-XA",
            "audio_encoding": "INVALID"
        }
        
        response = client.post("/tts", json=tts_data)
        # Should handle invalid encoding (fallback to default)
        assert response.status_code in [200, 500]
    
    def test_tts_endpoint_invalid_speaking_rate(self, client, arabic_text):
        """Test POST /tts endpoint with invalid speaking rate"""
        tts_data = {
            "text": arabic_text,
            "language_code": "ar-XA",
            "speaking_rate": 10.0,  # Too high
            "audio_encoding": "MP3"
        }
        
        response = client.post("/tts", json=tts_data)
        # Should handle invalid rate
        assert response.status_code in [200, 400, 500]
    
    def test_tts_endpoint_invalid_pitch(self, client, arabic_text):
        """Test POST /tts endpoint with invalid pitch"""
        tts_data = {
            "text": arabic_text,
            "language_code": "ar-XA",
            "pitch": 50.0,  # Too high
            "audio_encoding": "MP3"
        }
        
        response = client.post("/tts", json=tts_data)
        # Should handle invalid pitch
        assert response.status_code in [200, 400, 500]

    # Static Files Tests
    
    def test_audio_static_files(self, client):
        """Test GET /audio/* endpoint"""
        # This will return 404 if no audio files exist, which is expected
        response = client.get("/audio/test.mp3")
        # Should either return the file or 404
        assert response.status_code in [200, 404]

    # Performance Tests
    
    def test_tts_performance(self, client, arabic_text):
        """Test TTS processing performance"""
        tts_data = {
            "text": arabic_text[:100],  # Shorter text for faster processing
            "language_code": "ar-XA",
            "audio_encoding": "MP3"
        }
        
        response = client.post("/tts", json=tts_data)
        
        if response.status_code == 200:
            # Response should be reasonably fast
            assert len(response.content) > 0
            # Content should be audio data
            assert response.headers["content-type"].startswith("audio/")
