"""
RAG Client for Orchestrator
Handles HTTP communication with RAG system for text generation
"""

import asyncio
import httpx
import re
from typing import Optional, List, AsyncGenerator
from app.models.schemas import RAGQueryRequest, RAGQueryResponse
from app.core.config import settings
from app.core.logging import get_logger


class RAGClient:
    """HTTP client for RAG service"""
    
    def __init__(self):
        self.logger = get_logger("rag_client")
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url = settings.rag_service_url
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self):
        """Initialize HTTP client"""
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.rag_timeout_seconds),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
            self.logger.info(f"RAG client connected to: {self.base_url}")
    
    async def disconnect(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
            self.logger.info("RAG client disconnected")
    
    async def query(self, query: str, max_results: int = 5, 
                   conversation_history: Optional[str] = None) -> Optional[RAGQueryResponse]:
        """
        Send query to RAG system
        
        Args:
            query: User query
            max_results: Maximum number of results
            conversation_history: Conversation history context
            
        Returns:
            RAG response or None if failed
        """
        if not self.client:
            await self.connect()
        
        try:
            # Prepare request data
            request_data = RAGQueryRequest(
                query=query,
                max_results=max_results,
                include_history=bool(conversation_history)
            )
            
            # Add conversation history to query if available
            if conversation_history:
                enhanced_query = f"{conversation_history}\n\nالسؤال الحالي: {query}"
            else:
                enhanced_query = query
            
            request_data.query = enhanced_query
            
            self.logger.info(f"Sending RAG query: {query[:100]}...")
            
            # Send request
            response = await self.client.post(
                f"{self.base_url}/query",
                json=request_data.dict(),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                response_data = response.json()
                rag_response = RAGQueryResponse(**response_data)
                self.logger.info(f"RAG response received: {rag_response.answer[:100]}...")
                return rag_response
            else:
                self.logger.error(f"RAG request failed: {response.status_code} - {response.text}")
                return None
                
        except httpx.TimeoutException:
            self.logger.error("RAG request timeout")
            return None
        except httpx.RequestError as e:
            self.logger.error(f"RAG request error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected RAG error: {e}")
            return None
    
    async def stream_response_sentences(self, query: str, max_results: int = 5,
                                      conversation_history: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Stream RAG response sentence by sentence
        
        Args:
            query: User query
            max_results: Maximum number of results
            conversation_history: Conversation history context
            
        Yields:
            Individual sentences from the response
        """
        rag_response = await self.query(query, max_results, conversation_history)
        
        if not rag_response:
            self.logger.error("No RAG response received for streaming")
            return
        
        # Split response into sentences
        sentences = self._split_into_sentences(rag_response.answer)
        
        for sentence in sentences:
            if sentence.strip():
                self.logger.debug(f"Streaming sentence: {sentence[:50]}...")
                yield sentence.strip()
                # Small delay between sentences for natural flow
                await asyncio.sleep(0.1)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        if not text:
            return []
        
        # Arabic sentence endings
        sentence_endings = ['.', '!', '?', '؟', '!', '۔']
        
        # Split by sentence endings
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            
            if char in sentence_endings:
                sentence = current_sentence.strip()
                if sentence:
                    sentences.append(sentence)
                current_sentence = ""
        
        # Add remaining text as last sentence
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences
    
    async def health_check(self) -> bool:
        """
        Check RAG service health
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            if not self.client:
                await self.connect()
            
            response = await self.client.get(f"{self.base_url}/health")
            is_healthy = response.status_code == 200
            
            if is_healthy:
                self.logger.debug("RAG service health check passed")
            else:
                self.logger.warning(f"RAG service health check failed: {response.status_code}")
            
            return is_healthy
            
        except Exception as e:
            self.logger.error(f"RAG health check error: {e}")
            return False
    
    async def get_stats(self) -> Optional[dict]:
        """
        Get RAG service statistics
        
        Returns:
            Service stats or None if failed
        """
        try:
            if not self.client:
                await self.connect()
            
            response = await self.client.get(f"{self.base_url}/stats")
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get RAG stats: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting RAG stats: {e}")
            return None


class RAGClientManager:
    """Manages RAG client instances"""
    
    def __init__(self):
        self.logger = get_logger("rag_manager")
        self.client: Optional[RAGClient] = None
    
    async def get_client(self) -> RAGClient:
        """
        Get RAG client instance
        
        Returns:
            RAG client instance
        """
        if not self.client:
            self.client = RAGClient()
            await self.client.connect()
            self.logger.info("Created RAG client")
        
        return self.client
    
    async def cleanup(self):
        """Cleanup RAG client"""
        if self.client:
            await self.client.disconnect()
            self.client = None
            self.logger.info("Cleaned up RAG client")


# Global RAG client manager
rag_manager = RAGClientManager()


def get_rag_manager() -> RAGClientManager:
    """Get the global RAG client manager"""
    return rag_manager
