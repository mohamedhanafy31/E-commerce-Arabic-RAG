"""
TTS Client for Orchestrator
Handles WebSocket communication with TTS API for speech synthesis
"""

import asyncio
import json
import websockets
from typing import Optional, Callable, AsyncGenerator
from datetime import datetime
from app.models.schemas import TTSRequest, TTSMetadataResponse, TTSCompleteResponse
from app.core.config import settings
from app.core.logging import get_logger


class TTSClient:
    """WebSocket client for TTS service"""
    
    def __init__(self):
        self.logger = get_logger("tts_client")
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.is_processing = False
        self.current_request_id: Optional[str] = None
        
    async def connect(self) -> bool:
        """
        Connect to TTS service
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            tts_url = f"{settings.tts_service_url}/ws/tts-stream"
            self.logger.info(f"Connecting to TTS service: {tts_url}")
            
            # websockets.connect uses open_timeout/close_timeout
            self.websocket = await websockets.connect(
                tts_url,
                open_timeout=settings.tts_timeout_seconds
            )
            
            self.is_connected = True
            self.logger.info("TTS service connected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to TTS service: {e}")
            await self.disconnect()
            return False
    
    async def disconnect(self):
        """Disconnect from TTS service"""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                self.logger.warning(f"Error closing TTS connection: {e}")
            finally:
                self.websocket = None
                self.is_connected = False
                self.is_processing = False
                self.current_request_id = None
                self.logger.info("Disconnected from TTS service")
    
    async def synthesize_text(self, text: str, voice_gender: Optional[str] = None,
                            callback: Optional[Callable[[bytes], None]] = None) -> Optional[bytes]:
        """
        Synthesize text to speech
        
        Args:
            text: Text to synthesize
            voice_gender: Voice gender preference
            callback: Optional callback for audio chunks
            
        Returns:
            Complete audio data or None if failed
        """
        if not self.is_connected:
            if not await self.connect():
                return None
        
        try:
            # Prepare TTS request
            request = TTSRequest(
                text=text,
                language_code=settings.tts_language_code,
                voice_gender_choice=voice_gender or settings.tts_voice_gender,
                audio_encoding="MP3"
            )
            
            self.logger.info(f"Synthesizing text: {text[:50]}...")
            
            # Send TTS request
            await self.websocket.send(json.dumps(request.dict()))
            
            # Collect audio chunks
            audio_chunks = []
            metadata_received = False
            
            while True:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=settings.tts_timeout_seconds
                    )

                    # If we received raw binary, treat as audio chunk immediately
                    if isinstance(message, (bytes, bytearray)):
                        audio_chunks.append(bytes(message))
                        if callback:
                            callback(bytes(message))
                        self.logger.debug(f"Received audio chunk: {len(message)} bytes")
                        continue

                    # Otherwise, expect a JSON control message (metadata/complete/error)
                    if isinstance(message, str):
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            self.logger.warning("Received non-JSON text message from TTS; ignoring")
                            continue

                        message_type = data.get("type", "")
                        if message_type == "metadata":
                            metadata = TTSMetadataResponse(**data)
                            metadata_received = True
                            self.logger.debug(f"TTS metadata: voice={metadata.voice_used}, chunks={metadata.total_chunks}")
                        elif message_type == "complete":
                            completion = TTSCompleteResponse(**data)
                            self.logger.info(f"TTS completed: {completion.successful_chunks} successful, {completion.failed_chunks} failed")
                            break
                        elif message_type == "error":
                            error_detail = data.get("detail", "Unknown error")
                            self.logger.error(f"TTS error: {error_detail}")
                            return None
                        else:
                            self.logger.warning(f"Unknown TTS message type: {message_type}")
                            continue
                    else:
                        self.logger.warning(f"Received unexpected message type: {type(message)}")
                            
                except asyncio.TimeoutError:
                    self.logger.error("TTS request timeout")
                    return None
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning("TTS WebSocket connection closed")
                    break
                except Exception as e:
                    self.logger.error(f"Error receiving TTS message: {e}")
                    break
            
            if audio_chunks:
                # Combine all audio chunks
                complete_audio = b''.join(audio_chunks)
                self.logger.info(f"Synthesized audio: {len(complete_audio)} bytes total")
                return complete_audio
            else:
                self.logger.error("No audio data received from TTS")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in TTS synthesis: {e}")
            return None
    
    async def stream_synthesis(self, text: str, voice_gender: Optional[str] = None) -> AsyncGenerator[bytes, None]:
        """
        Stream TTS synthesis audio chunks
        
        Args:
            text: Text to synthesize
            voice_gender: Voice gender preference
            
        Yields:
            Audio chunks as they are received
        """
        if not self.is_connected:
            if not await self.connect():
                return
        
        try:
            # Prepare TTS request
            request = TTSRequest(
                text=text,
                language_code=settings.tts_language_code,
                voice_gender_choice=voice_gender or settings.tts_voice_gender,
                audio_encoding="MP3"
            )
            
            self.logger.info(f"Streaming TTS synthesis: {text[:50]}...")
            
            # Send TTS request
            await self.websocket.send(json.dumps(request.dict()))
            
            # Stream audio chunks
            while True:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=settings.tts_timeout_seconds
                    )

                    if isinstance(message, (bytes, bytearray)):
                        chunk = bytes(message)
                        yield chunk
                        self.logger.debug(f"Streamed audio chunk: {len(chunk)} bytes")
                        continue

                    if isinstance(message, str):
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            self.logger.warning("Received non-JSON text message from TTS during streaming; ignoring")
                            continue

                        message_type = data.get("type", "")
                        if message_type == "complete":
                            completion = TTSCompleteResponse(**data)
                            self.logger.info(f"TTS streaming completed: {completion.successful_chunks} successful")
                            break
                        elif message_type == "error":
                            error_detail = data.get("detail", "Unknown error")
                            self.logger.error(f"TTS streaming error: {error_detail}")
                            break
                        else:
                            self.logger.warning(f"Unknown TTS control message: {message_type}")
                            continue

                except asyncio.TimeoutError:
                    self.logger.error("TTS streaming timeout")
                    break
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning("TTS WebSocket connection closed during streaming")
                    break
                except Exception as e:
                    self.logger.error(f"Error in TTS streaming: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error starting TTS streaming: {e}")
    
    async def synthesize_sentences(self, sentences: list[str], voice_gender: Optional[str] = None) -> AsyncGenerator[bytes, None]:
        """
        Synthesize multiple sentences sequentially
        
        Args:
            sentences: List of sentences to synthesize
            voice_gender: Voice gender preference
            
        Yields:
            Audio chunks from all sentences
        """
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            self.logger.info(f"Synthesizing sentence {i+1}/{len(sentences)}: {sentence[:30]}...")
            
            async for audio_chunk in self.stream_synthesis(sentence, voice_gender):
                yield audio_chunk
            
            # Small delay between sentences
            await asyncio.sleep(0.1)
    
    async def health_check(self) -> bool:
        """
        Check TTS service health
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            if not await self.connect():
                return False
            
            # Try a simple synthesis
            test_audio = await self.synthesize_text("مرحبا", voice_gender="male")
            await self.disconnect()
            
            return test_audio is not None
            
        except Exception as e:
            self.logger.error(f"TTS health check failed: {e}")
            return False
    
    def is_ready(self) -> bool:
        """Check if TTS client is ready for use"""
        return self.is_connected and not self.is_processing


class TTSClientManager:
    """Manages multiple TTS client instances"""
    
    def __init__(self):
        self.logger = get_logger("tts_manager")
        self.clients: dict[str, TTSClient] = {}
    
    async def get_client(self, session_id: str) -> TTSClient:
        """
        Get or create TTS client for session
        
        Args:
            session_id: Session identifier
            
        Returns:
            TTS client instance
        """
        if session_id not in self.clients:
            self.clients[session_id] = TTSClient()
            self.logger.info(f"Created TTS client for session: {session_id}")
        
        return self.clients[session_id]
    
    async def cleanup_client(self, session_id: str):
        """
        Cleanup TTS client for session
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.clients:
            client = self.clients[session_id]
            await client.disconnect()
            del self.clients[session_id]
            self.logger.info(f"Cleaned up TTS client for session: {session_id}")
    
    async def cleanup_all(self):
        """Cleanup all TTS clients"""
        for session_id in list(self.clients.keys()):
            await self.cleanup_client(session_id)
        self.logger.info("Cleaned up all TTS clients")


# Global TTS client manager
tts_manager = TTSClientManager()


def get_tts_manager() -> TTSClientManager:
    """Get the global TTS client manager"""
    return tts_manager
