## TTS API — Architecture & Flow

This document explains the architecture, key components, and end-to-end processing flow of the TTS API service.

### Overview

- **Goal**: Provide a REST API over Google Cloud Text-to-Speech (TTS), save generated audio locally, and serve it via static hosting.
- **Tech**: FastAPI, Google Cloud Text-to-Speech, Uvicorn, Docker.
- **Primary audience**: Developers operating or extending the service.

### Key Components

- **Web App** (`app/main.py`)
  - Creates the FastAPI app, configures logging and CORS, mounts static files at `/audio` from `AUDIO_DIR`, and includes TTS routes.
- **Routes** (`app/api/routes_tts.py`)
  - `GET /health`: service health probe.
  - `GET /voices`: lists available Google TTS voices (filterable by `language_code`, `name_contains`).
  - `POST /tts`: synthesizes speech from `text` or `ssml`, writes audio to disk, returns a `file_url`.
  - `WebSocket /ws/tts-stream`: streams TTS audio in real-time using sentence-based chunking.
  - `GET /`: serves `pages/index.html` for quick manual testing.
- **Models** (`app/models/schemas.py`)
  - `TTSRequest`: validates input; exactly one of `text` or `ssml` is required; supports `language_code`, `voice_name`, `gender`, `audio_encoding`, `speaking_rate`, `pitch`, `effects_profile_ids`, `voice_gender_choice`.
  - `StreamingTTSRequest`: same fields as `TTSRequest` for WebSocket streaming.
  - `StreamMetadata`, `StreamComplete`, `StreamError`: WebSocket message schemas.
  - `TTSResponse`: contains `file_url`, `voice_used`, `language_code`.
- **TTS Service** (`app/services/gcp_tts.py`)
  - Wraps `google.cloud.texttospeech` for listing voices and synthesizing audio.
  - Voice selection supports explicit `voice_name`, preferred `gender`, fallbacks for Arabic locales, and a two-voice toggle via `voice_gender_choice` using `PREFERRED_VOICE_NAMES`.
- **Streaming TTS Service** (`app/services/streaming_tts.py`)
  - Provides async streaming of TTS audio using sentence-based chunking.
  - Implements retry logic (3 attempts) for failed chunks.
  - Yields audio chunks as they are generated from Google TTS API.
- **Text Chunker** (`app/services/text_chunker.py`)
  - Splits Arabic text into sentences based on punctuation (., ؟, !).
  - Handles edge cases and filters empty chunks.
- **Filename Utility** (`app/services/filename.py`)
  - Builds sanitized, timestamped, hashed audio filenames.
- **Middleware** (`app/middleware/error_handler.py`)
  - Catches unhandled exceptions and returns `500` with a generic JSON error.
- **Configuration** (`app/core/config.py`)
  - Provides `settings` from environment variables and `get_preferred_voice_list()`.
- **Logging** (`app/core/logging.py`)
  - Sets up structured logging to stdout; respects `LOG_LEVEL`.
- **Runner** (`run.py`)
  - Starts Uvicorn, with reload enabled by default when `RELOAD=true`.

### Configuration (env)

- `GOOGLE_APPLICATION_CREDENTIALS`: absolute path to the service account JSON (required to call Google TTS).
- `AUDIO_DIR`: directory to write audio files (defaults to `/data/audio`). Mounted as `/audio` in the app.
- `PREFERRED_VOICE_NAMES`: comma-separated list used for the male/female toggle.
- `CORS_ORIGINS`, `LOG_LEVEL`. Note: `API_KEY`, `RATE_LIMIT_ENABLED` exist but are not wired yet.

### Data & Static Files

- Audio files are written to `AUDIO_DIR` and served as static files under `/audio/<filename>`.
- Filenames include UTC timestamp and a short hash of the text to avoid collisions and aid cacheability.

### Error Handling

- Global middleware catches unhandled exceptions and returns a generic 500.
- Input validation is enforced by `TTSRequest` (mutual exclusivity for `text` vs `ssml`, bounds for rate/pitch).

