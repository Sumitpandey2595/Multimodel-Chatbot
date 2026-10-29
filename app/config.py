import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Multimodal AI Chatbot"
    API_V1_STR: str = "/api"
    
    # Database settings: Default to PostgreSQL, with automatic SQLite fallback if Postgres is unavailable
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/multimodal_chatbot")
    FALLBACK_SQLITE_URL: str = "sqlite:///./chatbot.db"
    
    # AI / LLM settings
    # Primary provider: Google Gemini
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gemini-1.5-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
    
    # Search settings
    SEARCH_API_KEY: Optional[str] = os.getenv("SEARCH_API_KEY", "")
    
    # Storage settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
    
    # Allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS: list[str] = [".png", ".jpg", ".jpeg", ".webp", ".gif"]
    ALLOWED_DOC_EXTENSIONS: list[str] = [".pdf", ".docx", ".txt", ".md"]
    ALLOWED_AUDIO_EXTENSIONS: list[str] = [".wav", ".mp3", ".m4a", ".webm", ".ogg"]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
