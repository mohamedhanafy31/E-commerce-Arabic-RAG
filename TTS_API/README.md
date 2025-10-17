# TTS API (FastAPI + Google Cloud TTS)

## Run locally

```bash
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/tts-key.json
export AUDIO_DIR=$(pwd)/data/audio
uvicorn app.main:app --reload
```

- Health: `GET /health`
- Voices: `GET /voices?language_code=ar-XA`
- TTS: `POST /tts`
- Streaming TTS: `WebSocket /ws/tts-stream`

Request example:

```json
{
  "text": "مرحبا بك في خدمة تحويل النص إلى كلام.",
  "language_code": "ar-XA",
  "voice_name": "ar-XA-Chirp3-HD-Achernar",
  "audio_encoding": "MP3"
}
```

## Docker

```bash
docker build -t tts-api .
mkdir -p /var/tts/audio /var/tts/keys
cp /path/to/tts-key.json /var/tts/keys/tts-key.json

docker run -d --name tts-api \
  -p 8000:8000 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/tts-key.json \
  -e AUDIO_DIR=/data/audio \
  -v /var/tts/audio:/data/audio \
  -v /var/tts/keys:/secrets \
  tts-api
```

Audio files available under `/audio/`.

## WebSocket Streaming

The service supports real-time audio streaming via WebSocket for faster response times.

### WebSocket Endpoint
- **URL**: `ws://localhost:8000/ws/tts-stream` (or `wss://` for HTTPS)
- **Protocol**: WebSocket with JSON and binary messages

### Message Protocol

1. **Client Request** (JSON):
```json
{
  "text": "مرحبا بك في خدمة تحويل النص إلى كلام.",
  "language_code": "ar-XA",
  "voice_gender_choice": "male",
  "audio_encoding": "MP3"
}
```

2. **Server Metadata** (JSON):
```json
{
  "type": "metadata",
  "voice_used": "ar-XA-Chirp3-HD-Algenib",
  "language_code": "ar-XA",
  "total_chunks": 3
}
```

3. **Server Audio Chunks** (Binary): MP3/OGG/WAV audio data

4. **Server Completion** (JSON):
```json
{
  "type": "complete",
  "successful_chunks": 3,
  "failed_chunks": 0
}
```

5. **Server Error** (JSON):
```json
{
  "type": "error",
  "detail": "Error message"
}
```

### Features
- **Sentence-based chunking**: Text is split into sentences for faster streaming
- **Retry logic**: Failed chunks are retried up to 3 times
- **Real-time progress**: Track streaming progress in the web interface
- **Error handling**: Graceful handling of connection issues and TTS failures
