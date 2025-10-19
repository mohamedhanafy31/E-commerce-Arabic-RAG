import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .core.logging import configure_logging
from .middleware.error_handler import ErrorHandlerMiddleware
from .api.routes_asr import router as asr_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        description="Audio Speech Recognition API using Google Cloud Speech-to-Text",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Middleware
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.cors_origins == "*" else settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(asr_router)

    # Static files for audio (if needed)
    if os.path.exists(settings.audio_dir):
        app.mount("/audio", StaticFiles(directory=settings.audio_dir), name="audio")

    return app


app = create_app()
