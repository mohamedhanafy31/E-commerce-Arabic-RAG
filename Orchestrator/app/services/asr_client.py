"""
ASR Client for Orchestrator
Handles WebSocket communication with ASR API for audio transcription
"""

import asyncio
import json
import websockets
from typing import Optional, Callable, AsyncGenerator
from datetime import datetime
from app.models.schemas import ASRConfigRequest, ASRTranscriptResponse
from app.core.config import settings
from app.core.logging import get_logger


class ASRClient:
    """WebSocket client for ASR service"""
    
    def __init__(self):
        self.logger = get_logger("asr_client")
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.is_processing = False
        
    async def connect(self, config: ASRConfigRequest) -> bool:
        """
        Connect to ASR service
        
        Args:
            config: ASR configuration
            
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            asr_url = f"{settings.asr_service_url}/ws/asr-stream"
            self.logger.info(f"Connecting to ASR service: {asr_url}")
            
            self.websocket = await asyncio.wait_for(
                websockets.connect(asr_url),
                timeout=settings.asr_timeout_seconds
            )
            
            # Send initial configuration
            config_data = config.dict()
            await self.websocket.send(json.dumps(config_data))
            
            # Wait for acknowledgment
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") == "metadata" and response_data.get("status") == "ready":
                self.is_connected = True
                self.logger.info("ASR service connected successfully")
                return True
            else:
                self.logger.error(f"Unexpected ASR response: {response_data}")
                await self.disconnect()
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to ASR service: {e}")
            await self.disconnect()
            return False
    
    async def disconnect(self):
        """Disconnect from ASR service"""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                self.logger.warning(f"Error closing ASR connection: {e}")
            finally:
                self.websocket = None
                self.is_connected = False
                self.is_processing = False
                self.logger.info("Disconnected from ASR service")
    
    async def send_audio_chunk(self, audio_data: bytes) -> bool:
        """
        Send audio chunk to ASR service
        
        Args:
            audio_data: Audio data bytes
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_connected or not self.websocket:
            self.logger.error("ASR service not connected")
            return False
        
        try:
            await self.websocket.send(audio_data)
            self.logger.debug(f"Sent audio chunk: {len(audio_data)} bytes")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send audio chunk: {e}")
            return False
    
    async def listen_for_transcripts(self, callback: Callable[[ASRTranscriptResponse], None]) -> None:
        """
        Listen for transcript messages from ASR service
        
        Args:
            callback: Function to call with transcript responses
        """
        if not self.is_connected or not self.websocket:
            self.logger.error("ASR service not connected")
            return
        
        # Prevent multiple listening tasks
        if self.is_processing:
            self.logger.warning("Already listening for transcripts, skipping duplicate call")
            return
        
        self.is_processing = True
        self.logger.info("Started listening for ASR transcripts")
        
        try:
            while self.is_connected and self.is_processing:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=1.0
                    )
                    
                    # Parse JSON message
                    try:
                        data = json.loads(message)
                        transcript = ASRTranscriptResponse(**data)
                        callback(transcript)
                        
                        # Check if this is a final transcript
                        if transcript.is_final:
                            self.logger.info(f"Final transcript received: {transcript.text}")
                        else:
                            self.logger.debug(f"Interim transcript: {transcript.text}")
                            
                    except json.JSONDecodeError:
                        self.logger.warning(f"Received non-JSON message: {message}")
                    except Exception as e:
                        self.logger.error(f"Error processing transcript message: {e}")
                        
                except asyncio.TimeoutError:
                    # Continue listening
                    continue
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning("ASR WebSocket connection closed")
                    break
                except Exception as e:
                    self.logger.error(f"Error receiving ASR message: {e}")
                    break
                    
        finally:
            self.is_processing = False
            self.logger.info("Stopped listening for ASR transcripts")
    
    async def stop_listening(self):
        """Stop listening for transcripts"""
        self.is_processing = False
        self.logger.info("Stopping ASR transcript listening")
    
    async def transcribe_audio_stream(self, audio_stream: AsyncGenerator[bytes, None], 
                                    callback: Callable[[ASRTranscriptResponse], None]) -> Optional[str]:
        """
        Transcribe a complete audio stream
        
        Args:
            audio_stream: Async generator yielding audio chunks
            callback: Function to call with transcript responses
            
        Returns:
            Final transcript text or None if failed
        """
        if not await self.connect(ASRConfigRequest()):
            return None
        
        final_transcript = None
        
        try:
            # Start listening task
            listen_task = asyncio.create_task(
                self.listen_for_transcripts(callback)
            )
            
            # Send audio chunks
            async for audio_chunk in audio_stream:
                if not await self.send_audio_chunk(audio_chunk):
                    break
            
            # Wait a bit for final transcript
            await asyncio.sleep(1.0)
            
            # Stop listening
            await self.stop_listening()
            
            # Wait for listen task to complete
            try:
                await asyncio.wait_for(listen_task, timeout=5.0)
            except asyncio.TimeoutError:
                self.logger.warning("Timeout waiting for ASR listening task")
                listen_task.cancel()
            
            return final_transcript
            
        except Exception as e:
            self.logger.error(f"Error in audio stream transcription: {e}")
            return None
        finally:
            await self.disconnect()
    
    def is_ready(self) -> bool:
        """Check if ASR client is ready for use"""
        return self.is_connected and not self.is_processing
    
    async def health_check(self) -> bool:
        """
        Check ASR service health
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            if not await self.connect(ASRConfigRequest()):
                return False
            
            await self.disconnect()
            return True
            
        except Exception as e:
            self.logger.error(f"ASR health check failed: {e}")
            return False


class ASRClientManager:
    """Manages multiple ASR client instances"""
    
    def __init__(self):
        self.logger = get_logger("asr_manager")
        self.clients: dict[str, ASRClient] = {}
    
    async def get_client(self, session_id: str) -> ASRClient:
        """
        Get or create ASR client for session
        
        Args:
            session_id: Session identifier
            
        Returns:
            ASR client instance
        """
        if session_id not in self.clients:
            self.clients[session_id] = ASRClient()
            self.logger.info(f"Created ASR client for session: {session_id}")
        
        return self.clients[session_id]
    
    async def cleanup_client(self, session_id: str):
        """
        Cleanup ASR client for session
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.clients:
            client = self.clients[session_id]
            await client.disconnect()
            del self.clients[session_id]
            self.logger.info(f"Cleaned up ASR client for session: {session_id}")
    
    async def cleanup_all(self):
        """Cleanup all ASR clients"""
        for session_id in list(self.clients.keys()):
            await self.cleanup_client(session_id)
        self.logger.info("Cleaned up all ASR clients")


# Global ASR client manager
asr_manager = ASRClientManager()


def get_asr_manager() -> ASRClientManager:
    """Get the global ASR client manager"""
    return asr_manager
