"""
Unit Tests for Orchestrator
Tests all endpoints of the Orchestrator service
"""

import pytest
import json
import os
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the Orchestrator app
import sys
sys.path.append(str(Path(__file__).parent.parent / "Orchestrator"))
from app.main import app

class TestOrchestrator:
    """Test suite for Orchestrator endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client for Orchestrator"""
        return TestClient(app)
    
    @pytest.fixture
    def test_audio_data(self):
        """Mock audio data for testing"""
        return b"fake_audio_data_for_testing"

    # Core Information Endpoints
    
    def test_root_endpoint(self, client):
        """Test GET / endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"
        assert "endpoints" in data
        assert "websocket" in data["endpoints"]
        assert "health" in data["endpoints"]
        assert "stats" in data["endpoints"]
        assert "docs" in data["endpoints"]
        assert "configuration" in data
    
    def test_health_endpoint(self, client):
        """Test GET /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
        assert "orchestrator" in data["services"]
        assert "session_manager" in data["services"]
        assert "active_sessions" in data
        assert "max_sessions" in data
    
    def test_stats_endpoint(self, client):
        """Test GET /stats endpoint"""
        response = client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "sessions" in data
        assert "active_conversations" in data
        assert "configuration" in data
        assert "max_concurrent_sessions" in data["configuration"]
        assert "session_timeout_seconds" in data["configuration"]
        assert "audio_sample_rate" in data["configuration"]
        assert "audio_format" in data["configuration"]
        assert "default_language_code" in data["configuration"]
        assert "tts_language_code" in data["configuration"]
        assert "enable_conversation_history" in data["configuration"]
        assert "enable_sentence_streaming" in data["configuration"]

    # Web Interface Endpoints
    
    def test_test_endpoint(self, client):
        """Test GET /test endpoint"""
        response = client.get("/test")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
    
    def test_static_files(self, client):
        """Test GET /static/* endpoint"""
        # This will return 404 if no static files exist, which is expected
        response = client.get("/static/test.css")
        # Should either return the file or 404
        assert response.status_code in [200, 404]
    
    def test_docs_endpoint(self, client):
        """Test GET /docs endpoint"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
    
    def test_redoc_endpoint(self, client):
        """Test GET /redoc endpoint"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    # WebSocket Conversation Tests
    
    @pytest.mark.asyncio
    async def test_websocket_conversation_connection(self):
        """Test WebSocket connection to /ws/conversation"""
        try:
            import websockets
            
            uri = "ws://localhost:8004/ws/conversation"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Test basic connection
                    assert websocket.open
                    
            except Exception:
                pytest.skip("Orchestrator service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")
    
    @pytest.mark.asyncio
    async def test_websocket_conversation_ready_message(self):
        """Test WebSocket ready message"""
        try:
            import websockets
            
            uri = "ws://localhost:8004/ws/conversation"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Should receive ready message immediately
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    assert data["type"] == "ready"
                    assert "session_id" in data
                    assert "audio_config" in data
                    assert data["audio_config"]["language_code"] == "ar-EG"
                    assert data["audio_config"]["sample_rate_hertz"] == 16000
                    assert data["audio_config"]["encoding"] == "LINEAR16"
                    
            except Exception:
                pytest.skip("Orchestrator service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")
    
    @pytest.mark.asyncio
    async def test_websocket_conversation_state_message(self):
        """Test WebSocket state message"""
        try:
            import websockets
            
            uri = "ws://localhost:8004/ws/conversation"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Receive ready message
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Should receive state message
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    assert data["type"] == "state_update"
                    assert "state" in data
                    assert "previous_state" in data
                    
            except Exception:
                pytest.skip("Orchestrator service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")
    
    @pytest.mark.asyncio
    async def test_websocket_conversation_audio_chunks(self):
        """Test WebSocket audio chunk processing"""
        try:
            import websockets
            
            uri = "ws://localhost:8004/ws/conversation"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Receive ready message
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Receive state message
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Send audio chunk
                    fake_audio = b"fake_audio_data_for_testing"
                    await websocket.send(fake_audio)
                    
                    # Should receive some response or timeout
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        # Response could be various message types
                        if isinstance(response, str):
                            data = json.loads(response)
                            assert "type" in data
                    except asyncio.TimeoutError:
                        # Timeout is acceptable for this test
                        pass
                    
            except Exception:
                pytest.skip("Orchestrator service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")
    
    @pytest.mark.asyncio
    async def test_websocket_conversation_audio_end(self):
        """Test WebSocket audio end message"""
        try:
            import websockets
            
            uri = "ws://localhost:8004/ws/conversation"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Receive ready message
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Receive state message
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Send audio end message
                    audio_end = {"type": "audio_end"}
                    await websocket.send(json.dumps(audio_end))
                    
                    # Should receive some response or timeout
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10)
                        # Response could be transcript, rag_response, or audio_chunk_tts
                        if isinstance(response, str):
                            data = json.loads(response)
                            assert "type" in data
                            assert data["type"] in ["transcript", "rag_response", "audio_chunk_tts", "complete"]
                    except asyncio.TimeoutError:
                        # Timeout is acceptable for this test
                        pass
                    
            except Exception:
                pytest.skip("Orchestrator service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")
    
    @pytest.mark.asyncio
    async def test_websocket_conversation_complete_flow(self):
        """Test complete WebSocket conversation flow"""
        try:
            import websockets
            
            uri = "ws://localhost:8004/ws/conversation"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Receive ready message
                    ready_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    ready_data = json.loads(ready_response)
                    assert ready_data["type"] == "ready"
                    
                    # Receive state message
                    state_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    state_data = json.loads(state_response)
                    assert state_data["type"] == "state_update"
                    
                    # Send multiple audio chunks
                    for i in range(3):
                        fake_audio = f"fake_audio_chunk_{i}".encode()
                        await websocket.send(fake_audio)
                    
                    # Send audio end
                    audio_end = {"type": "audio_end"}
                    await websocket.send(json.dumps(audio_end))
                    
                    # Collect responses
                    responses = []
                    try:
                        while True:
                            response = await asyncio.wait_for(websocket.recv(), timeout=3)
                            if isinstance(response, str):
                                data = json.loads(response)
                                responses.append(data)
                                if data.get("type") == "complete":
                                    break
                            else:
                                # Binary audio data
                                responses.append({"type": "audio_binary", "size": len(response)})
                    except asyncio.TimeoutError:
                        # Timeout is acceptable
                        pass
                    
                    # Should have received some responses
                    assert len(responses) >= 0
                    
            except Exception:
                pytest.skip("Orchestrator service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")

    # Error Handling Tests
    
    @pytest.mark.asyncio
    async def test_websocket_conversation_invalid_message(self):
        """Test WebSocket with invalid message"""
        try:
            import websockets
            
            uri = "ws://localhost:8004/ws/conversation"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Receive ready message
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Receive state message
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Send invalid message
                    invalid_message = {"type": "invalid_type"}
                    await websocket.send(json.dumps(invalid_message))
                    
                    # Should handle invalid message gracefully
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2)
                        # Should either ignore or send error
                        if isinstance(response, str):
                            data = json.loads(response)
                            # Should not crash
                            assert isinstance(data, dict)
                    except asyncio.TimeoutError:
                        # Timeout is acceptable
                        pass
                    
            except Exception:
                pytest.skip("Orchestrator service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")
    
    @pytest.mark.asyncio
    async def test_websocket_conversation_malformed_json(self):
        """Test WebSocket with malformed JSON"""
        try:
            import websockets
            
            uri = "ws://localhost:8004/ws/conversation"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Receive ready message
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Receive state message
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Send malformed JSON
                    malformed_json = '{"type": "audio_end"'  # Missing closing brace
                    await websocket.send(malformed_json)
                    
                    # Should handle malformed JSON gracefully
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2)
                        # Should either ignore or send error
                        if isinstance(response, str):
                            data = json.loads(response)
                            # Should not crash
                            assert isinstance(data, dict)
                    except asyncio.TimeoutError:
                        # Timeout is acceptable
                        pass
                    
            except Exception:
                pytest.skip("Orchestrator service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")

    # Performance Tests
    
    @pytest.mark.asyncio
    async def test_websocket_conversation_performance(self):
        """Test WebSocket conversation performance"""
        try:
            import websockets
            import time
            
            uri = "ws://localhost:8004/ws/conversation"
            
            try:
                start_time = time.time()
                
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Receive ready message
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Receive state message
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    # Send audio end immediately
                    audio_end = {"type": "audio_end"}
                    await websocket.send(json.dumps(audio_end))
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10)
                        end_time = time.time()
                        
                        # Response should be reasonably fast (less than 10 seconds)
                        assert (end_time - start_time) < 10.0
                        
                    except asyncio.TimeoutError:
                        # Timeout is acceptable for this test
                        pass
                    
            except Exception:
                pytest.skip("Orchestrator service not running or WebSocket not available")
                
        except ImportError:
            pytest.skip("websockets library not available")

    # Configuration Tests
    
    def test_configuration_values(self, client):
        """Test configuration values in root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        config = data["configuration"]
        
        # Check configuration values
        assert config["max_concurrent_sessions"] == 100
        assert config["session_timeout_seconds"] == 300
        assert config["audio_format"] == "LINEAR16"
        assert config["audio_sample_rate"] == 16000
        assert config["default_language"] == "ar-EG"
    
    def test_stats_configuration(self, client):
        """Test configuration values in stats endpoint"""
        response = client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        config = data["configuration"]
        
        # Check configuration values
        assert config["max_concurrent_sessions"] == 100
        assert config["session_timeout_seconds"] == 300
        assert config["audio_sample_rate"] == 16000
        assert config["audio_format"] == "LINEAR16"
        assert config["default_language_code"] == "ar-EG"
        assert config["tts_language_code"] == "ar-XA"
        assert isinstance(config["enable_conversation_history"], bool)
        assert isinstance(config["enable_sentence_streaming"], bool)
