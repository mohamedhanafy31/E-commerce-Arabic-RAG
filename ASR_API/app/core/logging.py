import logging
import sys
from .config import settings


def configure_logging():
    """Configure logging for the ASR API"""
    
    # Set log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("fastapi").setLevel(log_level)
    logging.getLogger("google").setLevel(logging.WARNING)  # Reduce Google Cloud logs
    
    # Create logger for ASR operations
    asr_logger = logging.getLogger("asr")
    asr_logger.setLevel(log_level)
    
    return asr_logger
