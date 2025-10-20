#!/usr/bin/env python3
"""
Orchestrator Conversational System - Application Entry Point
"""

import uvicorn
from app.core.config import get_settings
from app.core.logging import configure_logging

def main():
    """Main application entry point"""
    # Configure logging
    configure_logging()
    
    # Get settings
    settings = get_settings()
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True
    )

if __name__ == "__main__":
    main()
