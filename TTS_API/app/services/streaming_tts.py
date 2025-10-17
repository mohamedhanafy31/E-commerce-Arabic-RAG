import asyncio
import logging
from typing import AsyncGenerator, List, Optional, Tuple
from ..services.gcp_tts import GoogleTTSService
from ..services.text_chunker import ArabicTextChunker


logger = logging.getLogger(__name__)


class StreamingTTSService:
    """
    Service for streaming TTS using Google Cloud TTS with sentence-based chunking.
    Provides async streaming of audio chunks with retry logic.
    """
    
    def __init__(self):
        self.tts_service = GoogleTTSService()
        self.text_chunker = ArabicTextChunker()
        self.max_retries = 3
        self.retry_delay = 0.5  # seconds
    
    async def synthesize_streaming(
        self,
        *,
        text: Optional[str],
        ssml: Optional[str],
        language_code: str,
        voice_name: Optional[str],
        gender: Optional[str],
        audio_encoding: str,
        speaking_rate: Optional[float] = None,
        pitch: Optional[float] = None,
        effects_profile_ids: Optional[List[str]] = None,
        voice_gender_choice: Optional[str] = None,
    ) -> AsyncGenerator[Tuple[str, bytes, str], None]:
        """
        Stream TTS audio chunks for the given text.
        
        Args:
            text: Plain text to synthesize (mutually exclusive with ssml)
            ssml: SSML input (mutually exclusive with text)
            language_code: Language code for TTS
            voice_name: Specific voice name to use
            gender: Gender preference for voice selection
            audio_encoding: Audio encoding format
            speaking_rate: Speaking rate multiplier
            pitch: Pitch adjustment
            effects_profile_ids: Audio effects profile IDs
            voice_gender_choice: Voice gender choice for preferred voices
            
        Yields:
            Tuple of (chunk_type, audio_bytes, metadata)
            chunk_type can be: "metadata", "audio", "error", "complete"
        """
        try:
            # Validate input
            if not text and not ssml:
                yield ("error", b"", "Either text or ssml must be provided")
                return
            
            if text and ssml:
                yield ("error", b"", "Provide only one of text or ssml")
                return
            
            # Get the text to process
            input_text = text or ssml or ""
            
            # For SSML, we can't chunk it easily, so process as single chunk
            if ssml:
                logger.info(f"Processing SSML input (length: {len(ssml)} chars)")
                audio_bytes, voice_used, lang_used = await self._synthesize_with_retry(
                    text=None,
                    ssml=ssml,
                    language_code=language_code,
                    voice_name=voice_name,
                    gender=gender,
                    audio_encoding=audio_encoding,
                    speaking_rate=speaking_rate,
                    pitch=pitch,
                    effects_profile_ids=effects_profile_ids,
                    voice_gender_choice=voice_gender_choice,
                )
                
                if audio_bytes:
                    yield ("metadata", b"", f"voice_used:{voice_used}|language_code:{lang_used}|total_chunks:1")
                    yield ("audio", audio_bytes, "")
                else:
                    yield ("error", b"", "Failed to synthesize SSML")
                
                yield ("complete", b"", "")
                return
            
            # Chunk the text into sentences
            sentences = self.text_chunker.split_into_sentences(input_text)
            
            if not sentences:
                yield ("error", b"", "No valid sentences found in text")
                return
            
            logger.info(f"Split text into {len(sentences)} sentences")
            
            # Get voice selection info for metadata
            _, voice_used, lang_used = self.tts_service.select_voice(
                language_code=language_code,
                preferred_gender=(gender or None),
                voice_name=voice_name,
                voice_gender_choice=voice_gender_choice,
            )
            
            # Send metadata
            metadata = f"voice_used:{voice_used}|language_code:{lang_used}|total_chunks:{len(sentences)}"
            yield ("metadata", b"", metadata)
            
            # Process each sentence
            successful_chunks = 0
            failed_chunks = 0
            
            for i, sentence in enumerate(sentences):
                logger.info(f"Processing sentence {i+1}/{len(sentences)}: {sentence[:50]}...")
                
                audio_bytes, _, _ = await self._synthesize_with_retry(
                    text=sentence,
                    ssml=None,
                    language_code=language_code,
                    voice_name=voice_name,
                    gender=gender,
                    audio_encoding=audio_encoding,
                    speaking_rate=speaking_rate,
                    pitch=pitch,
                    effects_profile_ids=effects_profile_ids,
                    voice_gender_choice=voice_gender_choice,
                )
                
                if audio_bytes:
                    yield ("audio", audio_bytes, f"chunk:{i+1}")
                    successful_chunks += 1
                else:
                    logger.error(f"Failed to synthesize sentence {i+1}: {sentence}")
                    failed_chunks += 1
                    # Continue with next chunk instead of stopping
            
            logger.info(f"Streaming complete: {successful_chunks} successful, {failed_chunks} failed chunks")
            yield ("complete", b"", f"successful_chunks:{successful_chunks}|failed_chunks:{failed_chunks}")
            
        except Exception as e:
            logger.exception("Error in streaming TTS")
            yield ("error", b"", f"Streaming error: {str(e)}")
    
    async def _synthesize_with_retry(
        self,
        *,
        text: Optional[str],
        ssml: Optional[str],
        language_code: str,
        voice_name: Optional[str],
        gender: Optional[str],
        audio_encoding: str,
        speaking_rate: Optional[float] = None,
        pitch: Optional[float] = None,
        effects_profile_ids: Optional[List[str]] = None,
        voice_gender_choice: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        """
        Synthesize audio with retry logic.
        
        Returns:
            Tuple of (audio_bytes, voice_used, language_code)
            Returns (b"", "", "") if all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Run the synchronous TTS call in a thread pool
                loop = asyncio.get_event_loop()
                
                # Create a wrapper function to call synthesize with keyword arguments
                def synthesize_wrapper():
                    return self.tts_service.synthesize(
                        text=text,
                        ssml=ssml,
                        language_code=language_code,
                        voice_name=voice_name,
                        gender=gender,
                        audio_encoding=audio_encoding,
                        speaking_rate=speaking_rate,
                        pitch=pitch,
                        effects_profile_ids=effects_profile_ids,
                        voice_gender_choice=voice_gender_choice,
                    )
                
                result = await loop.run_in_executor(None, synthesize_wrapper)
                
                audio_bytes, voice_used, lang_used = result
                return audio_bytes, voice_used, lang_used
                
            except Exception as e:
                last_error = e
                logger.warning(f"TTS synthesis attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    # Wait before retrying
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        
        logger.error(f"All {self.max_retries} attempts failed. Last error: {str(last_error)}")
        return b"", "", ""
