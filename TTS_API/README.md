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
