from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.database.session import get_db, engine
from backend.app.services.llm_service import llm_service
from backend.app.config import settings
import os

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint returning database connectivity,
    AI provider status, and environment readiness.
    """
    db_status = "ok"
    db_type = engine.dialect.name
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    uploads_ready = os.path.exists(settings.UPLOAD_DIR)

    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "database": {
            "status": db_status,
            "dialect": db_type,
        },
        "ai_service": {
            "provider": "Google Gemini",
            "model": settings.DEFAULT_LLM_MODEL,
            "configured": llm_service.is_configured(),
            "mode": "Live AI" if llm_service.is_configured() else "Interactive Demo Fallback"
        },
        "uploads": {
            "status": "ready" if uploads_ready else "not_found",
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB
        }
    }
