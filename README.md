# Multimodal AI Chatbot — MVP

A beginner-friendly, clean, and extensible **Multimodal AI Chatbot** combining Vision AI, Retrieval-Augmented Generation (RAG), Live Web Search, Document Creation & Editing, and Personal Emotional Support.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Key Features & MVP Scope](#2-key-features--mvp-scope)
3. [Technology Stack](#3-technology-stack)
4. [System Architecture](#4-system-architecture)
5. [RAG Architecture](#5-rag-architecture)
6. [Project Structure](#6-project-structure)
7. [Prerequisites](#7-prerequisites)
8. [Installation & Setup](#8-installation--setup)
   - [Environment Variables](#environment-variables)
   - [PostgreSQL with pgvector Setup](#postgresql-with-pgvector-setup)
   - [Backend Setup](#backend-setup)
   - [Frontend Setup](#frontend-setup)
9. [How to Run the Application](#9-how-to-run-the-application)
10. [API Endpoints Reference](#10-api-endpoints-reference)
11. [Supported File Formats](#11-supported-file-formats)
12. [Workflows & Example Usage](#12-workflows--example-usage)
    - [Multimodal Vision Workflow](#multimodal-vision-workflow)
    - [RAG Workflow](#rag-workflow)
    - [Web Search Workflow](#web-search-workflow)
    - [Document Editing Workflow](#document-editing-workflow)
    - [Emotional Assistance & Safety Protocol](#emotional-assistance--safety-protocol)
13. [Security Considerations](#13-security-considerations)
14. [Limitations & Future Improvements](#14-limitations--future-improvements)
15. [Troubleshooting Guide](#15-troubleshooting-guide)
16. [Contributors & License](#16-contributors--license)

---

## 1. Project Overview

The **Multimodal AI Chatbot** is a full-stack AI application designed to provide rich multimodal intelligence without unnecessary architectural complexity. It accepts multiple input formats (Text, Images, PDF documents, Word DOCX documents, Audio) and provides multiple output formats (Structured text with Markdown, downloadable modified documents, Text-to-Speech audio, and web citations).

It is built for developers, students, and engineers looking for a clear, real-world baseline for:
- Connecting React with FastAPI
- Ingesting, chunking, and embedding documents for vector similarity retrieval
- Performing automated external web searches only when necessary
- Safely handling personal emotional distress and crisis triggers

---

## 2. Key Features & MVP Scope

### In-Scope Features
- **Multimodal Inputs:**
  - Text prompts
  - Images (`.png`, `.jpg`, `.jpeg`, `.webp`)
  - PDF documents (`.pdf`)
  - Word documents (`.docx`, `.doc`)
  - Plaintext & Markdown (`.txt`, `.md`)
  - Voice audio inputs via microphone (Web Speech API and audio files)
- **Multimodal Outputs:**
  - Rich Markdown formatting with syntax highlighting
  - Text-to-Speech (TTS) audio narration for answers
  - Downloadable updated documents preserving original files
  - Interactive source citation cards with match relevance scores
- **RAG (Retrieval-Augmented Generation):**
  - Text extraction from PDFs and Word documents
  - Recursive overlapping text chunker (700 characters, 150 overlap)
  - Vector embedding generation (768 dimensions)
  - Vector similarity retrieval with cosine math
  - Prompt context injection with source attribution
- **Intelligent Web Search:**
  - Heuristic classifier detects if query requires real-time/temporal information
  - DuckDuckGo zero-key web search integration
  - Distinguishes external web citations from internal document citations
- **Document Creation & Editing:**
  - Create new `.docx`, `.txt`, `.md` documents directly from chat
  - Request modifications (e.g. "Add Python to skills and revise summary")
  - Automatic version generation without overwriting source documents
- **Emotional Support & Safety Protocols:**
  - Empathetic conversational tone and active listening
  - Clear boundaries (never pretends to be a medical doctor or licensed therapist)
  - Hardcoded crisis detection (identifies self-harm or danger keywords and provides immediate 24/7 hotline resources including 988)
- **Conversation Memory:**
  - Chat history stored in PostgreSQL (with automatic local SQLite fallback)
  - Remembers names, preferences, and context across messages in a session

### Explicitly Out of Scope
- No user authentication / passwords / OAuth (instant local access)
- No complex admin dashboards or enterprise role management
- No microservices or heavy message queues
- No video generation

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18, Vite | High-performance reactive UI |
| **Icons & Styling** | Lucide React, Custom Dark CSS | Modern ChatGPT/Claude aesthetic |
| **Backend** | Python 3.10+, FastAPI | High-speed async REST API |
| **Database ORM** | SQLAlchemy 2.0, Psycopg 3 | Database management and migrations |
| **Database** | PostgreSQL + pgvector (with SQLite fallback) | Persistence of chats, chunks, and documents |
| **AI / LLM** | Google Gemini (`gemini-1.5-flash`) | Vision, embeddings, audio, and language synthesis |
| **Document Processing** | `pypdf`, `python-docx` | Extraction & programmatic document creation |
| **Web Search** | DuckDuckGo (`ddgs`) | Fast zero-config web searching |
| **Speech / Audio** | Web Speech API, `gTTS` | Browser voice dictation & speech synthesis |

---

## 4. System Architecture

```mermaid
flowchart TD
    User["User Interface (React + Vite)"]
    
    subgraph FastAPI Backend
        API["FastAPI REST Endpoints (/api)"]
        Chat["Chat Orchestrator (/api/chat)"]
        DocService["Document Engine (/api/documents)"]
        SearchService["Web Search Service (/api/search)"]
        AudioService["Audio & Speech (/api/audio)"]
        EmotionService["Emotion & Safety Guardrails"]
        LLMService["Gemini AI Service Layer"]
        RAG["RAG Pipeline"]
    end

    subgraph Storage & Persistence
        DB[("PostgreSQL / SQLite")]
        VectorStore[("pgvector / Vector Index")]
        Uploads[("Local Uploads /uploads")]
    end

    User -->|"Text, Image, PDF, DOCX, Audio"| API
    API --> Chat
    API --> DocService
    API --> AudioService
    
    Chat --> EmotionService
    Chat --> SearchService
    Chat --> RAG
    
    RAG --> DocService
    RAG --> VectorStore
    
    Chat --> LLMService
    LLMService -->|"Gemini 1.5 Flash"| ExternalAI["Google AI Studio"]
    SearchService -->|"HTML Search"| DuckDuckGo["DuckDuckGo Search Engine"]
    
    DocService --> Uploads
    Chat --> DB
```

---

## 5. RAG Architecture

```mermaid
flowchart LR
    A["Uploaded File (PDF/DOCX)"] --> B["Text Extraction (pypdf/docx)"]
    B --> C["Recursive Chunker (700 char, 150 overlap)"]
    C --> D["Embedding Generator (768-dim)"]
    D --> E[("Vector Storage (PostgreSQL/pgvector)")]

    Q["User Query"] --> F["Query Embedding"]
    F --> G["Similarity Search (Cosine Score)"]
    E --> G
    G --> H["Top-K Retrieved Chunks"]
    H --> I["Context Augmented Prompt"]
    Q --> I
    I --> J["Multimodal LLM"]
    J --> K["Response with Citations"]
```

---

## 6. Project Structure

```
MultiModel chatbot/
│
├── docker-compose.yml           # PostgreSQL + pgvector Docker service
├── run_backend.bat              # 1-click Windows launcher for FastAPI
├── run_frontend.bat             # 1-click Windows launcher for React
├── start_app.bat                # 1-click Windows launcher for entire stack
├── .env.example                 # Example configuration template
├── .gitignore                   # Safe git ignores (secrets, venv, uploads)
├── README.md                    # Comprehensive documentation
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app definition, CORS, static mounts
│   │   ├── config.py            # Pydantic Settings configuration
│   │   │
│   │   ├── api/
│   │   │   ├── chat.py          # /api/chat & /api/conversations
│   │   │   ├── documents.py     # /api/upload, /api/documents/create, /api/documents/edit
│   │   │   ├── search.py        # /api/search
│   │   │   ├── audio.py         # /api/audio/transcribe, /api/audio/speak
│   │   │   └── health.py        # /api/health
│   │   │
│   │   ├── services/
│   │   │   ├── llm_service.py      # Gemini integration with fallback mode
│   │   │   ├── rag_service.py      # Text chunking, embeddings, similarity
│   │   │   ├── document_service.py # PDF/DOCX extract, create, and rewrite
│   │   │   ├── search_service.py   # DuckDuckGo query classifier and search
│   │   │   ├── audio_service.py    # gTTS and audio processing
│   │   │   └── emotion_service.py  # Emotional analysis & crisis detection
│   │   │
│   │   ├── models/
│   │   │   ├── conversation.py  # Conversation & Message SQL models
│   │   │   ├── document.py      # Document & DocumentChunk SQL models
│   │   │   └── search.py        # WebSearch SQL models
│   │   │
│   │   ├── schemas/
│   │   │   ├── chat.py          # Pydantic schemas for Chat
│   │   │   ├── document.py      # Pydantic schemas for Documents
│   │   │   ├── search.py        # Pydantic schemas for Search
│   │   │   └── audio.py         # Pydantic schemas for Audio
│   │   │
│   │   ├── database/
│   │   │   ├── base.py          # SQLAlchemy declarative Base
│   │   │   └── session.py       # Engine, SessionLocal, PostgreSQL/SQLite fallback
│   │   │
│   │   └── utils/
│   │       ├── file_utils.py    # Filename sanitization, async file saving
│   │       └── text_utils.py    # Recursive chunker, cosine similarity math
│   │
│   ├── uploads/                 # Local directory for files
│   │   ├── documents/
│   │   ├── images/
│   │   ├── audio/
│   │   └── generated/
│   │
│   ├── requirements.txt         # Python dependencies
│   ├── test_app.py              # Automated backend test suite
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Header.jsx          # Header with status pills and actions
    │   │   ├── ChatWindow.jsx      # Message scroll area with starter cards
    │   │   ├── MessageBubble.jsx   # Markdown, code blocks, TTS, citations
    │   │   ├── ChatInput.jsx       # Multi-attach input, search/voice toggles
    │   │   ├── FileUpload.jsx      # Image & document file pickers
    │   │   ├── VoiceInput.jsx      # Web Speech API dictation
    │   │   ├── DocumentPreview.jsx # Document library, creation, and editor modal
    │   │   └── SourceList.jsx      # Visual citations for RAG & Web
    │   │
    │   ├── pages/
    │   │   └── ChatPage.jsx        # Sidebar history and main layout
    │   │
    │   ├── services/
    │   │   └── api.js              # Centralized backend HTTP client
    │   │
    │   ├── App.jsx
    │   ├── index.css               # Full responsive CSS stylesheet
    │   └── main.jsx
    │
    ├── package.json
    ├── vite.config.js
    └── index.html
```

---

## 7. Prerequisites

Before installing, ensure you have:
- **Node.js**: v18+ or v20+
- **Python**: 3.10+ (tested through Python 3.14)
- **Git** (optional, for cloning)
- **Docker Desktop** (optional, if you want PostgreSQL + pgvector container)

---

## 8. Installation & Setup

### Environment Variables

Copy `.env.example` to `backend/.env`:

```bash
cp .env.example backend/.env
```

Edit `backend/.env` with your settings:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/multimodal_chatbot

# Google Gemini API Key (Get free key from https://aistudio.google.com/)
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Model Selection
DEFAULT_LLM_MODEL=gemini-1.5-flash
EMBEDDING_MODEL=models/text-embedding-004

# File Upload Settings
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=20
```

> **Note on Zero Configuration:** If you do not have a Gemini API key immediately or PostgreSQL is not running, the application starts in **Interactive Demo Mode** with SQLite automatically. It does not crash, enabling you to test file uploads, document chunking, web searches, and audio generation right away!

---

### PostgreSQL with pgvector Setup

#### Option A: 1-Command Docker Setup (Recommended)
If you have Docker installed, simply run:

```bash
docker compose up -d
```
This spins up PostgreSQL 16 with the official `pgvector` extension enabled on port `5432`.

#### Option B: Native PostgreSQL
1. Create a database named `multimodal_chatbot`:
   ```sql
   CREATE DATABASE multimodal_chatbot;
   ```
2. Enable pgvector (if installed):
   ```sql
   \c multimodal_chatbot;
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Update `DATABASE_URL` in `backend/.env`.

#### Option C: Automatic Local SQLite Fallback
If PostgreSQL is not running on port `5432`, the backend detects the connection timeout and automatically falls back to `sqlite:///./chatbot.db`. Zero manual configuration required!

---

### Backend Setup

1. Open a terminal in the project root:
   ```bash
   python -m venv backend/venv
   ```
2. Activate the virtual environment:
   - **Windows PowerShell:**
     ```powershell
     .\backend\venv\Scripts\Activate.ps1
     ```
   - **Windows Command Prompt:**
     ```cmd
     backend\venv\Scripts\activate.bat
     ```
   - **Linux / macOS:**
     ```bash
     source backend/venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Run the automated test suite to verify your installation:
   ```bash
   python backend/test_app.py
   ```

---

### Frontend Setup

1. Open a terminal in `frontend/`:
   ```bash
   cd frontend
   npm install
   ```

---

## 9. How to Run the Application

### Method 1: 1-Click Launcher (Windows)
Double-click `start_app.bat` in the project root directory. It will automatically launch both the FastAPI backend and Vite React frontend in separate windows.

### Method 2: Manual Start

**Terminal 1 (Backend):**
```powershell
.\backend\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API is live at: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```
- Open browser at: `http://localhost:3000`

---

## 10. API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System health, database dialect, and AI provider status |
| `POST` | `/api/chat` | Main multimodal chat orchestrator |
| `GET` | `/api/conversations` | List conversation sessions |
| `POST` | `/api/conversations` | Create a new conversation session |
| `GET` | `/api/conversations/{id}` | Get conversation messages history |
| `DELETE` | `/api/conversations/{id}` | Delete conversation and its messages |
| `POST` | `/api/upload` | Upload files (PDF, DOCX, Images, Audio) & ingest RAG |
| `GET` | `/api/documents` | List uploaded and generated documents |
| `POST` | `/api/documents/create` | Programmatically create a new document (.docx/.txt/.md) |
| `POST` | `/api/documents/edit` | AI-assisted document modification & generation |
| `GET` | `/api/documents/download/{filename}` | Download generated or uploaded document files |
| `POST` | `/api/search` | Direct DuckDuckGo web search |
| `POST` | `/api/audio/speak` | Synthesize text to speech audio MP3 via gTTS |
| `POST` | `/api/audio/transcribe` | Transcribe voice recording into text |

---

## 11. Supported File Formats

| Category | Extensions | Processing Method |
|---|---|---|
| **Images** | `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif` | Multimodal Vision understanding (Gemini) |
| **Documents** | `.pdf` | Extracted via `pypdf`, chunked, vectorized for RAG |
| **Word Docs** | `.docx`, `.doc` | Extracted & formatted via `python-docx` |
| **Text Docs** | `.txt`, `.md` | Plaintext parsing and RAG ingestion |
| **Audio** | `.wav`, `.mp3`, `.m4a`, `.webm` | Web Speech API & speech recognition |

---

## 12. Workflows & Example Usage

### Multimodal Vision Workflow
1. User clicks the **Image** button in the chat input.
2. Selects an image (e.g. `architecture_diagram.png`).
3. Types: `"Explain this diagram and its main components."`
4. The backend routes the image to Gemini Vision API and returns an in-depth breakdown.

### RAG Workflow
1. User clicks the **Paperclip / Document** button and uploads `user_guide.pdf`.
2. The backend extracts text, splits it into overlapping semantic chunks, generates vector embeddings, and indexes them.
3. User asks: `"What are the safety steps in chapter 2?"`
4. RAG engine retrieves the top relevant chunks, provides them in the LLM prompt, and answers with explicit citation tags.
5. In the UI, an expandable **"Referenced X sources"** card appears with the exact matching text snippets and relevance scores.

### Web Search Workflow
1. User asks: `"What are the latest developments in AI this week?"`
2. The backend heuristic classifier detects the temporal keyword `"latest"` and `"this week"`.
3. It performs a live DuckDuckGo web search, parses the top snippets and URLs.
4. The LLM synthesizes an up-to-date answer citing the web sources with clickable external links.
5. For standard questions like `"What is Python?"`, web search is automatically bypassed.

### Document Editing Workflow
1. User opens the **Documents Hub** in the header or uploads `resume.docx`.
2. Under the **AI Document Editor** tab, selects the document and inputs:
   > *"Add Python, FastAPI, and Docker to my technical skills, and sharpen the professional summary."*
3. The system processes the original text with the LLM, creates an updated document (e.g. `resume_updated.docx`), and saves it in `uploads/generated/`.
4. The original file is untouched, and a download button is presented immediately.

### Emotional Assistance & Safety Protocol
1. User says: *"I've been feeling stressed, lonely, and burned out with my work."*
2. Emotion analyzer detects the emotional state (`stress`, `loneliness`).
3. Assistant responds with empathy, active listening, healthy coping recommendations (breathing exercises, speaking to friends), and asks supportive follow-up questions.
4. **Safety Protocol:** If self-harm keywords are detected, the system immediately presents verified 24/7 crisis hotlines (**988** Suicide & Crisis Lifeline in US/Canada, **14416** in India, **111/116 123** in UK) without offering amateur diagnoses.

---

## 13. Security Considerations

- **API Keys Protected:** API keys are never bundled into the frontend or exposed in JavaScript. All keys live exclusively in the backend `.env` file.
- **Path Traversal Protection:** All file uploads are sanitized using `sanitize_filename` and assigned random UUID prefixes to prevent directory traversal attacks (`../`).
- **File Size & Type Whitelisting:** Enforces a strict 20MB limit and only accepts whitelisted MIME types and extensions.
- **CORS Configuration:** Configured for local development and easily locked down to production domains.
- **Safe Error Masking:** Production exceptions return user-friendly messages rather than exposing raw server stack traces.

---

## 14. Limitations & Future Improvements

### Current MVP Limitations
- Uses local frequency-based embeddings when running without an external AI key.
- Web search relies on DuckDuckGo HTML scraping; high-frequency bursts may experience rate limits.
- Voice transcription depends on browser Web Speech API support (Google Chrome and Edge recommended).

### Future Improvements
- Add persistent user accounts with JWT authentication when moving beyond MVP.
- Integrate OCR (e.g. `tesseract` or `easyocr`) for scanned images and non-selectable PDFs.
- Add streaming responses via Server-Sent Events (SSE) or WebSockets.
- Support additional LLM providers (Anthropic Claude, OpenAI, Ollama for local offline LLMs).

---

## 15. Troubleshooting Guide

### 1. PostgreSQL Connection Warning
- **Symptom:** Backend prints `Could not connect to PostgreSQL... Falling back to local SQLite`.
- **Cause:** PostgreSQL is not running on localhost:5432.
- **Fix:** Start PostgreSQL or run `docker compose up -d`. The application will continue functioning smoothly on SQLite in the meantime.

### 2. Gemini API Key Notice
- **Symptom:** Chatbot responds: `To enable live responses from Google Gemini, add your GEMINI_API_KEY to backend/.env`.
- **Cause:** `GEMINI_API_KEY` is empty in `backend/.env`.
- **Fix:** Obtain a free key from [Google AI Studio](https://aistudio.google.com/) and paste it into `backend/.env`, then restart the backend.

### 3. Voice Input Permission Denied
- **Symptom:** Microphone button triggers permission error.
- **Fix:** In your browser URL bar, ensure microphone permissions are granted for `http://localhost:3000`.

---

## 16. Contributors & License

- **Author:** Built as a clean, beginner-friendly Multimodal AI Chatbot MVP.
- **License:** MIT License. Free to use, adapt, and build upon.
