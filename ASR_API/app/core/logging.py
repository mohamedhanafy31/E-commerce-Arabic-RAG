"""
Comprehensive logging configuration for ASR API
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
            
        # Add audio processing info if available
        if hasattr(record, 'audio_file_size'):
            log_entry["audio_file_size"] = record.audio_file_size
        if hasattr(record, 'audio_duration'):
            log_entry["audio_duration"] = record.audio_duration
        if hasattr(record, 'audio_format'):
            log_entry["audio_format"] = record.audio_format
        if hasattr(record, 'language_code'):
            log_entry["language_code"] = record.language_code
            
        # Add transcription info if available
        if hasattr(record, 'transcript_length'):
            log_entry["transcript_length"] = record.transcript_length
        if hasattr(record, 'confidence_score'):
            log_entry["confidence_score"] = record.confidence_score
            
        # Add Google Cloud info if available
        if hasattr(record, 'gcp_operation_id'):
            log_entry["gcp_operation_id"] = record.gcp_operation_id
        if hasattr(record, 'gcp_response_time'):
            log_entry["gcp_response_time"] = record.gcp_response_time
            
        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging():
    """Configure comprehensive logging for the ASR API"""
    
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
        logs_dir / "asr.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error-specific file handler
    error_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "asr_errors.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Audio processing handler
    audio_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "asr_audio.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    audio_handler.setLevel(logging.INFO)
    audio_handler.setFormatter(file_formatter)
    
    # Transcription handler
    transcription_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "asr_transcription.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    transcription_handler.setLevel(logging.INFO)
    transcription_handler.setFormatter(file_formatter)
    
    # Create specific loggers for different components
    loggers_config = {
        'asr': logging.INFO,
        'asr.audio': logging.INFO,
        'asr.transcription': logging.INFO,
        'asr.gcp': logging.INFO,
        'asr.websocket': logging.INFO,
        'asr.preprocessing': logging.INFO,
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
        if 'audio' in logger_name:
            logger.addHandler(audio_handler)
        if 'transcription' in logger_name:
            logger.addHandler(transcription_handler)
    
    # Log startup information
    startup_logger = logging.getLogger('asr.startup')
    startup_logger.info("ASR API logging system initialized", extra={
        'operation': 'logging_init',
        'log_level': settings.log_level,
        'logs_directory': str(logs_dir.absolute()),
        'default_language_code': settings.default_language_code,
        'max_file_size_mb': settings.max_file_size_mb
    })


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(f'asr.{name}')


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


def log_audio_processing(logger: logging.Logger, operation: str, file_size: int, 
                        duration: float, format: str, **kwargs):
    """Log audio processing operations"""
    logger.info(f"Audio processing: {operation}", extra={
        'operation': operation,
        'audio_file_size': file_size,
        'audio_duration': duration,
        'audio_format': format,
        **kwargs
    })


def log_transcription(logger: logging.Logger, operation: str, transcript_length: int,
                     confidence: float, language_code: str, **kwargs):
    """Log transcription operations"""
    logger.info(f"Transcription: {operation}", extra={
        'operation': operation,
        'transcript_length': transcript_length,
        'confidence_score': confidence,
        'language_code': language_code,
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
    
    def log_audio_processing(self, operation: str, file_size: int, duration: float, 
                            format: str, **kwargs) -> None:
        """Log audio processing with session context"""
        log_audio_processing(self.logger, operation, file_size, duration, format, 
                           session_id=self.session_id, **kwargs)
    
    def log_transcription(self, operation: str, transcript_length: int, confidence: float,
                         language_code: str, **kwargs) -> None:
        """Log transcription with session context"""
        log_transcription(self.logger, operation, transcript_length, confidence, language_code,
                         session_id=self.session_id, **kwargs)