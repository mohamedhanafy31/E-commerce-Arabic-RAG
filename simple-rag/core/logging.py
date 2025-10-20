"""
Comprehensive logging configuration for RAG System
Monitors all operations, errors, and performance metrics
"""

import logging
import logging.handlers
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add session_id if available
        if hasattr(record, 'session_id'):
            log_entry["session_id"] = record.session_id
            
        # Add operation context if available
        if hasattr(record, 'operation'):
            log_entry["operation"] = record.operation
            
        # Add performance metrics if available
        if hasattr(record, 'duration_ms'):
            log_entry["duration_ms"] = record.duration_ms
            
        # Add error details if available
        if hasattr(record, 'error_code'):
            log_entry["error_code"] = record.error_code
        if hasattr(record, 'error_details'):
            log_entry["error_details"] = record.error_details
            
        # Add file processing info if available
        if hasattr(record, 'file_name'):
            log_entry["file_name"] = record.file_name
        if hasattr(record, 'file_size'):
            log_entry["file_size"] = record.file_size
        if hasattr(record, 'file_type'):
            log_entry["file_type"] = record.file_type
            
        # Add chunking info if available
        if hasattr(record, 'chunk_count'):
            log_entry["chunk_count"] = record.chunk_count
        if hasattr(record, 'chunk_size'):
            log_entry["chunk_size"] = record.chunk_size
            
        # Add embedding info if available
        if hasattr(record, 'embedding_model'):
            log_entry["embedding_model"] = record.embedding_model
        if hasattr(record, 'embedding_dimension'):
            log_entry["embedding_dimension"] = record.embedding_dimension
            
        # Add vector store info if available
        if hasattr(record, 'vector_count'):
            log_entry["vector_count"] = record.vector_count
        if hasattr(record, 'search_results'):
            log_entry["search_results"] = record.search_results
            
        # Add generation info if available
        if hasattr(record, 'query_length'):
            log_entry["query_length"] = record.query_length
        if hasattr(record, 'response_length'):
            log_entry["response_length"] = record.response_length
        if hasattr(record, 'model_used'):
            log_entry["model_used"] = record.model_used
            
        # Add Gemini API info if available
        if hasattr(record, 'gemini_request_id'):
            log_entry["gemini_request_id"] = record.gemini_request_id
        if hasattr(record, 'gemini_response_time'):
            log_entry["gemini_response_time"] = record.gemini_response_time
            
        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging():
    """Configure comprehensive logging for the RAG System"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Get log level from environment or default to INFO
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "rag.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(numeric_level)
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error-specific file handler
    error_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "rag_errors.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # File processing handler
    file_processing_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "rag_file_processing.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    file_processing_handler.setLevel(logging.INFO)
    file_processing_handler.setFormatter(file_formatter)
    
    # Embedding handler
    embedding_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "rag_embedding.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    embedding_handler.setLevel(logging.INFO)
    embedding_handler.setFormatter(file_formatter)
    
    # Query processing handler
    query_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "rag_query.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    query_handler.setLevel(logging.INFO)
    query_handler.setFormatter(file_formatter)
    
    # Create specific loggers for different components
    loggers_config = {
        'rag': logging.INFO,
        'rag.file_processing': logging.INFO,
        'rag.chunking': logging.INFO,
        'rag.embedding': logging.INFO,
        'rag.vector_store': logging.INFO,
        'rag.generation': logging.INFO,
        'rag.query': logging.INFO,
        'rag.gemini': logging.INFO,
        'httpx': logging.WARNING,
        'uvicorn': logging.WARNING,
        'uvicorn.access': logging.WARNING,
        'uvicorn.error': logging.WARNING,
        'watchfiles': logging.WARNING,
        'fastapi': logging.INFO,
        'sentence_transformers': logging.WARNING,
        'transformers': logging.WARNING,
        'torch': logging.WARNING,
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        
        # Add specific handlers based on logger type
        if 'file_processing' in logger_name or 'chunking' in logger_name:
            logger.addHandler(file_processing_handler)
        if 'embedding' in logger_name:
            logger.addHandler(embedding_handler)
        if 'query' in logger_name or 'generation' in logger_name:
            logger.addHandler(query_handler)
    
    # Log startup information
    startup_logger = logging.getLogger('rag.startup')
    startup_logger.info("RAG System logging initialized", extra={
        'operation': 'logging_init',
        'log_level': log_level,
        'logs_directory': str(logs_dir.absolute())
    })


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(f'rag.{name}')


def log_operation(logger: logging.Logger, operation: str, **kwargs):
    """Log an operation with structured data"""
    logger.info(f"Operation: {operation}", extra={
        'operation': operation,
        **kwargs
    })


def log_error(logger: logging.Logger, error: Exception, operation: str, **kwargs):
    """Log an error with structured data"""
    logger.error(f"Error in {operation}: {str(error)}", extra={
        'operation': operation,
        'error_code': type(error).__name__,
        'error_details': str(error),
        **kwargs
    }, exc_info=True)


def log_performance(logger: logging.Logger, operation: str, duration_ms: float, **kwargs):
    """Log performance metrics"""
    logger.info(f"Performance: {operation} completed in {duration_ms:.2f}ms", extra={
        'operation': operation,
        'duration_ms': duration_ms,
        **kwargs
    })


def log_file_processing(logger: logging.Logger, operation: str, file_name: str,
                       file_size: int, file_type: str, **kwargs):
    """Log file processing operations"""
    logger.info(f"File processing: {operation}", extra={
        'operation': operation,
        'file_name': file_name,
        'file_size': file_size,
        'file_type': file_type,
        **kwargs
    })


def log_chunking(logger: logging.Logger, operation: str, chunk_count: int,
                chunk_size: int, **kwargs):
    """Log chunking operations"""
    logger.info(f"Chunking: {operation}", extra={
        'operation': operation,
        'chunk_count': chunk_count,
        'chunk_size': chunk_size,
        **kwargs
    })


def log_embedding(logger: logging.Logger, operation: str, embedding_model: str,
                 embedding_dimension: int, **kwargs):
    """Log embedding operations"""
    logger.info(f"Embedding: {operation}", extra={
        'operation': operation,
        'embedding_model': embedding_model,
        'embedding_dimension': embedding_dimension,
        **kwargs
    })


def log_vector_store(logger: logging.Logger, operation: str, vector_count: int,
                    search_results: int, **kwargs):
    """Log vector store operations"""
    logger.info(f"Vector store: {operation}", extra={
        'operation': operation,
        'vector_count': vector_count,
        'search_results': search_results,
        **kwargs
    })


def log_query_processing(logger: logging.Logger, operation: str, query_length: int,
                        response_length: int, model_used: str, **kwargs):
    """Log query processing operations"""
    logger.info(f"Query processing: {operation}", extra={
        'operation': operation,
        'query_length': query_length,
        'response_length': response_length,
        'model_used': model_used,
        **kwargs
    })


def log_gemini_interaction(logger: logging.Logger, operation: str, request_id: str,
                         response_time: float, **kwargs):
    """Log Gemini API interactions"""
    logger.info(f"Gemini interaction: {operation}", extra={
        'operation': operation,
        'gemini_request_id': request_id,
        'gemini_response_time': response_time,
        **kwargs
    })


class SessionLogger:
    """Logger that includes session ID in all messages"""
    
    def __init__(self, session_id: str, logger_name: str = "session"):
        self.session_id = session_id
        self.logger = get_logger(logger_name)
    
    def _format_message(self, message: str) -> str:
        """Format message with session ID"""
        return f"[{self.session_id}] {message}"
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(self._format_message(message), extra={
            'session_id': self.session_id,
            **kwargs
        })
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.logger.info(self._format_message(message), extra={
            'session_id': self.session_id,
            **kwargs
        })
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(self._format_message(message), extra={
            'session_id': self.session_id,
            **kwargs
        })
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message"""
        self.logger.error(self._format_message(message), extra={
            'session_id': self.session_id,
            **kwargs
        })
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception message"""
        self.logger.exception(self._format_message(message), extra={
            'session_id': self.session_id,
            **kwargs
        })
    
    def log_operation(self, operation: str, **kwargs) -> None:
        """Log an operation with session context"""
        log_operation(self.logger, operation, session_id=self.session_id, **kwargs)
    
    def log_error(self, error: Exception, operation: str, **kwargs) -> None:
        """Log an error with session context"""
        log_error(self.logger, error, operation, session_id=self.session_id, **kwargs)
    
    def log_performance(self, operation: str, duration_ms: float, **kwargs) -> None:
        """Log performance metrics with session context"""
        log_performance(self.logger, operation, duration_ms, session_id=self.session_id, **kwargs)
