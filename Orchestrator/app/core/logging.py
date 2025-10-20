"""
Comprehensive logging configuration for Orchestrator
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
            
        # Add request/response data if available
        if hasattr(record, 'request_data'):
            log_entry["request_data"] = record.request_data
        if hasattr(record, 'response_data'):
            log_entry["response_data"] = record.response_data
            
        # Add external service info if available
        if hasattr(record, 'service_name'):
            log_entry["service_name"] = record.service_name
        if hasattr(record, 'service_url'):
            log_entry["service_url"] = record.service_url
            
        return json.dumps(log_entry, ensure_ascii=False)


class ColorFormatter(logging.Formatter):
    """Human-readable colorized formatter for console output only"""
    # ANSI colors
    COLORS = {
        'RESET': "\x1b[0m",
        'DIM': "\x1b[2m",
        'BOLD': "\x1b[1m",
        'LEVEL': {
            'DEBUG': "\x1b[38;5;244m",      # gray
            'INFO': "\x1b[38;5;39m",        # blue
            'WARNING': "\x1b[38;5;214m",    # orange
            'ERROR': "\x1b[38;5;196m",      # red
            'CRITICAL': "\x1b[48;5;196;97m"  # red bg + white fg
        },
        'NAME': "\x1b[38;5;45m",            # cyan
        'TIME': "\x1b[38;5;244m",            # gray
        'TAG': "\x1b[38;5;141m"              # magenta
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS['LEVEL'].get(record.levelname, '')
        reset = self.COLORS['RESET']
        time_c = self.COLORS['TIME']
        name_c = self.COLORS['NAME']
        tag_c = self.COLORS['TAG']

        # Base fields
        asctime = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        level = f"{color}{record.levelname:<8}{reset}"
        logger_name = f"{name_c}{record.name:<20}{reset}"
        tag = f"{tag_c}@Orchestrator{reset}"

        # Optional context
        context_parts = []
        if hasattr(record, 'operation'):
            context_parts.append(f"op={record.operation}")
        if hasattr(record, 'session_id'):
            context_parts.append(f"sid={record.session_id}")
        if hasattr(record, 'duration_ms'):
            context_parts.append(f"t={getattr(record, 'duration_ms', 0):.2f}ms")
        context = f" [{', '.join(context_parts)}]" if context_parts else ""

        message = record.getMessage()
        return f"{time_c}{asctime}{reset} | {level} | {logger_name} | {tag} | {message}{context}"

class PerformanceFilter(logging.Filter):
    """Filter to add performance metrics to log records"""
    
    def filter(self, record):
        # Add request start time for performance tracking
        if not hasattr(record, 'request_start_time'):
            record.request_start_time = time.time()
        return True


def configure_logging():
    """Configure comprehensive logging for the Orchestrator"""
    
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
    
    # Console handler with colored output (distinct for Orchestrator)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = ColorFormatter()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "orchestrator.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error-specific file handler
    error_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "errors.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Performance metrics handler
    perf_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "performance.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.addFilter(PerformanceFilter())
    perf_handler.setFormatter(file_formatter)
    root_logger.addHandler(perf_handler)
    
    # WebSocket-specific handler
    ws_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "websocket.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    ws_handler.setLevel(logging.INFO)
    ws_handler.setFormatter(file_formatter)
    
    # Create specific loggers for different components
    loggers_config = {
        'orchestrator': logging.INFO,
        'orchestrator.websocket': logging.INFO,
        'orchestrator.asr_client': logging.INFO,
        'orchestrator.rag_client': logging.INFO,
        'orchestrator.tts_client': logging.INFO,
        'orchestrator.session_manager': logging.INFO,
        'httpx': logging.WARNING,
        'websockets': logging.WARNING,
        'uvicorn': logging.WARNING,
        'uvicorn.access': logging.WARNING,
        'uvicorn.error': logging.WARNING,
        'watchfiles': logging.WARNING,
        'fastapi': logging.INFO,
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        
        # Add WebSocket handler for WebSocket-related loggers
        if 'websocket' in logger_name or 'client' in logger_name:
            logger.addHandler(ws_handler)
    
    # Log startup information
    startup_logger = logging.getLogger('orchestrator.startup')
    startup_logger.info("Orchestrator logging system initialized", extra={
        'operation': 'logging_init',
        'log_level': settings.log_level,
        'logs_directory': str(logs_dir.absolute())
    })


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(f'orchestrator.{name}')


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


def log_external_service(logger: logging.Logger, service_name: str, operation: str, 
                        service_url: str, **kwargs):
    """Log external service interactions"""
    logger.info(f"External service {service_name}: {operation}", extra={
        'operation': operation,
        'service_name': service_name,
        'service_url': service_url,
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