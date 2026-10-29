import os
import sys
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from backend.app.database.session import init_db
from backend.app.services.search_service import should_search_web
from backend.app.services.emotion_service import analyze_emotion
from backend.app.utils.text_utils import chunk_text, cosine_similarity

init_db()
client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert "ai_service" in data
    print("[PASS] Health check test passed!")

def test_create_and_list_conversations():
    # Create conversation
    create_res = client.post("/api/conversations", json={"title": "Test AI Chat"})
    assert create_res.status_code == 200
    convo = create_res.json()
    assert convo["title"] == "Test AI Chat"
    convo_id = convo["id"]

    # List conversations
    list_res = client.get("/api/conversations")
    assert list_res.status_code == 200
    convos = list_res.json()
    assert any(c["id"] == convo_id for c in convos)
    print("[PASS] Conversation CRUD test passed!")
    return convo_id

def test_chat_flow(convo_id):
    # Test chat endpoint
    chat_res = client.post("/api/chat", json={
        "conversation_id": convo_id,
        "message": "Hello, my name is Alex. Can you assist me with Python programming?",
        "enable_web_search": False,
        "enable_tts": False
    })
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert data["conversation_id"] == convo_id
    assert data["user_message"]["content"] == "Hello, my name is Alex. Can you assist me with Python programming?"
    assert len(data["assistant_message"]["content"]) > 0
    print("[PASS] Standard chat flow test passed!")

def test_emotion_and_safety():
    # 1. Stress / sadness emotion detection
    emotion_data = analyze_emotion("I feel really stressed and overwhelmed with deadlines.")
    assert "stress" in emotion_data["detected_emotions"]
    assert emotion_data["is_crisis"] is False

    # 2. Self-harm / crisis detection
    crisis_data = analyze_emotion("I want to end my life, please help")
    assert crisis_data["is_crisis"] is True
    assert "988" in crisis_data["crisis_response"]

    # 3. Test through chat endpoint
    chat_crisis = client.post("/api/chat", json={
        "message": "I feel like hurting myself",
        "enable_web_search": False
    })
    assert chat_crisis.status_code == 200
    crisis_json = chat_crisis.json()
    assert "988" in crisis_json["assistant_message"]["content"]
    assert crisis_json["emotion_detected"]["is_crisis"] is True
    print("[PASS] Emotional assistance & Safety protocol test passed!")

def test_web_search_logic():
    # Keyword classifier
    assert should_search_web("What is the latest news about AI in 2026?") is True
    assert should_search_web("What is Python?") is False
    assert should_search_web("Look up on the web who won the match") is True

    # Web search API endpoint
    res = client.post("/api/search", json={"query": "FastAPI python web framework", "max_results": 2})
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    print("[PASS] Web search classification & search test passed!")

def test_document_creation_and_editing():
    # 1. Create document
    create_res = client.post("/api/documents/create", json={
        "title": "Software Engineer Resume",
        "content": "Professional Summary: Passionate developer.\n\nSkills: JavaScript, HTML, CSS.",
        "file_format": "docx"
    })
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["success"] is True
    assert created["filename"].endswith(".docx")
    assert "/api/documents/download/" in created["download_url"]

    # 2. List documents
    docs_res = client.get("/api/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json()
    assert len(docs) > 0
    doc_id = docs[0]["id"]

    # 3. Edit document
    edit_res = client.post("/api/documents/edit", json={
        "document_id": doc_id,
        "instructions": "Add Python and FastAPI to skills section.",
        "target_format": "docx"
    })
    assert edit_res.status_code == 200
    edited = edit_res.json()
    assert edited["success"] is True
    assert edited["filename"].endswith(".docx")
    print("[PASS] Document creation and editing test passed!")

def test_tts_audio():
    res = client.post("/api/audio/speak", json={"text": "Hello, welcome to Multimodal AI."})
    assert res.status_code == 200
    data = res.json()
    assert data["audio_url"].startswith("/uploads/audio/")
    print("[PASS] Text-to-speech audio test passed!")

def test_rag_chunking_and_similarity():
    sample_text = (
        "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints.\n\n"
        "The key features are: Fast: Very high performance, on par with NodeJS and Go (thanks to Starlette and Pydantic). One of the fastest Python frameworks available.\n\n"
        "Fast to code: Increase the speed to develop features by about 200% to 300%.\n\n"
        "Fewer bugs: Reduce about 40% of human (developer) induced errors."
    )
    chunks = chunk_text(sample_text, chunk_size=120, chunk_overlap=30)
    assert len(chunks) >= 2

    v1 = [1.0, 0.0, 0.5]
    v2 = [1.0, 0.0, 0.5]
    v3 = [-1.0, 0.0, -0.5]
    assert round(cosine_similarity(v1, v2), 4) == 1.0
    assert round(cosine_similarity(v1, v3), 4) == -1.0
    print("[PASS] RAG chunking and vector math test passed!")

if __name__ == "__main__":
    print("--- Running Multimodal AI Chatbot Test Suite ---")
    test_health()
    convo_id = test_create_and_list_conversations()
    test_chat_flow(convo_id)
    test_emotion_and_safety()
    test_web_search_logic()
    test_document_creation_and_editing()
    test_tts_audio()
    test_rag_chunking_and_similarity()
    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")
