@echo off
title Multimodal AI Chatbot Launcher
cd /d "%~dp0"

echo ========================================================
echo Launching Multimodal AI Chatbot (Backend & Frontend)
echo ========================================================

start "Backend - FastAPI" cmd /k "%~dp0run_backend.bat"
timeout /t 3 /nobreak > nul
start "Frontend - React" cmd /k "%~dp0run_frontend.bat"

echo.
echo Application started successfully!
echo.
echo - Web Chat Interface: http://localhost:3000
echo - Backend API Docs:   http://127.0.0.1:8000/docs
echo.
echo Keep both terminal windows open while using the application.
timeout /t 5
