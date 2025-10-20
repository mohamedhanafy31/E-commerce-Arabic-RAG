"""
Main Orchestrator Service
Coordinates ASR, RAG, and TTS clients for conversational flow
"""

import asyncio
import uuid
from typing import Optional, AsyncGenerator, Callable
import json
import base64
from datetime import datetime
from fastapi import WebSocket

from app.models.schemas import (
    ConversationState, TranscriptMessage, RAGResponseMessage, 
    AudioChunkMessage, ErrorMessage, StateMessage, CompleteMessage,
    ASRConfigRequest, AudioConfig
)
from app.services.asr_client import get_asr_manager
from app.services.rag_client import get_rag_manager
from app.services.tts_client import get_tts_manager
from app.utils.session_manager import get_session_manager
from app.core.config import settings
from app.core.logging import get_logger, SessionLogger


class ConversationSession:
    """Manages a single conversation session"""
    
    def __init__(self, session_id: str, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.logger = SessionLogger(session_id, "conversation")
        
        # Service managers
        self.asr_manager = get_asr_manager()
        self.rag_manager = get_rag_manager()
        self.tts_manager = get_tts_manager()
        self.session_manager = get_session_manager()
        
        # State management
        self.current_state = ConversationState.IDLE
        self.is_active = True
        self.audio_buffer = []
        self.final_transcript = ""
        self.final_segments: list[str] = []
        self.latest_interim: str = ""
        
        # Tasks
        self.asr_task: Optional[asyncio.Task] = None
        self.processing_task: Optional[asyncio.Task] = None
        
    async def start_conversation(self, audio_config: AudioConfig) -> bool:
        """
        Start a new conversation session
        
        Args:
            audio_config: Audio configuration
            
        Returns:
            True if started successfully, False otherwise
        """
        try:
            # Update session state
            await self.session_manager.update_session_state(self.session_id, ConversationState.LISTENING)
            await self._update_state(ConversationState.LISTENING)
            
            self.logger.info("Conversation session started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start conversation: {e}")
            await self._send_error("session_start_failed", str(e))
            return False
    
    async def process_audio_chunk(self, audio_data: bytes) -> bool:
        """
        Process incoming audio chunk
        
        Args:
            audio_data: Audio data bytes
            
        Returns:
            True if processed successfully, False otherwise
        """
        try:
            if self.current_state != ConversationState.LISTENING:
                self.logger.warning(f"Received audio in wrong state: {self.current_state}")
                return False
            
            # Add to buffer
            self.audio_buffer.append(audio_data)
            
            # Get ASR client and send audio
            asr_client = await self.asr_manager.get_client(self.session_id)
            
            if not asr_client.is_connected:
                # Connect to ASR service
                config = ASRConfigRequest(
                    language_code=settings.default_language_code,
                    sample_rate_hertz=settings.audio_sample_rate,
                    encoding=settings.audio_format
                )
                
                if not await asr_client.connect(config):
                    self.logger.error("Failed to connect to ASR service")
                    return False
                
                # Start listening for transcripts only if not already running
                if not hasattr(self, 'asr_task') or self.asr_task is None or self.asr_task.done():
                    self.asr_task = asyncio.create_task(
                        self._listen_for_transcripts(asr_client)
                    )
            
            # Send audio chunk to ASR
            success = await asr_client.send_audio_chunk(audio_data)
            if not success:
                self.logger.error("Failed to send audio chunk to ASR")
                return False
            
            self.logger.debug(f"Processed audio chunk: {len(audio_data)} bytes")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing audio chunk: {e}")
            await self._send_error("audio_processing_failed", str(e))
            return False
    
    async def end_audio_input(self) -> bool:
        """
        Signal end of audio input and start processing
        
        Returns:
            True if processing started successfully, False otherwise
        """
        try:
            if self.current_state != ConversationState.LISTENING:
                self.logger.warning(f"Cannot end audio input in state: {self.current_state}")
                return False
            
            # Update state to processing
            await self.session_manager.update_session_state(self.session_id, ConversationState.PROCESSING)
            await self._update_state(ConversationState.PROCESSING)
            
            # Start processing task
            self.processing_task = asyncio.create_task(self._process_conversation())
            
            self.logger.info("Audio input ended, processing started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ending audio input: {e}")
            await self._send_error("audio_end_failed", str(e))
            return False
    
    async def _listen_for_transcripts(self, asr_client):
        """Listen for transcript messages from ASR"""
        try:
            def transcript_callback(transcript_response):
                asyncio.create_task(self._handle_transcript(transcript_response))
            
            await asr_client.listen_for_transcripts(transcript_callback)
            
        except Exception as e:
            self.logger.error(f"Error in transcript listening: {e}")
    
    async def _handle_transcript(self, transcript_response):
        """Handle transcript message from ASR"""
        try:
            # Send transcript to client
            transcript_msg = TranscriptMessage(
                text=transcript_response.text or "",
                is_final=transcript_response.is_final or False,
                confidence=transcript_response.confidence
            )
            
            await self._send_message(transcript_msg)
            
            # Track transcripts
            if transcript_response.is_final and transcript_response.text:
                # Accumulate final segments to preserve the full utterance
                self.final_segments.append(transcript_response.text.strip())
                self.final_transcript = " ".join(s for s in self.final_segments if s)
                self.latest_interim = ""
                self.logger.info(f"Final transcript segment added: {transcript_response.text}")
            else:
                # Keep latest interim as fallback if no final arrives
                self.latest_interim = (transcript_response.text or "").strip()
            
        except Exception as e:
            self.logger.error(f"Error handling transcript: {e}")
    
    async def _process_conversation(self):
        """Process the complete conversation flow"""
        try:
            # Wait briefly for final transcript to arrive from ASR
            await asyncio.sleep(1.0)

            # Fallback: if no final transcript, use latest high-confidence interim
            if not self.final_transcript and self.latest_interim:
                self.final_transcript = self.latest_interim
            
            if not self.final_transcript:
                self.logger.error("No final transcript received")
                await self._send_error("no_transcript", "No transcript received from ASR")
                return

            # Build context
            conversation_history = ""
            if settings.enable_conversation_history:
                conversation_history = await self.session_manager.get_context_for_rag(self.session_id)

            rag_client = await self.rag_manager.get_client()
            aggregated_answer = None
            aggregated_processing_ms = None

            if settings.enable_sentence_streaming:
                # Stream sentences and aggregate to a single answer string for history
                collected_sentences: list[str] = []
                async for sentence in rag_client.stream_response_sentences(
                    self.final_transcript,
                    conversation_history=conversation_history
                ):
                    collected_sentences.append(sentence)
                    await self._process_sentence(sentence)
                aggregated_answer = " ".join(collected_sentences).strip()
            else:
                rag_response = await rag_client.query(
                    self.final_transcript,
                    conversation_history=conversation_history
                )
                if rag_response:
                    await self._process_rag_response(rag_response)
                    aggregated_answer = rag_response.answer
                    aggregated_processing_ms = rag_response.processing_time_ms
                else:
                    await self._send_error("rag_failed", "Failed to get RAG response")
                    return

            # Persist conversation turn if enabled and we have an answer
            if settings.enable_conversation_history and aggregated_answer:
                await self.session_manager.add_conversation_turn(
                    self.session_id,
                    self.final_transcript,
                    aggregated_answer,
                    aggregated_processing_ms or 0
                )
            
            # Send completion message
            await self._send_message(CompleteMessage(session_id=self.session_id))
            
            # Update state to idle
            await self.session_manager.update_session_state(self.session_id, ConversationState.IDLE)
            await self._update_state(ConversationState.IDLE)
            
            self.logger.info("Conversation processing completed")
            
        except Exception as e:
            self.logger.error(f"Error in conversation processing: {e}")
            await self._send_error("processing_failed", str(e))
        finally:
            # Cleanup
            await self._cleanup_session()
    
    async def _process_sentence(self, sentence: str):
        """Process a single sentence through TTS"""
        try:
            # Send RAG response message
            rag_msg = RAGResponseMessage(text=sentence)
            await self._send_message(rag_msg)
            
            # Update state to speaking
            await self.session_manager.update_session_state(self.session_id, ConversationState.SPEAKING)
            await self._update_state(ConversationState.SPEAKING)
            
            # Synthesize with TTS
            tts_client = await self.tts_manager.get_client(self.session_id)
            
            async for audio_chunk in tts_client.stream_synthesis(sentence):
                audio_msg = AudioChunkMessage(
                    audio_data=audio_chunk,
                    sentence_index=0  # Could track sentence index
                )
                await self._send_message(audio_msg)
            
            self.logger.debug(f"Processed sentence: {sentence[:30]}...")
            
        except Exception as e:
            self.logger.error(f"Error processing sentence: {e}")
    
    async def _process_rag_response(self, rag_response):
        """Process complete RAG response"""
        try:
            # Send RAG response message
            rag_msg = RAGResponseMessage(
                text=rag_response.answer,
                sources=rag_response.sources,
                processing_time_ms=rag_response.processing_time_ms,
                model_used=rag_response.model_used
            )
            await self._send_message(rag_msg)
            
            # Update state to speaking
            await self.session_manager.update_session_state(self.session_id, ConversationState.SPEAKING)
            await self._update_state(ConversationState.SPEAKING)
            
            # Synthesize with TTS
            tts_client = await self.tts_manager.get_client(self.session_id)
            
            # Split into sentences and synthesize
            sentences = self._split_into_sentences(rag_response.answer)
            
            async for audio_chunk in tts_client.synthesize_sentences(sentences):
                audio_msg = AudioChunkMessage(audio_data=audio_chunk)
                await self._send_message(audio_msg)
            
            self.logger.info(f"Processed RAG response: {rag_response.answer[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Error processing RAG response: {e}")
    
    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences"""
        if not text:
            return []
        
        # Arabic sentence endings
        sentence_endings = ['.', '!', '?', '؟', '!', '۔']
        
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            
            if char in sentence_endings:
                sentence = current_sentence.strip()
                if sentence:
                    sentences.append(sentence)
                current_sentence = ""
        
        # Add remaining text
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences
    
    async def _update_state(self, new_state: ConversationState):
        """Update conversation state"""
        try:
            previous_state = self.current_state
            self.current_state = new_state
            
            state_msg = StateMessage(
                state=new_state,
                previous_state=previous_state
            )
            
            await self._send_message(state_msg)
            self.logger.debug(f"State updated: {previous_state} -> {new_state}")
            
        except Exception as e:
            self.logger.error(f"Error updating state: {e}")
    
    async def _send_message(self, message):
        """Send message to WebSocket client"""
        try:
            if self.is_active and self.websocket:
                # Ensure binary audio is base64-encoded before JSON serialization
                if isinstance(message, AudioChunkMessage):
                    # Build payload without serializing bytes first, then base64 the audio and ISO-format datetimes
                    payload = message.dict()
                    try:
                        payload["audio_data"] = base64.b64encode(message.audio_data).decode("ascii") if message.audio_data else ""
                    except Exception:
                        payload["audio_data"] = ""
                    # Ensure datetimes are JSON-serializable
                    ts = payload.get("timestamp")
                    if ts is not None:
                        try:
                            payload["timestamp"] = ts.isoformat()
                        except Exception:
                            pass
                    await self.websocket.send_text(json.dumps(payload))
                else:
                    await self.websocket.send_text(message.json())
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
    
    async def _send_error(self, error_code: str, detail: str):
        """Send error message to client"""
        try:
            error_msg = ErrorMessage(error_code=error_code, detail=detail)
            await self._send_message(error_msg)
            
            # Update state to error
            await self.session_manager.update_session_state(self.session_id, ConversationState.ERROR)
            await self._update_state(ConversationState.ERROR)
            
        except Exception as e:
            self.logger.error(f"Error sending error message: {e}")
    
    async def _cleanup_session(self):
        """Cleanup session resources"""
        try:
            # Cancel tasks
            if self.asr_task and not self.asr_task.done():
                self.asr_task.cancel()
            
            if self.processing_task and not self.processing_task.done():
                self.processing_task.cancel()
            
            # Cleanup clients
            await self.asr_manager.cleanup_client(self.session_id)
            await self.tts_manager.cleanup_client(self.session_id)
            
            self.is_active = False
            self.logger.info("Session cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error in session cleanup: {e}")
    
    async def close(self):
        """Close the conversation session"""
        try:
            await self._cleanup_session()
            
            # Close WebSocket
            if self.websocket:
                await self.websocket.close()
            
            self.logger.info("Conversation session closed")
            
        except Exception as e:
            self.logger.error(f"Error closing session: {e}")


class OrchestratorService:
    """Main orchestrator service"""
    
    def __init__(self):
        self.logger = get_logger("orchestrator")
        self.active_sessions: dict[str, ConversationSession] = {}
        self.session_manager = get_session_manager()
    
    async def create_session(self, websocket: WebSocket, audio_config: AudioConfig) -> Optional[str]:
        """
        Create a new conversation session
        
        Args:
            websocket: WebSocket connection
            audio_config: Audio configuration
            
        Returns:
            Session ID or None if failed
        """
        try:
            # Check session limit
            if len(self.active_sessions) >= settings.max_concurrent_sessions:
                self.logger.warning("Maximum concurrent sessions reached")
                return None
            
            # Create session
            session_id = await self.session_manager.create_session(audio_config)
            if not session_id:
                return None
            
            # Create conversation session
            conversation_session = ConversationSession(session_id, websocket)
            
            # Start conversation
            if await conversation_session.start_conversation(audio_config):
                self.active_sessions[session_id] = conversation_session
                self.logger.info(f"Created conversation session: {session_id}")
                return session_id
            else:
                await self.session_manager.delete_session(session_id)
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating session: {e}")
            return None
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get conversation session by ID"""
        return self.active_sessions.get(session_id)
    
    async def close_session(self, session_id: str):
        """Close a conversation session"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                await session.close()
                del self.active_sessions[session_id]
                
                # Cleanup from session manager
                await self.session_manager.delete_session(session_id)
                
                self.logger.info(f"Closed conversation session: {session_id}")
                
        except Exception as e:
            self.logger.error(f"Error closing session {session_id}: {e}")
    
    async def cleanup_all_sessions(self):
        """Cleanup all active sessions"""
        for session_id in list(self.active_sessions.keys()):
            await self.close_session(session_id)
        self.logger.info("Cleaned up all conversation sessions")


# Global orchestrator service
orchestrator_service = OrchestratorService()


def get_orchestrator_service() -> OrchestratorService:
    """Get the global orchestrator service"""
    return orchestrator_service
