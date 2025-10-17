import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .core.logging import configure_logging
from .middleware.error_handler import ErrorHandlerMiddleware
from .api.routes_tts import router as tts_router


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title=settings.app_name)

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
    app.include_router(tts_router)

    # Static files for audio
    os.makedirs(settings.audio_dir, exist_ok=True)
    app.mount("/audio", StaticFiles(directory=settings.audio_dir), name="audio")

    return app


app = create_app()