### End-to-End Flow (Request → Response)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant UI as Browser (index.html)
  participant API as FastAPI (routes)
  participant Svc as GoogleTTSService
  participant GCP as Google TTS API
  participant FS as File System (AUDIO_DIR)

  User->>UI: Enter text, choose gender/lang/encoding
  UI->>API: POST /tts { text, language_code, voice_gender_choice, audio_encoding }
  API->>API: Validate TTSRequest (text XOR ssml)
  API->>Svc: synthesize(...)
  Svc->>Svc: select_voice(language_code, voice_name, gender, voice_gender_choice)
  Svc->>GCP: synthesize_speech(input, voice, audio_config)
  GCP-->>Svc: audio bytes, voice metadata
  Svc-->>API: audio bytes, selected voice, language
  API->>FS: write file (timestamp + hash).mp3
  API-->>UI: { file_url, voice_used, language_code }
  UI->>API: GET /audio/<filename>
  API->>FS: Read file
  FS-->>API: MP3 bytes
  API-->>UI: MP3 stream
  UI-->>User: Play audio
```

### Streaming Flow (WebSocket)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant UI as Browser (index.html)
  participant WS as WebSocket /ws/tts-stream
  participant StreamSvc as StreamingTTSService
  participant Chunker as TextChunker
  participant TTS as GoogleTTSService
  participant GCP as Google TTS API

  User->>UI: Enter text, enable streaming mode
  UI->>WS: WebSocket connection
  WS-->>UI: Connection established
  UI->>WS: JSON request { text, language_code, voice_gender_choice, audio_encoding }
  WS->>WS: Validate StreamingTTSRequest
  WS->>StreamSvc: synthesize_streaming(...)
  StreamSvc->>Chunker: split_into_sentences(text)
  Chunker-->>StreamSvc: [sentence1, sentence2, sentence3]
  StreamSvc->>WS: metadata { voice_used, total_chunks: 3 }
  WS-->>UI: JSON metadata
  
  loop For each sentence
    StreamSvc->>TTS: synthesize(sentence)
    TTS->>GCP: synthesize_speech(sentence, voice, config)
    GCP-->>TTS: audio bytes
    TTS-->>StreamSvc: audio bytes
    StreamSvc->>WS: audio chunk (binary)
    WS-->>UI: Binary audio data
    UI->>UI: Buffer audio chunk
  end
  
  StreamSvc->>WS: complete { successful_chunks: 3, failed_chunks: 0 }
  WS-->>UI: JSON completion
  UI->>UI: Play buffered audio
  UI-->>User: Audio playback
```

### Component View

```mermaid
flowchart LR
  subgraph Client
    B[Browser UI (index.html)]
  end

  subgraph Server[FastAPI App]
    R[Routes /health /voices /tts /]
    M[ErrorHandlerMiddleware]
    L[Logging]
    C[Settings (env)]
    S[GoogleTTSService]
    F[Filename Utility]
  end

  G[(Google Cloud TTS)]
  D[(AUDIO_DIR Storage)]

  B -->|HTTP| R
  R --> M
  R --> S
  R --> F
  S --> C
  R --> C
  L -.-> R
  S -->|RPC| G
  R -->|write/read| D
  B -->|GET /audio| R
```

### API Summary

- `GET /health`: service liveness.
- `GET /voices?language_code=&name_contains=`: list voices with optional filters.
- `POST /tts`: synthesize audio; response includes `file_url`.
- `GET /`: minimal UI for manual testing.

### Deployment

- Local: `uvicorn app.main:app --reload` (ensure `GOOGLE_APPLICATION_CREDENTIALS` and `AUDIO_DIR` are set).
- Docker: build with provided `Dockerfile`, run with volumes for `/data/audio` and credentials mounted (see `README.md`).

### Extensibility Notes

- Add API key or JWT auth via dependency in `routes_tts.py`.
- Wire rate limiting (SlowAPI) if needed.
- Extend UI to call `/voices` and offer selectable voice list.
