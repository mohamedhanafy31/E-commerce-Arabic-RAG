import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from typing import List, Optional

from ..models.schemas import TTSRequest, TTSResponse, VoicesResponse
from ..services.gcp_tts import GoogleTTSService
from ..services.filename import build_audio_filename
from ..core.config import settings


router = APIRouter()


def get_tts_service() -> GoogleTTSService:
    return GoogleTTSService()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/voices", response_model=List[VoicesResponse])
def list_voices(
    language_code: Optional[str] = Query(None),
    name_contains: Optional[str] = Query(None),
    tts: GoogleTTSService = Depends(get_tts_service),
):
    voices = tts.list_voices(language_code=language_code)
    out: List[VoicesResponse] = []
    for v in voices:
        if name_contains and name_contains.lower() not in v.name.lower():
            continue
        out.append(VoicesResponse(name=v.name, language_codes=list(v.language_codes), gender=v.ssml_gender.name))
    return out


@router.get("/", response_class=HTMLResponse)
def index_page():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pages", "index.html"))
    return FileResponse(path)


@router.post("/tts", response_model=TTSResponse)
def synthesize(req: TTSRequest, tts: GoogleTTSService = Depends(get_tts_service)):
    text_payload = req.text or ""
    if len(text_payload) > 5000:
        raise HTTPException(status_code=413, detail="Text too long (max 5000 chars)")

    audio_content, voice_used, lang_used = tts.synthesize(
        text=req.text,
        ssml=req.ssml,
        language_code=req.language_code,
        voice_name=req.voice_name,
        gender=req.gender,
        audio_encoding=req.audio_encoding,
        speaking_rate=req.speaking_rate,
        pitch=req.pitch,
        effects_profile_ids=req.effects_profile_ids,
        voice_gender_choice=req.voice_gender_choice,
    )

    os.makedirs(settings.audio_dir, exist_ok=True)
    filename = build_audio_filename(voice_used or req.voice_name or "voice", req.text or req.ssml or "")
    file_path = os.path.join(settings.audio_dir, filename)
    with open(file_path, "wb") as f:
        f.write(audio_content)

    file_url = f"/audio/{filename}"
    return TTSResponse(file_url=file_url, voice_used=voice_used or (req.voice_name or ""), language_code=lang_used)


