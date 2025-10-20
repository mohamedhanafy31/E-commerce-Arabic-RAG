"""
Session Manager for Orchestrator
Manages conversation history and session state
"""

import asyncio
import uuid
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from app.models.schemas import SessionData, ConversationTurn, ConversationState, AudioConfig
from app.core.config import settings
from app.core.logging import get_logger


class SessionManager:
    """Manages conversation sessions and history"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        self._lock = asyncio.Lock()
        self.logger = get_logger("session_manager")
        
        # Don't start cleanup task during initialization
        # It will be started when the first session is created
        self._cleanup_task = None
    
    async def create_session(self, audio_config: Optional[AudioConfig] = None) -> str:
        """
        Create a new conversation session
        
        Args:
            audio_config: Audio configuration for the session
            
        Returns:
            Session ID
        """
        async with self._lock:
            # Start cleanup task if not already running
            if self._cleanup_task is None:
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
            
            session_id = str(uuid.uuid4())
            config = audio_config or AudioConfig()
            
            session_data = SessionData(
                session_id=session_id,
                audio_config=config,
                current_state=ConversationState.IDLE
            )
            
            self.sessions[session_id] = session_data
            self.logger.info(f"Created new session: {session_id}")
            
            return session_id
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session data by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        async with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.last_activity = datetime.utcnow()
            return session
    
    async def update_session_state(self, session_id: str, state: ConversationState) -> bool:
        """
        Update session state
        
        Args:
            session_id: Session identifier
            state: New conversation state
            
        Returns:
            True if updated successfully, False otherwise
        """
        async with self._lock:
            session = self.sessions.get(session_id)
            if session:
                previous_state = session.current_state
                session.current_state = state
                session.last_activity = datetime.utcnow()
                self.logger.debug(f"Session {session_id} state: {previous_state} -> {state}")
                return True
            return False
    
    async def add_conversation_turn(self, session_id: str, user_query: str, 
                                  assistant_response: str, processing_time_ms: Optional[int] = None) -> bool:
        """
        Add a conversation turn to session history
        
        Args:
            session_id: Session identifier
            user_query: User's query
            assistant_response: Assistant's response
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            True if added successfully, False otherwise
        """
        async with self._lock:
            session = self.sessions.get(session_id)
            if session:
                turn = ConversationTurn(
                    user_query=user_query,
                    assistant_response=assistant_response,
                    processing_time_ms=processing_time_ms
                )
                
                session.conversation_history.append(turn)
                session.last_activity = datetime.utcnow()
                
                # Trim history if it exceeds max length
                if len(session.conversation_history) > settings.max_session_history:
                    session.conversation_history = session.conversation_history[-settings.max_session_history:]
                
                self.logger.debug(f"Added conversation turn to session {session_id}")
                return True
            return False
    
    async def get_conversation_history(self, session_id: str) -> List[ConversationTurn]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation turns
        """
        async with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.last_activity = datetime.utcnow()
                return session.conversation_history.copy()
            return []
    
    async def get_context_for_rag(self, session_id: str) -> str:
        """
        Get formatted context for RAG system
        
        Args:
            session_id: Session identifier
            
        Returns:
            Formatted context string
        """
        history = await self.get_conversation_history(session_id)
        
        if not history:
            return ""
        
        context_parts = []
        for i, turn in enumerate(history):
            context_parts.append(f"السؤال {i+1}: {turn.user_query}")
            context_parts.append(f"الإجابة {i+1}: {turn.assistant_response}")
        
        return "\n\n".join(context_parts)
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        async with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                self.logger.info(f"Deleted session: {session_id}")
                return True
            return False
    
    async def get_active_sessions_count(self) -> int:
        """
        Get count of active sessions
        
        Returns:
            Number of active sessions
        """
        async with self._lock:
            return len(self.sessions)
    
    async def _cleanup_expired_sessions(self):
        """Cleanup expired sessions periodically"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                async with self._lock:
                    now = datetime.utcnow()
                    expired_sessions = []
                    
                    for session_id, session in self.sessions.items():
                        if now - session.last_activity > timedelta(seconds=settings.session_timeout_seconds):
                            expired_sessions.append(session_id)
                    
                    for session_id in expired_sessions:
                        del self.sessions[session_id]
                        self.logger.info(f"Cleaned up expired session: {session_id}")
                    
                    if expired_sessions:
                        self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                        
            except Exception as e:
                self.logger.error(f"Error in session cleanup: {e}")
    
    async def get_session_stats(self) -> Dict[str, any]:
        """
        Get session statistics
        
        Returns:
            Dictionary with session statistics
        """
        async with self._lock:
            total_sessions = len(self.sessions)
            total_turns = sum(len(session.conversation_history) for session in self.sessions.values())
            
            state_counts = {}
            for session in self.sessions.values():
                state = session.current_state
                state_counts[state] = state_counts.get(state, 0) + 1
            
            return {
                "total_sessions": total_sessions,
                "total_conversation_turns": total_turns,
                "state_distribution": state_counts,
                "max_sessions": settings.max_concurrent_sessions,
                "session_timeout_seconds": settings.session_timeout_seconds
            }


# Global session manager instance
session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    return session_manager
