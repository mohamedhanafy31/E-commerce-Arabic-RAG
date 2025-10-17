from typing import List, Optional, Tuple
from google.cloud import texttospeech
from ..core.config import get_preferred_voice_list


GENDER_MAP = {
    None: texttospeech.SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED,
    "MALE": texttospeech.SsmlVoiceGender.MALE,
    "FEMALE": texttospeech.SsmlVoiceGender.FEMALE,
    "NEUTRAL": texttospeech.SsmlVoiceGender.NEUTRAL,
}

ENCODING_MAP = {
    "MP3": texttospeech.AudioEncoding.MP3,
    "LINEAR16": texttospeech.AudioEncoding.LINEAR16,
    "OGG_OPUS": texttospeech.AudioEncoding.OGG_OPUS,
}


class GoogleTTSService:
    def __init__(self) -> None:
        self.client = texttospeech.TextToSpeechClient()

    def list_voices(self, language_code: Optional[str] = None) -> List[texttospeech.Voice]:
        resp = self.client.list_voices(language_code=language_code or "")
        return list(resp.voices)

    def select_voice(
        self,
        language_code: str,
        preferred_gender: Optional[str] = None,
        voice_name: Optional[str] = None,
        voice_gender_choice: Optional[str] = None,
    ) -> Tuple[str, str, texttospeech.SsmlVoiceGender]:
        # Two-voice toggle (male first, female second) when requested via API
        if voice_gender_choice:
            names = get_preferred_voice_list()
            if names:
                idx = 1 if voice_gender_choice.lower() == "female" and len(names) > 1 else 0
                chosen = names[idx]
                voices = self.list_voices()
                for v in voices:
                    if v.name == chosen:
                        lc = v.language_codes[0] if v.language_codes else language_code
                        return lc, v.name, v.ssml_gender
        if voice_name:
            # Validate provided voice exists
            voices = self.list_voices()
            for v in voices:
                if v.name == voice_name:
                    lc = v.language_codes[0] if v.language_codes else language_code
                    return lc, v.name, v.ssml_gender
            # If not found, fall back to selection below

        # Try exact language match first
        voices = self.list_voices(language_code=language_code)
        if voices:
            gender_enum = GENDER_MAP.get((preferred_gender or "").upper(), GENDER_MAP[None])
            candidates = [v for v in voices if v.ssml_gender == gender_enum] if preferred_gender else voices
            v = candidates[0] if candidates else voices[0]
            return language_code, v.name, v.ssml_gender

        # Fallbacks: prefer ar-EG -> ar-XA -> any ar-*
        for fallback in ("ar-EG", "ar-XA"):
            voices = self.list_voices(language_code=fallback)
            if voices:
                v = voices[0]
                return fallback, v.name, v.ssml_gender

        # Any Arabic voice
        voices = [v for v in self.list_voices() if any(code.startswith("ar") for code in v.language_codes)]
        if voices:
            v = voices[0]
            lc = v.language_codes[0] if v.language_codes else language_code
            return lc, v.name, v.ssml_gender

        # As a last resort, return defaults
        return language_code, "", texttospeech.SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED

    def synthesize(
        self,
        *,
        text: Optional[str],
        ssml: Optional[str],
        language_code: str,
        voice_name: Optional[str],
        gender: Optional[str],
        audio_encoding: str,
        speaking_rate: Optional[float] = None,
        pitch: Optional[float] = None,
        effects_profile_ids: Optional[List[str]] = None,
        voice_gender_choice: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        input_cfg = texttospeech.SynthesisInput(text=text) if text else texttospeech.SynthesisInput(ssml=ssml or "")

        selected_language, selected_name, selected_gender = self.select_voice(
            language_code=language_code,
            preferred_gender=(gender or None),
            voice_name=voice_name,
            voice_gender_choice=voice_gender_choice,
        )

        voice_params = texttospeech.VoiceSelectionParams(
            language_code=selected_language,
            name=selected_name or None,
            ssml_gender=selected_gender,
        )

        audio_cfg = texttospeech.AudioConfig(
            audio_encoding=ENCODING_MAP.get(audio_encoding.upper(), texttospeech.AudioEncoding.MP3),
            speaking_rate=speaking_rate or 1.0,
            pitch=pitch or 0.0,
            effects_profile_id=effects_profile_ids or [],
        )

        response = self.client.synthesize_speech(
            input=input_cfg,
            voice=voice_params,
            audio_config=audio_cfg,
        )
        return response.audio_content, selected_name or "", selected_language


