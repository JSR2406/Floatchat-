# Voice Router
# Speech-to-text and text-to-speech endpoints

import logging
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.schemas.chat import (
    VoiceTranscribeRequest, VoiceTranscribeResponse,
    VoiceSynthesizeRequest, VoiceSynthesizeResponse,
)
from app.services.voice_providers import (
    STTProvider, TTSProvider, TranslationProvider,
    SarvamSTTProvider, SarvamTTSProvider, ElevenLabsTTSProvider,
    GoogleTranslationProvider, VoiceProviderFactory, get_voice_factory,
    COASTAL_LANGUAGES, COASTAL_LANGUAGE_CODES, COASTAL_LANGUAGE_NAMES,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


# Global provider instances
_voice_factory: VoiceProviderFactory = None


async def get_voice_factory_instance() -> VoiceProviderFactory:
    global _voice_factory
    if _voice_factory is None:
        _voice_factory = await get_voice_factory()
    return _voice_factory


async def get_stt_provider() -> STTProvider:
    factory = await get_voice_factory_instance()
    return factory.get_stt("sarvam")


async def get_tts_provider() -> TTSProvider:
    factory = await get_voice_factory_instance()
    return factory.get_tts("elevenlabs")


async def get_translation_provider() -> TranslationProvider:
    factory = await get_voice_factory_instance()
    return factory.get_translation("google")


@router.post("/transcribe", response_model=VoiceTranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language_hint: str = Form(default="ml-IN"),
    stt: STTProvider = Depends(get_stt_provider),
):
    """Transcribe audio to text."""
    # Validate file size
    max_size = settings.max_audio_size_mb * 1024 * 1024
    content = await audio.read()
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail=f"Audio file too large (max {settings.max_audio_size_mb}MB)")
    
    # Validate content type
    allowed_types = ["audio/wav", "audio/mp3", "audio/mpeg", "audio/webm", "audio/ogg"]
    if audio.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format. Allowed: {allowed_types}")
    
    try:
        result = await stt.transcribe(content, language_hint)
        logger.info(f"Transcribed: {result.get('text', '')[:50]}... (lang: {result.get('language', '')})")
        return VoiceTranscribeResponse(
            transcript=result.get("text", ""),
            language=result.get("language", language_hint),
            confidence=result.get("confidence", 0.95),
            duration_seconds=result.get("duration_ms", 0) / 1000.0,
        )
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/synthesize", response_model=VoiceSynthesizeResponse)
async def synthesize_speech(
    request: VoiceSynthesizeRequest,
    tts: TTSProvider = Depends(get_tts_provider),
):
    """Synthesize text to speech."""
    try:
        audio_bytes = await tts.synthesize(request.text, request.language, request.voice)
        # In production, upload to storage and return URL
        # For demo, return base64 encoded audio
        import base64
        audio_b64 = base64.b64encode(audio_bytes).decode()
        audio_url = f"data:audio/mp3;base64,{audio_b64}"
        
        logger.info(f"Synthesized: {request.text[:50]}... (lang: {request.language})")
        return VoiceSynthesizeResponse(
            audio_url=audio_url,
            duration_seconds=len(request.text) * 0.1,
            format="mp3",
        )
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@router.post("/translate")
async def translate_text(
    text: str = Form(...),
    source_lang: str = Form(default="en-IN"),
    target_lang: str = Form(default="ml-IN"),
    translation: TranslationProvider = Depends(get_translation_provider),
):
    """Translate text between languages."""
    try:
        translated = await translation.translate(text, source_lang, target_lang)
        return {
            "translated_text": translated,
            "source_lang": source_lang,
            "target_lang": target_lang,
        }
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.post("/detect-language")
async def detect_language(
    text: str = Form(...),
    translation: TranslationProvider = Depends(get_translation_provider),
):
    """Detect language of text."""
    try:
        detected = await translation.detect_language(text)
        return {"detected_language": detected}
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")


@router.get("/providers")
async def list_providers(factory: VoiceProviderFactory = Depends(get_voice_factory_instance)):
    """List available voice providers and their status."""
    status = await factory.get_all_status()
    return {
        "coastal_languages": COASTAL_LANGUAGES,
        "coastal_language_names": COASTAL_LANGUAGE_NAMES,
        "stt": status.get("stt", {}),
        "tts": status.get("tts", {}),
        "translation": status.get("translation", {}),
    }


@router.get("/languages")
async def list_languages():
    """List supported coastal languages."""
    return {
        "languages": COASTAL_LANGUAGES,
        "names": COASTAL_LANGUAGE_NAMES,
        "count": len(COASTAL_LANGUAGES),
    }