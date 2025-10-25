"""
WebSocket Testing Utilities
Specialized utilities for testing WebSocket endpoints
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
import pytest

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

class WebSocketTestRunner:
    """Advanced WebSocket testing utility"""
    
    def __init__(self, url: str, timeout: float = 10.0):
        self.url = url
        self.timeout = timeout
        self.websocket = None
        self.messages_received = []
        self.binary_data_received = []
    
    async def connect(self) -> bool:
        """Connect to WebSocket"""
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets library not available")
        
        try:
            self.websocket = await websockets.connect(self.url, timeout=self.timeout)
            return True
        except Exception as e:
            print(f"Failed to connect to {self.url}: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
    
    async def send_json(self, data: Dict[str, Any]) -> bool:
        """Send JSON data"""
        try:
            await self.websocket.send(json.dumps(data))
            return True
        except Exception as e:
            print(f"Failed to send JSON: {e}")
            return False
    
    async def send_bytes(self, data: bytes) -> bool:
        """Send binary data"""
        try:
            await self.websocket.send(data)
            return True
        except Exception as e:
            print(f"Failed to send bytes: {e}")
            return False
    
    async def receive_message(self, timeout: Optional[float] = None) -> Optional[Any]:
        """Receive a message (JSON or binary)"""
        try:
            timeout = timeout or self.timeout
            message = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            
            # Try to parse as JSON
            try:
                json_data = json.loads(message)
                self.messages_received.append(json_data)
                return json_data
            except json.JSONDecodeError:
                # Binary data
                self.binary_data_received.append(message)
                return message
                
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            print(f"Failed to receive message: {e}")
            return None
    
    async def receive_json(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Receive JSON message specifically"""
        message = await self.receive_message(timeout)
        if isinstance(message, dict):
            return message
        return None
    
    async def receive_binary(self, timeout: Optional[float] = None) -> Optional[bytes]:
        """Receive binary message specifically"""
        message = await self.receive_message(timeout)
        if isinstance(message, bytes):
            return message
        return None
    
    async def wait_for_message_type(self, message_type: str, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Wait for a specific message type"""
        timeout = timeout or self.timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            message = await self.receive_message(1.0)
            if isinstance(message, dict) and message.get("type") == message_type:
                return message
        
        return None
    
    async def collect_messages(self, duration: float, message_filter: Optional[Callable] = None) -> List[Any]:
        """Collect messages for a specified duration"""
        messages = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            message = await self.receive_message(0.5)
            if message is not None:
                if message_filter is None or message_filter(message):
                    messages.append(message)
        
        return messages
    
    def get_messages_by_type(self, message_type: str) -> List[Dict[str, Any]]:
        """Get all received messages of a specific type"""
        return [msg for msg in self.messages_received if msg.get("type") == message_type]
    
    def get_binary_messages(self) -> List[bytes]:
        """Get all received binary messages"""
        return self.binary_data_received.copy()
    
    def clear_messages(self):
        """Clear received messages"""
        self.messages_received.clear()
        self.binary_data_received.clear()

class ASRStreamTester(WebSocketTestRunner):
    """Specialized tester for ASR WebSocket streaming"""
    
    def __init__(self, url: str = "ws://localhost:8001/ws/asr-stream"):
        super().__init__(url)
    
    async def test_basic_flow(self) -> Dict[str, Any]:
        """Test basic ASR streaming flow"""
        results = {
            "connection": False,
            "config_sent": False,
            "config_ack": False,
            "audio_sent": False,
            "transcript_received": False,
            "errors": []
        }
        
        try:
            # Connect
            results["connection"] = await self.connect()
            if not results["connection"]:
                return results
            
            # Send configuration
            config = {
                "language_code": "ar-EG",
                "sample_rate_hertz": 16000,
                "encoding": "LINEAR16"
            }
            
            results["config_sent"] = await self.send_json(config)
            if not results["config_sent"]:
                return results
            
            # Wait for acknowledgment
            ack = await self.wait_for_message_type("metadata", 5.0)
            if ack and ack.get("status") == "ready":
                results["config_ack"] = True
            
            # Send audio data
            fake_audio = b"fake_audio_data_for_testing"
            results["audio_sent"] = await self.send_bytes(fake_audio)
            
            # Wait for transcript
            transcript = await self.wait_for_message_type("transcript", 10.0)
            if transcript:
                results["transcript_received"] = True
            
        except Exception as e:
            results["errors"].append(str(e))
        
        finally:
            await self.disconnect()
        
        return results

class TTSStreamTester(WebSocketTestRunner):
    """Specialized tester for TTS WebSocket streaming"""
    
    def __init__(self, url: str = "ws://localhost:8003/ws/tts-stream"):
        super().__init__(url)
    
    async def test_basic_flow(self, text: str = "هذا نص تجريبي للاختبار") -> Dict[str, Any]:
        """Test basic TTS streaming flow"""
        results = {
            "connection": False,
            "request_sent": False,
            "metadata_received": False,
            "audio_chunks_received": 0,
            "completion_received": False,
            "errors": []
        }
        
        try:
            # Connect
            results["connection"] = await self.connect()
            if not results["connection"]:
                return results
            
            # Send TTS request
            request = {
                "text": text,
                "language_code": "ar-XA",
                "voice_name": "ar-XA-Chirp3-HD-Achernar",
                "audio_encoding": "MP3"
            }
            
            results["request_sent"] = await self.send_json(request)
            if not results["request_sent"]:
                return results
            
            # Wait for metadata
            metadata = await self.wait_for_message_type("metadata", 5.0)
            if metadata:
                results["metadata_received"] = True
            
            # Collect audio chunks and completion
            messages = await self.collect_messages(15.0)
            
            for message in messages:
                if isinstance(message, dict):
                    if message.get("type") == "complete":
                        results["completion_received"] = True
                elif isinstance(message, bytes):
                    results["audio_chunks_received"] += 1
            
        except Exception as e:
            results["errors"].append(str(e))
        
        finally:
            await self.disconnect()
        
        return results

class ConversationTester(WebSocketTestRunner):
    """Specialized tester for Orchestrator conversation WebSocket"""
    
    def __init__(self, url: str = "ws://localhost:8004/ws/conversation"):
        super().__init__(url)
    
    async def test_basic_flow(self) -> Dict[str, Any]:
        """Test basic conversation flow"""
        results = {
            "connection": False,
            "ready_received": False,
            "state_received": False,
            "audio_sent": False,
            "audio_end_sent": False,
            "transcript_received": False,
            "rag_response_received": False,
            "tts_audio_received": False,
            "completion_received": False,
            "errors": []
        }
        
        try:
            # Connect
            results["connection"] = await self.connect()
            if not results["connection"]:
                return results
            
            # Wait for ready message
            ready = await self.wait_for_message_type("ready", 5.0)
            if ready:
                results["ready_received"] = True
            
            # Wait for state message
            state = await self.wait_for_message_type("state_update", 5.0)
            if state:
                results["state_received"] = True
            
            # Send audio chunks
            fake_audio = b"fake_audio_data_for_testing"
            results["audio_sent"] = await self.send_bytes(fake_audio)
            
            # Send audio end
            audio_end = {"type": "audio_end"}
            results["audio_end_sent"] = await self.send_json(audio_end)
            
            # Collect responses
            messages = await self.collect_messages(20.0)
            
            for message in messages:
                if isinstance(message, dict):
                    msg_type = message.get("type")
                    if msg_type == "transcript":
                        results["transcript_received"] = True
                    elif msg_type == "rag_response":
                        results["rag_response_received"] = True
                    elif msg_type == "complete":
                        results["completion_received"] = True
                elif isinstance(message, bytes):
                    results["tts_audio_received"] = True
            
        except Exception as e:
            results["errors"].append(str(e))
        
        finally:
            await self.disconnect()
        
        return results

# Pytest fixtures for WebSocket testing
@pytest.fixture
def websocket_available():
    """Check if websockets library is available"""
    return WEBSOCKETS_AVAILABLE

@pytest.fixture
def asr_stream_tester():
    """Provide ASR stream tester"""
    return ASRStreamTester()

@pytest.fixture
def tts_stream_tester():
    """Provide TTS stream tester"""
    return TTSStreamTester()

@pytest.fixture
def conversation_tester():
    """Provide conversation tester"""
    return ConversationTester()

# Utility functions for WebSocket testing
async def test_websocket_connection(url: str, timeout: float = 5.0) -> bool:
    """Test if WebSocket connection is available"""
    if not WEBSOCKETS_AVAILABLE:
        return False
    
    try:
        async with websockets.connect(url, timeout=timeout) as websocket:
            return websocket.open
    except Exception:
        return False

async def test_websocket_basic_flow(url: str, send_data: Any, expected_response_type: Optional[str] = None, timeout: float = 10.0) -> Dict[str, Any]:
    """Test basic WebSocket flow"""
    results = {
        "connection": False,
        "data_sent": False,
        "response_received": False,
        "expected_type_received": False,
        "error": None
    }
    
    if not WEBSOCKETS_AVAILABLE:
        results["error"] = "websockets library not available"
        return results
    
    try:
        async with websockets.connect(url, timeout=timeout) as websocket:
            results["connection"] = True
            
            # Send data
            if isinstance(send_data, dict):
                await websocket.send(json.dumps(send_data))
            else:
                await websocket.send(send_data)
            results["data_sent"] = True
            
            # Receive response
            response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            results["response_received"] = True
            
            # Check if expected type
            if expected_response_type and isinstance(response, str):
                try:
                    data = json.loads(response)
                    if data.get("type") == expected_response_type:
                        results["expected_type_received"] = True
                except json.JSONDecodeError:
                    pass
            
    except Exception as e:
        results["error"] = str(e)
    
    return results
