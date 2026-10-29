import os
import uuid
import logging
from gtts import gTTS
from backend.app.config import settings

logger = logging.getLogger("uvicorn.error")

def generate_tts(text: str, language: str = "en") -> str:
    """
    Converts text to an audio speech MP3 using gTTS.
    Returns the web URL path e.g. /uploads/audio/speech_xxx.mp3
    """
    try:
        # Limit text length to first 500 characters for snappy TTS in MVP
        tts_text = text.strip()
        if len(tts_text) > 500:
            tts_text = tts_text[:500] + "..."

        audio_dir = os.path.join(settings.UPLOAD_DIR, "audio")
        os.makedirs(audio_dir, exist_ok=True)

        filename = f"tts_{uuid.uuid4().hex[:10]}.mp3"
        filepath = os.path.join(audio_dir, filename)

        tts = gTTS(text=tts_text, lang=language, slow=False)
        tts.save(filepath)

        logger.info(f"Generated TTS audio file: {filepath}")
        return f"/uploads/audio/{filename}"
    except Exception as e:
        logger.error(f"Error generating TTS audio: {e}")
        return ""

async def transcribe_audio_file(filepath: str, gemini_service=None) -> str:
    """
    Transcribes audio. If Gemini service is available, uploads and transcribes natively.
    Otherwise returns an informative fallback message.
    """
    try:
        if gemini_service and gemini_service.is_configured():
            return await gemini_service.transcribe_audio_native(filepath)
        return "Audio input received. (To transcribe with AI, please configure GEMINI_API_KEY in .env)."
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return f"[Audio processing note: {str(e)}]"
