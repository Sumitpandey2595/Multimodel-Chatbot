@echo off
title Multimodal AI Chatbot - Frontend (React)
cd /d "%~dp0frontend"

echo ========================================================
echo Starting Multimodal AI Chatbot Frontend (React + Vite)...
echo ========================================================

if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
)

echo Starting Vite dev server on http://localhost:3000
call npm run dev
pause
