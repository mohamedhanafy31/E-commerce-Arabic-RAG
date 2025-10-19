import os
import queue
import threading
import asyncio
import logging
import json
from typing import Generator
from google.cloud import speech
from google.cloud.speech import RecognitionConfig, StreamingRecognitionConfig, StreamingRecognizeRequest
from google.oauth2 import service_account

from ..core.config import settings
from ..models.schemas import StreamingConfigRequest

logger = logging.getLogger("asr")


class StreamingASRError(Exception):
    """Base exception for streaming ASR operations"""
    pass


class StreamingCredentialsError(StreamingASRError):
    """Error with Google Cloud credentials for streaming"""
    pass


class StreamingConfigError(StreamingASRError):
    """Error with streaming configuration"""
    pass


class StreamingASRProcessor:
    """Streaming ASR processor using Google Cloud Speech-to-Text streaming API"""
    
    def __init__(self):
        self.speech_client = None
        self.setup_credentials()
    
    def setup_credentials(self):
        """Setup Google Cloud credentials from environment variable or file"""
        credentials_path = settings.google_application_credentials or 'tts-key.json'
        
        if os.path.exists(credentials_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.speech_client = speech.SpeechClient(credentials=credentials)
                logger.info("✓ Google Cloud streaming credentials loaded successfully")
            except Exception as e:
                logger.error(f"❌ Error loading streaming credentials from {credentials_path}: {str(e)}")
                raise StreamingCredentialsError(f"Failed to load streaming credentials: {str(e)}")
        else:
            logger.error(f"❌ Error: {credentials_path} not found!")
            logger.info("💡 Set GOOGLE_APPLICATION_CREDENTIALS environment variable or ensure tts-key.json exists")
            raise StreamingCredentialsError(f"Credentials file not found: {credentials_path}")
    
    def create_streaming_config(self, language_code: str = None, sample_rate: int = None, encoding: str = None) -> StreamingRecognitionConfig:
        """
        Create Google Cloud streaming recognition configuration
        
        Args:
            language_code: Language code for transcription (default: from settings)
            sample_rate: Sample rate in Hz (default: from settings)
            encoding: Audio encoding (default: LINEAR16)
            
        Returns:
            StreamingRecognitionConfig object
        """
        # Use settings defaults, allow client overrides
        config_language = language_code or settings.default_language_code
        config_sample_rate = sample_rate or settings.default_sample_rate_hertz
        config_encoding = encoding or "LINEAR16"
        
        # Map encoding string to Google Cloud enum
        encoding_map = {
            "LINEAR16": RecognitionConfig.AudioEncoding.LINEAR16,
            "FLAC": RecognitionConfig.AudioEncoding.FLAC,
            "MULAW": RecognitionConfig.AudioEncoding.MULAW,
            "AMR": RecognitionConfig.AudioEncoding.AMR,
            "AMR_WB": RecognitionConfig.AudioEncoding.AMR_WB,
            "OGG_OPUS": RecognitionConfig.AudioEncoding.OGG_OPUS,
            "SPEEX_WITH_HEADER_BYTE": RecognitionConfig.AudioEncoding.SPEEX_WITH_HEADER_BYTE,
        }
        
        if config_encoding not in encoding_map:
            logger.warning(f"⚠️  Unsupported encoding '{config_encoding}', defaulting to LINEAR16")
            config_encoding = "LINEAR16"
        
        try:
            config = RecognitionConfig(
                encoding=encoding_map[config_encoding],
                sample_rate_hertz=config_sample_rate,
                language_code=config_language,
                enable_automatic_punctuation=settings.enable_automatic_punctuation,
                enable_word_time_offsets=False  # Not supported in streaming mode
            )
            
            streaming_config = StreamingRecognitionConfig(
                config=config,
                interim_results=settings.streaming_interim_results
            )
            
            logger.info(f"✓ Created streaming config: {config_language}, {config_sample_rate}Hz, {config_encoding}")
            return streaming_config
            
        except Exception as e:
            logger.error(f"❌ Error creating streaming config: {str(e)}")
            raise StreamingConfigError(f"Failed to create streaming configuration: {str(e)}")
    
    def process_audio_stream(self, audio_generator: Generator[bytes, None, None], 
                           websocket, loop: asyncio.AbstractEventLoop, streaming_config: StreamingRecognitionConfig) -> None:
        """
        Process audio stream using Google Cloud streaming API
        
        Args:
            audio_generator: Generator yielding audio chunks
            websocket: WebSocket connection for sending results
            loop: Asyncio event loop for thread-safe communication
            streaming_config: Google Cloud streaming configuration
        """
        try:
            # Create request generator with timeout handling
            def request_generator():
                chunk_count = 0
                for audio_chunk in audio_generator:
                    if audio_chunk is None:
                        break
                    chunk_count += 1
                    logger.debug(f"Processing audio chunk {chunk_count}: {len(audio_chunk)} bytes")
                    yield StreamingRecognizeRequest(audio_content=audio_chunk)
            
            # Process streaming recognition with timeout
            logger.info("Starting Google Cloud streaming recognition...")
            responses = self.speech_client.streaming_recognize(
                streaming_config, 
                request_generator()
            )
            
            for response in responses:
                if not response.results:
                    continue
                
                for result in response.results:
                    if not result.alternatives:
                        continue
                    
                    alternative = result.alternatives[0]
                    transcript = alternative.transcript
                    confidence = alternative.confidence
                    is_final = result.is_final
                    
                    # Create response message
                    message = {
                        "type": "transcript",
                        "text": transcript,
                        "is_final": is_final,
                        "confidence": confidence
                    }
                    
                    # Send message via WebSocket (thread-safe)
                    asyncio.run_coroutine_threadsafe(
                        websocket.send_text(json.dumps(message)),
                        loop
                    )
                    
                    logger.debug(f"📝 Sent transcript: '{transcript}' (final: {is_final}, conf: {confidence:.2f})")
            
            # Send completion signal
            complete_message = {"type": "complete"}
            asyncio.run_coroutine_threadsafe(
                websocket.send_text(json.dumps(complete_message)),
                loop
            )
            logger.info("✅ Streaming recognition completed")
            
        except Exception as e:
            logger.error(f"❌ Error in streaming recognition: {str(e)}")
            error_message = {
                "type": "error",
                "detail": f"Streaming recognition error: {str(e)}"
            }
            asyncio.run_coroutine_threadsafe(
                websocket.send_text(json.dumps(error_message)),
                loop
            )
    
    def start_streaming_session(self, config_request: StreamingConfigRequest) -> 'StreamingSession':
        """
        Start a new streaming session with given configuration
        
        Args:
            config_request: Streaming configuration from client
            
        Returns:
            StreamingSession object for managing the session
        """
        try:
            # Create streaming configuration
            streaming_config = self.create_streaming_config(
                language_code=config_request.language_code,
                sample_rate=config_request.sample_rate_hertz,
                encoding=config_request.encoding
            )
            
            # Create and return session
            session = StreamingSession(self, streaming_config)
            logger.info(f"🚀 Started streaming session: {config_request.language_code}")
            return session
            
        except Exception as e:
            logger.error(f"❌ Error starting streaming session: {str(e)}")
            raise StreamingASRError(f"Failed to start streaming session: {str(e)}")


class StreamingSession:
    """Manages a single streaming ASR session"""
    
    def __init__(self, processor: StreamingASRProcessor, streaming_config: StreamingRecognitionConfig):
        self.processor = processor
        self.streaming_config = streaming_config
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.recognition_thread = None
        self.loop = None
        self.websocket = None
    
    def start_recognition(self, websocket, loop: asyncio.AbstractEventLoop):
        """
        Start the recognition thread
        
        Args:
            websocket: WebSocket connection
            loop: Asyncio event loop
        """
        self.websocket = websocket
        self.loop = loop
        
        # Create audio generator
        def audio_generator():
            while not self.stop_event.is_set():
                try:
                    chunk = self.audio_queue.get(timeout=1.0)
                    if chunk is None:
                        break
                    yield chunk
                except queue.Empty:
                    continue
        
        # Start recognition thread
        self.recognition_thread = threading.Thread(
            target=self.processor.process_audio_stream,
            args=(audio_generator(), websocket, loop, self.streaming_config)
        )
        self.recognition_thread.start()
        logger.info("🎤 Recognition thread started")
    
    def add_audio_chunk(self, audio_chunk: bytes):
        """
        Add audio chunk to the processing queue
        
        Args:
            audio_chunk: Raw audio bytes
        """
        if not self.stop_event.is_set():
            self.audio_queue.put(audio_chunk)
    
    def stop_recognition(self):
        """Stop the recognition process"""
        logger.info("🛑 Stopping recognition...")
        self.stop_event.set()
        self.audio_queue.put(None)  # Signal end of stream
        
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=5.0)
            if self.recognition_thread.is_alive():
                logger.warning("⚠️  Recognition thread did not stop gracefully")
        
        logger.info("✅ Recognition stopped")


def get_streaming_asr_service() -> StreamingASRProcessor:
    """Dependency injection for streaming ASR processor"""
    return StreamingASRProcessor()
