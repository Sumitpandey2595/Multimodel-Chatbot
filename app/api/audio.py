from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.schemas.audio import TTSRequest, TTSResponse, TranscribeResponse
from backend.app.services.audio_service import generate_tts, transcribe_audio_file
from backend.app.services.llm_service import llm_service
from backend.app.utils.file_utils import save_upload_file, get_file_extension
from backend.app.config import settings

router = APIRouter(prefix="/audio", tags=["Audio"])

@router.post("/speak", response_model=TTSResponse)
def text_to_speech_endpoint(request: TTSRequest):
    """
    Converts input text into spoken audio MP3 and returns a downloadable URL.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    audio_url = generate_tts(request.text, language=request.language)
    if not audio_url:
        raise HTTPException(status_code=500, detail="Failed to synthesize speech audio.")

    return TTSResponse(audio_url=audio_url, message="Audio synthesized successfully.")

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """
    Accepts an audio file upload and returns its transcription.
    """
    ext = get_file_extension(file.filename)
    if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type '{ext}'. Allowed: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}"
        )

    _, file_path, _ = await save_upload_file(file, category="audio")
    transcript = await transcribe_audio_file(file_path, gemini_service=llm_service)

    return TranscribeResponse(text=transcript, confidence=0.95)
