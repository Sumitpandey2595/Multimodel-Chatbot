@echo off
title Multimodal AI Chatbot - Backend (FastAPI)
cd /d "%~dp0"

echo ========================================================
echo Starting Multimodal AI Chatbot Backend (FastAPI)...
echo ========================================================

if not exist "backend\venv\Scripts\python.exe" (
    echo Creating virtual environment in backend\venv...
    python -m venv backend\venv
    echo Installing dependencies...
    backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
)

echo Starting server on http://127.0.0.1:8000 (API Docs: http://127.0.0.1:8000/docs)
backend\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
