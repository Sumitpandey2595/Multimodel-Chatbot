import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database.session import init_db
from backend.app.api.health import router as health_router
from backend.app.api.chat import router as chat_router
from backend.app.api.documents import router as documents_router
from backend.app.api.search import router as search_router
from backend.app.api.audio import router as audio_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("uvicorn.error")

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Beginner-friendly Multimodal AI Chatbot API with RAG, Web Search, Document Editing, and Emotional Support.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local MVP development; can be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event: Ensure directories exist and initialize database
@app.on_event("startup")
def on_startup():
    logger.info("Starting Multimodal AI Chatbot backend...")
    for folder in ["documents", "images", "audio", "generated"]:
        os.makedirs(os.path.join(settings.UPLOAD_DIR, folder), exist_ok=True)
    init_db()
    logger.info("Startup complete. API ready at /api and documentation at /docs.")

# Mount static uploads directory for serving images, generated docs, and audio files
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API Routers under /api prefix
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(search_router, prefix=settings.API_V1_STR)
app.include_router(audio_router, prefix=settings.API_V1_STR)

# Global error handler for unhandled exceptions to return friendly messages without exposing raw traces
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing your request. Please try again or check backend logs.",
            "detail": str(exc)
        }
    )

@app.get("/")
def root():
    return {
        "message": "Welcome to the Multimodal AI Chatbot API",
        "documentation": "/docs",
        "health": "/api/health",
        "status": "running"
    }
