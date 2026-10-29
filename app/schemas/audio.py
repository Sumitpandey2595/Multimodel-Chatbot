from pydantic import BaseModel, Field

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to convert to speech")
    language: str = Field("en", description="Language code e.g. en, es, fr, hi")

class TTSResponse(BaseModel):
    audio_url: str
    message: str = "Audio generated successfully"

class TranscribeResponse(BaseModel):
    text: str
    confidence: float = 1.0
