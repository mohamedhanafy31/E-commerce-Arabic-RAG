"""
Test Configuration and Utilities
Shared testing utilities and configuration for all services
"""

import os
import sys
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import pytest
import httpx
import websockets
from fastapi.testclient import TestClient

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Test Configuration
TEST_CONFIG = {
    "base_urls": {
        "rag_system": "http://localhost:8002",
        "asr_api": "http://localhost:8001", 
        "tts_api": "http://localhost:8003",
        "orchestrator": "http://localhost:8004"
    },
    "websocket_urls": {
        "asr_stream": "ws://localhost:8001/ws/asr-stream",
        "tts_stream": "ws://localhost:8003/ws/tts-stream",
        "conversation": "ws://localhost:8004/ws/conversation"
    },
    "test_files": {
        "document": PROJECT_ROOT / "large.txt",
        "audio": PROJECT_ROOT / "ASR_API" / "speaker.mp3"
    },
    "test_data": {
        "arabic_text": "الدليل ده معمول علشان يوضحلك بالضبط إيه المطلوب في إثبات المهام )Tasks )الخاصة بمسار الكوتشنج ضمن مبادرة رّواد مصر الرقمية، علشان نضمن إن كل شغل بتقدمه بيعكس مهارات حقيقية وتقدر الوزارة تتحقق منه بسهولة. ليه الزم تقرأه كويس؟",
        "arabic_query": "ما هو موضوع هذا المستند؟",
        "english_query": "What is the main topic of this document?"
    }
}

class TestUtilities:
    """Utility class for common testing operations"""
    
    @staticmethod
    def create_test_client(app):
        """Create a FastAPI test client"""
        return TestClient(app)
    
    @staticmethod
    def create_temp_file(content: str, suffix: str = ".txt") -> str:
        """Create a temporary file with content"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name
    
    @staticmethod
    def cleanup_temp_file(file_path: str):
        """Clean up temporary file"""
        try:
            os.unlink(file_path)
        except FileNotFoundError:
            pass
    
    @staticmethod
    def get_test_document_path() -> str:
        """Get path to test document"""
        return str(TEST_CONFIG["test_files"]["document"])
    
    @staticmethod
    def get_test_audio_path() -> str:
        """Get path to test audio file"""
        return str(TEST_CONFIG["test_files"]["audio"])
    
    @staticmethod
    def create_multipart_data(file_path: str, **fields) -> Dict[str, Any]:
        """Create multipart form data for file uploads"""
        with open(file_path, 'rb') as f:
            files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
            return {"files": files, "data": fields}

class WebSocketTestClient:
    """WebSocket testing utilities"""
    
    def __init__(self, url: str):
        self.url = url
        self.websocket = None
    
    async def connect(self):
        """Connect to WebSocket"""
        self.websocket = await websockets.connect(self.url)
        return self.websocket
    
    async def send_json(self, data: Dict[str, Any]):
        """Send JSON data"""
        await self.websocket.send(json.dumps(data))
    
    async def send_bytes(self, data: bytes):
        """Send binary data"""
        await self.websocket.send(data)
    
    async def receive_json(self) -> Dict[str, Any]:
        """Receive JSON data"""
        message = await self.websocket.recv()
        return json.loads(message)
    
    async def receive_bytes(self) -> bytes:
        """Receive binary data"""
        return await self.websocket.recv()
    
    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()

class ServiceHealthChecker:
    """Check if services are running"""
    
    @staticmethod
    async def check_service_health(url: str) -> bool:
        """Check if a service is running"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health", timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False
    
    @staticmethod
    async def check_all_services() -> Dict[str, bool]:
        """Check health of all services"""
        services = {}
        for service, url in TEST_CONFIG["base_urls"].items():
            services[service] = await ServiceHealthChecker.check_service_health(url)
        return services

# Pytest fixtures
@pytest.fixture
def test_config():
    """Provide test configuration"""
    return TEST_CONFIG

@pytest.fixture
def test_utils():
    """Provide test utilities"""
    return TestUtilities

@pytest.fixture
def test_document_path():
    """Provide test document path"""
    return TestUtilities.get_test_document_path()

@pytest.fixture
def test_audio_path():
    """Provide test audio path"""
    return TestUtilities.get_test_audio_path()

@pytest.fixture
def arabic_text():
    """Provide Arabic test text"""
    return TEST_CONFIG["test_data"]["arabic_text"]

@pytest.fixture
def arabic_query():
    """Provide Arabic test query"""
    return TEST_CONFIG["test_data"]["arabic_query"]

@pytest.fixture
def english_query():
    """Provide English test query"""
    return TEST_CONFIG["test_data"]["english_query"]

# Skip tests if services are not running
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "service_required: mark test as requiring specific service"
    )
    config.addinivalue_line(
        "markers", "websocket: mark test as WebSocket test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
