"""
Arabic Embeddings Module
Handles text embedding generation using Arabic-aware models
"""

import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
import torch
from core.config import config


class ArabicEmbedder:
    """Arabic-aware text embedder using sentence transformers"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.embedding_model
        self.model = None
        self.is_loaded = False
        self.config = config
        
        # Handle CUDA compatibility issues
        cuda_available = False
        cuda_error = None
        
        try:
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                device_count = torch.cuda.device_count()
                print(f"✅ CUDA detected: {device_count} GPU(s)")
            else:
                print("⚠️  CUDA not available")
        except Exception as e:
            cuda_error = str(e)
            print(f"❌ CUDA Error: {cuda_error}")
            print("🔧 This is likely a hardware compatibility issue (Error 804)")
            print("💡 Solution: Install CPU-only PyTorch for compatibility")
        
        # Force GPU usage as per user rules, but handle compatibility issues
        if config.force_gpu and cuda_available:
            self.device = config.gpu_device
            print("🎯 GPU usage enabled as per user rules")
        elif config.force_gpu and not cuda_available:
            print("⚠️  GPU forced but CUDA not available - using CPU")
            self.device = "cpu"
        else:
            self.device = "cpu"
            print("🖥️  Using CPU for compatibility")
        
        print(f"🔧 Embedder initialized with device: {self.device}")
    
    def load(self):
        """Load the embedding model"""
        try:
            print(f"📥 Loading embedding model: {self.model_name}")
            print(f"🎯 Loading on device: {self.device}")
            
            # Set Hugging Face token if available
            if self.config.hf_token:
                import os
                os.environ['HF_TOKEN'] = self.config.hf_token
                print("🔑 Using Hugging Face token for authentication")
            
            # Try to load on GPU first
            try:
                self.model = SentenceTransformer(self.model_name, device=self.device)
                print("✅ Embedding model loaded successfully on", self.device)
            except Exception as gpu_error:
                print(f"⚠️  GPU loading failed: {gpu_error}")
                print("🔄 Falling back to CPU...")
                self.device = "cpu"
                self.model = SentenceTransformer(self.model_name, device=self.device)
                print(f"✅ Embedding model loaded on CPU fallback")
            
            self.is_loaded = True
            
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            raise e
    
    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        Encode texts to embeddings
        
        Args:
            texts: Single text or list of texts to encode
            batch_size: Batch size for processing
            
        Returns:
            Numpy array of embeddings
        """
        if not self.is_loaded:
            raise RuntimeError("Embedding model not loaded. Call load() first.")
        
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        try:
            # Encode texts
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 10,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalize for better similarity search
            )
            
            return embeddings
            
        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            raise e
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text to embedding"""
        return self.encode([text])[0]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        if not self.is_loaded:
            raise RuntimeError("Embedding model not loaded")
        
        # Get dimension by encoding a dummy text
        dummy_embedding = self.encode(["test"])
        return dummy_embedding.shape[1]
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Cosine similarity score (0-1)
        """
        embeddings = self.encode([text1, text2])
        emb1, emb2 = embeddings[0], embeddings[1]
        
        # Calculate cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)
    
    def find_most_similar(self, query: str, candidates: List[str], top_k: int = 5) -> List[tuple]:
        """
        Find most similar texts from candidates
        
        Args:
            query: Query text
            candidates: List of candidate texts
            top_k: Number of top results to return
            
        Returns:
            List of (text, similarity_score) tuples
        """
        if not candidates:
            return []
        
        # Encode query and candidates
        query_embedding = self.encode_single(query)
        candidate_embeddings = self.encode(candidates)
        
        # Calculate similarities
        similarities = []
        for i, candidate in enumerate(candidates):
            similarity = np.dot(query_embedding, candidate_embeddings[i])
            similarities.append((candidate, similarity))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        if not self.is_loaded:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "model_name": self.model_name,
            "device": self.device,
            "embedding_dimension": self.get_embedding_dimension(),
            "max_seq_length": getattr(self.model, 'max_seq_length', 'unknown')
        }
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess Arabic text for better embedding quality
        
        Args:
            text: Input Arabic text
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Normalize Arabic text
        text = self._normalize_arabic_text(text)
        
        return text.strip()
    
    def _normalize_arabic_text(self, text: str) -> str:
        """Normalize Arabic text for better embedding"""
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
