"""
Arabic Text Chunking Module
Handles text segmentation for Arabic content with proper sentence boundaries
"""

import re
from typing import List
from core.config import config


class ArabicTextChunker:
    """Arabic-aware text chunker that chunks by sentences"""
    
    def __init__(self, sentences_per_chunk: int = None, sentence_overlap: int = None):
        self.sentences_per_chunk = sentences_per_chunk or 7
        self.sentence_overlap = sentence_overlap or 5
        
        # Arabic sentence endings
        self.sentence_endings = [
            '.', '!', '?', '؟', '!',  # Basic punctuation
            '۔', '۔',  # Urdu/Arabic periods
            '\n\n',  # Paragraph breaks
        ]
        
        # Arabic paragraph markers
        self.paragraph_markers = [
            '\n\n',
            '\n\r\n',
            '\r\n\r\n'
        ]
    
    def chunk(self, text: str) -> List[str]:
        """
        Chunk Arabic text into overlapping sentence-based segments
        
        Args:
            text: Input Arabic text
            
        Returns:
            List of text chunks (each containing 7 sentences with 5 sentence overlap)
        """
        if not text or not text.strip():
            return []
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Split text into sentences
        sentences = self._split_into_sentences(text)
        
        if not sentences:
            return []
        
        # Create chunks with sentence overlap
        chunks = self._create_sentence_chunks(sentences)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize Arabic text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize Arabic characters
        text = self._normalize_arabic(text)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into individual sentences
        
        Args:
            text: Input Arabic text
            
        Returns:
            List of sentences
        """
        sentences = []
        current_sentence = ""
        
        i = 0
        while i < len(text):
            char = text[i]
            current_sentence += char
            
            # Check for sentence endings
            if char in self.sentence_endings:
                # Look ahead to see if it's really a sentence end
                if self._is_sentence_end(text, i):
                    sentence = current_sentence.strip()
                    if sentence:
                        sentences.append(sentence)
                    current_sentence = ""
            
            i += 1
        
        # Add remaining text as last sentence
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences
    
    def _create_sentence_chunks(self, sentences: List[str]) -> List[str]:
        """
        Create overlapping chunks from sentences
        
        Args:
            sentences: List of sentences
            
        Returns:
            List of chunks with sentence overlap
        """
        if len(sentences) <= self.sentences_per_chunk:
            # If we have fewer sentences than chunk size, return as single chunk
            return [" ".join(sentences)]
        
        chunks = []
        start_idx = 0
        
        while start_idx < len(sentences):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.sentences_per_chunk, len(sentences))
            
            # Get sentences for this chunk
            chunk_sentences = sentences[start_idx:end_idx]
            chunk_text = " ".join(chunk_sentences)
            chunks.append(chunk_text)
            
            # Move to next chunk with overlap
            if end_idx >= len(sentences):
                break
            
            # Calculate next start index with overlap
            next_start = end_idx - self.sentence_overlap
            if next_start <= start_idx:
                # Ensure we make progress
                next_start = start_idx + 1
            
            start_idx = next_start
        
        return chunks
    
    def _normalize_arabic(self, text: str) -> str:
        """Normalize Arabic text for better processing"""
        # Normalize Arabic numerals
        arabic_numerals = '٠١٢٣٤٥٦٧٨٩'
        english_numerals = '0123456789'
        
        for ar, en in zip(arabic_numerals, english_numerals):
            text = text.replace(ar, en)
        
        # Normalize common Arabic letter variants
        replacements = {
            'أ': 'ا', 'إ': 'ا', 'آ': 'ا',  # Alif variants
            'ى': 'ي',  # Ya variants
            'ة': 'ه',  # Ta marbuta
            'ؤ': 'و',  # Waw with hamza
            'ئ': 'ي',  # Ya with hamza
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _is_sentence_end(self, text: str, pos: int) -> bool:
        """Check if position is really a sentence end"""
        if pos >= len(text) - 1:
            return True
        
        # Check if next character is whitespace or end of text
        next_char = text[pos + 1]
        if next_char.isspace() or pos + 1 == len(text) - 1:
            return True
        
        # Check for Arabic-specific patterns
        if next_char in ['،', '؛', ':', '؛']:  # Arabic punctuation
            return True
        
        return False
    
    def get_chunk_stats(self, chunks: List[str]) -> dict:
        """Get statistics about chunks"""
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_sentences_per_chunk": 0,
                "total_sentences": 0,
                "sentences_per_chunk": self.sentences_per_chunk,
                "sentence_overlap": self.sentence_overlap
            }
        
        # Count sentences in each chunk (approximate)
        total_sentences = 0
        for chunk in chunks:
            # Count sentence endings in chunk
            sentence_count = sum(1 for char in chunk if char in self.sentence_endings)
            total_sentences += sentence_count
        
        return {
            "total_chunks": len(chunks),
            "avg_sentences_per_chunk": total_sentences / len(chunks) if chunks else 0,
            "total_sentences": total_sentences,
            "sentences_per_chunk": self.sentences_per_chunk,
            "sentence_overlap": self.sentence_overlap
        }
