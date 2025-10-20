"""
Comprehensive logging configuration for TTS API
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
from .config import settings


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
            
        # Add text processing info if available
        if hasattr(record, 'text_length'):
            log_entry["text_length"] = record.text_length
        if hasattr(record, 'language_code'):
            log_entry["language_code"] = record.language_code
        if hasattr(record, 'voice_name'):
            log_entry["voice_name"] = record.voice_name
        if hasattr(record, 'audio_encoding'):
            log_entry["audio_encoding"] = record.audio_encoding
            
        # Add audio generation info if available
        if hasattr(record, 'audio_file_size'):
            log_entry["audio_file_size"] = record.audio_file_size
        if hasattr(record, 'audio_duration'):
            log_entry["audio_duration"] = record.audio_duration
        if hasattr(record, 'chunk_count'):
            log_entry["chunk_count"] = record.chunk_count
            
        # Add Google Cloud info if available
        if hasattr(record, 'gcp_operation_id'):
            log_entry["gcp_operation_id"] = record.gcp_operation_id
        if hasattr(record, 'gcp_response_time'):
            log_entry["gcp_response_time"] = record.gcp_response_time
            
        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging():
    """Configure comprehensive logging for the TTS API"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Get log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "tts.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error-specific file handler
    error_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "tts_errors.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Text processing handler
    text_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "tts_text.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    text_handler.setLevel(logging.INFO)
    text_handler.setFormatter(file_formatter)
    
    # Audio generation handler
    audio_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "tts_audio.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    audio_handler.setLevel(logging.INFO)
    audio_handler.setFormatter(file_formatter)
    
    # Create specific loggers for different components
    loggers_config = {
        'tts': logging.INFO,
        'tts.text': logging.INFO,
        'tts.audio': logging.INFO,
        'tts.gcp': logging.INFO,
        'tts.websocket': logging.INFO,
        'tts.voice': logging.INFO,
        'httpx': logging.WARNING,
        'websockets': logging.WARNING,
        'uvicorn': logging.WARNING,
        'uvicorn.access': logging.WARNING,
        'uvicorn.error': logging.WARNING,
        'watchfiles': logging.WARNING,
        'fastapi': logging.INFO,
        'google.cloud': logging.WARNING,
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        
        # Add specific handlers based on logger type
        if 'text' in logger_name:
            logger.addHandler(text_handler)
        if 'audio' in logger_name:
            logger.addHandler(audio_handler)
    
    # Log startup information
    startup_logger = logging.getLogger('tts.startup')
    startup_logger.info("TTS API logging system initialized", extra={
        'operation': 'logging_init',
        'log_level': settings.log_level,
        'logs_directory': str(logs_dir.absolute()),
        'preferred_voices': settings.preferred_voice_names
    })


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(f'tts.{name}')


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


def log_text_processing(logger: logging.Logger, operation: str, text_length: int,
                       language_code: str, voice_name: str, **kwargs):
    """Log text processing operations"""
    logger.info(f"Text processing: {operation}", extra={
        'operation': operation,
        'text_length': text_length,
        'language_code': language_code,
        'voice_name': voice_name,
        **kwargs
    })


def log_audio_generation(logger: logging.Logger, operation: str, audio_file_size: int,
                        audio_duration: float, chunk_count: int, **kwargs):
    """Log audio generation operations"""
    logger.info(f"Audio generation: {operation}", extra={
        'operation': operation,
        'audio_file_size': audio_file_size,
        'audio_duration': audio_duration,
        'chunk_count': chunk_count,
        **kwargs
    })


def log_gcp_interaction(logger: logging.Logger, operation: str, operation_id: str,
                       response_time: float, **kwargs):
    """Log Google Cloud Platform interactions"""
    logger.info(f"GCP interaction: {operation}", extra={
        'operation': operation,
        'gcp_operation_id': operation_id,
        'gcp_response_time': response_time,
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
    
    def log_text_processing(self, operation: str, text_length: int, language_code: str,
                           voice_name: str, **kwargs) -> None:
        """Log text processing with session context"""
        log_text_processing(self.logger, operation, text_length, language_code, voice_name,
                           session_id=self.session_id, **kwargs)
    
    def log_audio_generation(self, operation: str, audio_file_size: int, audio_duration: float,
                            chunk_count: int, **kwargs) -> None:
        """Log audio generation with session context"""
        log_audio_generation(self.logger, operation, audio_file_size, audio_duration, chunk_count,
                            session_id=self.session_id, **kwargs)