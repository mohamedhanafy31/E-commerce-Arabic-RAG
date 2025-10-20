import os
import time
import tempfile
from typing import Dict, List, Optional
from google.cloud import speech
from google.oauth2 import service_account
try:
    from pydub import AudioSegment
    from pydub.utils import which
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Warning: pydub not available, audio preprocessing will be limited")
import logging

from ..core.config import settings
from ..models.schemas import WordInfo


logger = logging.getLogger("asr")


class ASRError(Exception):
    """Base exception for ASR operations"""
    pass


class CredentialsError(ASRError):
    """Error with Google Cloud credentials"""
    pass


class AudioProcessingError(ASRError):
    """Error during audio processing"""
    pass


class TranscriptionError(ASRError):
    """Error during transcription"""
    pass


class ASRProcessor:
    def __init__(self):
        self.speech_client = None
        self.setup_credentials()
        self.setup_audio_processor()
    
    def setup_credentials(self):
        """Setup Google Cloud credentials from environment variable or file"""
        credentials_path = settings.google_application_credentials or 'tts-key.json'
        
        if os.path.exists(credentials_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.speech_client = speech.SpeechClient(credentials=credentials)
                logger.info("✓ Google Cloud credentials loaded successfully")
            except Exception as e:
                logger.error(f"❌ Error loading credentials from {credentials_path}: {str(e)}")
                raise CredentialsError(f"Failed to load credentials: {str(e)}")
        else:
            logger.error(f"❌ Error: {credentials_path} not found!")
            logger.info("💡 Set GOOGLE_APPLICATION_CREDENTIALS environment variable or ensure tts-key.json exists")
            raise CredentialsError(f"Credentials file not found: {credentials_path}")
    
    def setup_audio_processor(self):
        """Setup audio processing capabilities"""
        # Check if ffmpeg is available
        if not which("ffmpeg"):
            logger.warning("⚠️  ffmpeg not found. Some audio formats may not be supported.")
            logger.info("💡 Install ffmpeg: sudo apt install ffmpeg (Ubuntu/Debian) or brew install ffmpeg (macOS)")
        else:
            logger.info("✓ ffmpeg found - full audio format support available")
    
    def chunk_audio(self, audio_file_path: str, chunk_duration_minutes: float = 0.5) -> List[str]:
        """
        Chunk audio file into segments of specified duration
        
        Args:
            audio_file_path: Path to the audio file
            chunk_duration_minutes: Duration of each chunk in minutes (default: 0.5 = 30 seconds)
            
        Returns:
            List of temporary file paths for audio chunks
        """
        logger.info(f"📁 Processing audio file: {audio_file_path}")
        
        # Check file size
        file_size = os.path.getsize(audio_file_path)
        file_size_mb = file_size / (1024 * 1024)
        logger.info(f"📊 File size: {file_size_mb:.2f} MB")
        
        # Check if ffmpeg is available for chunking
        if not which("ffmpeg"):
            logger.warning("⚠️  ffmpeg not available, processing entire file as single chunk")
            logger.info("💡 For large files, consider installing ffmpeg for better chunking")
            return [audio_file_path]
        
        try:
            # Load audio file
            audio = AudioSegment.from_file(audio_file_path)
            logger.info(f"🎵 Audio loaded: {len(audio)}ms duration, {audio.frame_rate}Hz, {audio.channels} channels")
            
            # Calculate chunk duration in milliseconds
            chunk_duration_ms = chunk_duration_minutes * 60 * 1000
            
            # Create chunks
            chunks = []
            chunk_files = []
            
            for i in range(0, len(audio), int(chunk_duration_ms)):
                chunk = audio[i:i + chunk_duration_ms]
                chunks.append(chunk)
                
                # Create temporary file for this chunk
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                chunk.export(temp_file.name, format="wav")
                chunk_files.append(temp_file.name)
                
                logger.info("📦 Created chunk %d: %dms", len(chunk_files), len(chunk))
            
            logger.info(f"✅ Created {len(chunk_files)} audio chunks")
            return chunk_files
            
        except Exception as e:
            logger.error(f"❌ Error chunking audio: {str(e)}")
            logger.info("💡 Falling back to processing entire file as single chunk")
            raise AudioProcessingError(f"Failed to chunk audio: {str(e)}")
    
    def preprocess_audio(self, audio_file_path: str) -> str:
        """
        Preprocess audio file for better ASR results
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Path to the preprocessed audio file
        """
        try:
            # Check if pydub is available
            if not PYDUB_AVAILABLE:
                logger.warning("⚠️  pydub not available, skipping audio preprocessing")
                return audio_file_path
                
            # Check if ffmpeg is available
            if not which("ffmpeg"):
                logger.warning("⚠️  ffmpeg not available, skipping audio preprocessing")
                logger.info("💡 For MP3 files, Google Cloud Speech-to-Text can handle them directly")
                return audio_file_path
            
            # Load audio
            audio = AudioSegment.from_file(audio_file_path)
            logger.info(f"🔧 Preprocessing audio: {len(audio)}ms")
            
            # Apply preprocessing
            # 1. Normalize volume
            audio = audio.normalize()
            
            # 2. Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
                logger.info("🔊 Converted to mono")
            
            # 3. Set sample rate to 16kHz (optimal for Google Speech-to-Text)
            if audio.frame_rate != 16000:
                audio = audio.set_frame_rate(16000)
                logger.info(f"🎯 Set sample rate to 16kHz")
            
            # 4. Apply high-pass filter to remove low-frequency noise
            audio = audio.high_pass_filter(80)
            
            # Create temporary file for preprocessed audio
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            audio.export(temp_file.name, format="wav")
            
            logger.info("✅ Audio preprocessing completed")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"❌ Error preprocessing audio: {str(e)}")
            logger.info("💡 Falling back to original file without preprocessing")
            raise AudioProcessingError(f"Failed to preprocess audio: {str(e)}")
    
    def transcribe_chunk(self, chunk_file_path: str, language_code: str = "ar-EG", enable_word_timestamps: bool = True) -> Dict:
        """
        Transcribe a single audio chunk
        
        Args:
            chunk_file_path: Path to the audio chunk file
            language_code: Language code for transcription
            enable_word_timestamps: Whether to include word-level timestamps
            
        Returns:
            Dictionary with transcript, confidence, and words
        """
        try:
            with open(chunk_file_path, "rb") as f:
                audio_data = f.read()
            
            audio = speech.RecognitionAudio(content=audio_data)
            
            # Determine encoding based on file extension
            file_ext = os.path.splitext(chunk_file_path)[1].lower()
            
            if file_ext == '.mp3':
                # Try MP3 encoding first (beta feature)
                try:
                    config = speech.RecognitionConfig(
                        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
                        sample_rate_hertz=16000,
                        language_code=language_code,
                        enable_automatic_punctuation=True,
                        enable_word_time_offsets=enable_word_timestamps
                    )
                    logger.info("🎵 Using MP3 encoding (beta feature)")
                except AttributeError:
                    # Fallback to auto-detection
                    config = speech.RecognitionConfig(
                        encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                        sample_rate_hertz=16000,
                        language_code=language_code,
                        enable_automatic_punctuation=True,
                        enable_word_time_offsets=enable_word_timestamps
                    )
                    logger.info("🔍 Using auto-detection for MP3 format")
            else:
                # Use LINEAR16 for WAV files
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code=language_code,
                    enable_automatic_punctuation=True,
                    enable_word_time_offsets=enable_word_timestamps
                )
                logger.info("🎵 Using LINEAR16 encoding for WAV")
            
            response = self.speech_client.recognize(config=config, audio=audio)
            
            if response.results:
                result = response.results[0]
                alternative = result.alternatives[0]
                
                # Process word-level timestamps if available
                words = []
                if enable_word_timestamps and hasattr(alternative, 'words') and alternative.words:
                    for word in alternative.words:
                        start_time = word.start_time.total_seconds() if word.start_time else 0
                        end_time = word.end_time.total_seconds() if word.end_time else 0
                        words.append(WordInfo(
                            word=word.word,
                            start_time=start_time,
                            end_time=end_time,
                            confidence=getattr(word, 'confidence', None)
                        ))
                
                return {
                    'transcript': alternative.transcript,
                    'confidence': alternative.confidence,
                    'words': words
                }
            else:
                return {'transcript': '', 'confidence': 0.0, 'words': []}
                
        except Exception as e:
            logger.error(f"❌ Error transcribing chunk {chunk_file_path}: {str(e)}")
            raise TranscriptionError(f"Failed to transcribe chunk: {str(e)}")
    
    def process_audio_file(self, audio_file_path: str, language_code: str = "ar-EG", 
                          chunk_duration_minutes: float = 0.5, enable_preprocessing: bool = True,
                          enable_word_timestamps: bool = True) -> Dict:
        """
        Process entire audio file with chunking and transcription
        
        Args:
            audio_file_path: Path to the audio file
            language_code: Language code for transcription
            chunk_duration_minutes: Duration of each chunk in minutes
            enable_preprocessing: Whether to preprocess audio
            enable_word_timestamps: Whether to include word-level timestamps
            
        Returns:
            Dictionary with complete transcription results
        """
        if not os.path.exists(audio_file_path):
            logger.error(f"❌ Error: {audio_file_path} not found!")
            raise AudioProcessingError(f"Audio file not found: {audio_file_path}")
        
        logger.info(f"🚀 Starting ASR processing for: {audio_file_path}")
        start_time = time.time()
        
        # Check file size limits
        file_size = os.path.getsize(audio_file_path)
        file_size_mb = file_size / (1024 * 1024)
        MAX_SYNC_SIZE = settings.max_file_size_mb * 1024 * 1024  # Convert MB to bytes
        
        if file_size > MAX_SYNC_SIZE and not which("ffmpeg"):
            logger.error(f"❌ File size ({file_size_mb:.2f} MB) exceeds Google Cloud's {settings.max_file_size_mb}MB limit!")
            raise AudioProcessingError(
                f"File too large ({file_size_mb:.2f} MB). "
                f"Install ffmpeg for chunking or use files < {settings.max_file_size_mb}MB"
            )
        
        preprocessed_file = audio_file_path
        chunk_files = []
        
        try:
            # Step 1: Preprocess audio if enabled
            if enable_preprocessing:
                preprocessed_file = self.preprocess_audio(audio_file_path)
            
            # Step 2: Chunk audio
            chunk_files = self.chunk_audio(preprocessed_file, chunk_duration_minutes)
            
            # Step 3: Transcribe each chunk
            all_transcripts = []
            all_words = []
            total_confidence = 0
            
            for i, chunk_file in enumerate(chunk_files):
                logger.info(f"🔄 Transcribing chunk {i+1}/{len(chunk_files)}")
                result = self.transcribe_chunk(chunk_file, language_code, enable_word_timestamps)
                
                if result['transcript']:
                    all_transcripts.append(result['transcript'])
                    all_words.extend(result['words'])
                    total_confidence += result['confidence']
                    logger.info(f"✅ Chunk {i+1}: {result['transcript'][:50]}...")
                else:
                    logger.warning(f"⚠️  Chunk {i+1}: No transcription result")
            
            # Step 4: Combine results
            full_transcript = " ".join(all_transcripts)
            avg_confidence = total_confidence / len(chunk_files) if chunk_files else 0
            
            processing_time = time.time() - start_time
            
            logger.info(f"🎉 Processing completed in {processing_time:.2f} seconds")
            logger.info(f"📝 Full transcript: {full_transcript}")
            logger.info(f"🎯 Average confidence: {avg_confidence:.2f}")
            
            return {
                'transcript': full_transcript,
                'confidence': avg_confidence,
                'language_code': language_code,
                'processing_time': processing_time,
                'chunks_processed': len(chunk_files),
                'words': all_words
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing audio file: {str(e)}")
            raise AudioProcessingError(f"Failed to process audio file: {str(e)}")
        
        finally:
            # Cleanup temporary files
            try:
                if preprocessed_file != audio_file_path:  # Only delete if it's a temp file
                    os.unlink(preprocessed_file)
                for chunk_file in chunk_files:
                    if chunk_file != audio_file_path:  # Only delete if it's a temp file
                        os.unlink(chunk_file)
            except Exception as e:
                logger.warning(f"⚠️  Error cleaning up temp files: {str(e)}")


def get_asr_service() -> ASRProcessor:
    """Dependency injection for ASR processor"""
    return ASRProcessor()
