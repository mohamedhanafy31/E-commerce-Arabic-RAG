import re
from typing import List


class ArabicTextChunker:
    """
    Service for splitting Arabic text into sentences for streaming TTS.
    Handles Arabic punctuation marks and edge cases.
    """
    
    def __init__(self):
        # Arabic sentence ending punctuation marks
        self.sentence_endings = r'[.!؟]'
        # Pattern to split on sentence endings while keeping punctuation
        self.split_pattern = r'([.!؟]+)'
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split Arabic text into sentences based on punctuation marks.
        
        Args:
            text: Input text to split
            
        Returns:
            List of sentences with punctuation preserved
        """
        if not text or not text.strip():
            return []
        
        # Clean up the text
        text = text.strip()
        
        # Split on sentence endings while preserving punctuation
        parts = re.split(self.split_pattern, text)
        
        sentences = []
        current_sentence = ""
        
        for part in parts:
            if not part:
                continue
                
            # If this part is punctuation, add it to current sentence
            if re.match(self.sentence_endings, part):
                current_sentence += part
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""
            else:
                # Regular text - add to current sentence
                current_sentence += part
        
        # Add any remaining text as a sentence
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # Filter out empty sentences and clean up
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def get_chunk_info(self, text: str) -> dict:
        """
        Get information about text chunking without actually splitting.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with chunking information
        """
        sentences = self.split_into_sentences(text)
        
        return {
            "total_sentences": len(sentences),
            "total_characters": len(text),
            "average_sentence_length": sum(len(s) for s in sentences) / len(sentences) if sentences else 0,
            "sentences": sentences
        }
