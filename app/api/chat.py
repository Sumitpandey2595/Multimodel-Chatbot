import os
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.conversation import Conversation, Message
from backend.app.models.document import Document
from backend.app.models.search import WebSearch
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationCreate,
    MessageResponse,
    SourceItem
)
from backend.app.services.llm_service import llm_service
from backend.app.services.rag_service import rag_service
from backend.app.services.search_service import should_search_web, search_web
from backend.app.services.emotion_service import analyze_emotion
from backend.app.services.audio_service import generate_tts
from backend.app.config import settings

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["Chat & Conversations"])

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main Multimodal Chatbot Orchestrator:
    - Handles Text, Image, Document RAG, Audio, and Emotional assistance.
    - Manages conversation memory in PostgreSQL.
    - Performs intelligent web search when external/recent info is needed.
    """
    user_query = request.message.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="User message cannot be empty.")

    # 1. Resolve or create Conversation
    conversation_id = request.conversation_id
    if conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            # If invalid ID provided, create new
            conversation = Conversation(title=user_query[:35] + ("..." if len(user_query) > 35 else ""))
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
    else:
        conversation = Conversation(title=user_query[:35] + ("..." if len(user_query) > 35 else ""))
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    conversation_id = conversation.id

    # 2. Emotional Analysis & Crisis Safety Check
    emotion_result = analyze_emotion(user_query)
    if emotion_result.get("is_crisis"):
        # Immediate safety intervention
        safety_text = emotion_result.get("crisis_response")

        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=user_query,
            input_type="text",
            output_type="text"
        )
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=safety_text,
            input_type="text",
            output_type="text",
            metadata_json={"crisis_detected": True}
        )
        db.add_all([user_msg, assistant_msg])
        conversation.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user_msg)
        db.refresh(assistant_msg)

        return ChatResponse(
            conversation_id=conversation_id,
            user_message=MessageResponse.model_validate(user_msg),
            assistant_message=MessageResponse.model_validate(assistant_msg),
            sources=[],
            web_search_used=False,
            emotion_detected=emotion_result
        )

    # 3. Inspect attached files (Images, Documents, Audio)
    attached_docs = []
    attached_images = []
    input_type = "text"

    if request.file_ids:
        records = db.query(Document).filter(Document.id.in_(request.file_ids)).all()
        for doc in records:
            ext = f".{doc.file_type.lower()}"
            if ext in settings.ALLOWED_IMAGE_EXTENSIONS:
                attached_images.append(doc)
                input_type = "image"
            elif ext in settings.ALLOWED_DOC_EXTENSIONS:
                attached_docs.append(doc)
                input_type = "document"
            elif ext in settings.ALLOWED_AUDIO_EXTENSIONS:
                input_type = "audio"

    # 4. Fetch recent conversation memory (last 6 messages)
    history_records = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(6)
        .all()
    )
    # Reverse to chronological order
    history_records.reverse()
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in history_records
        if m.role in ["user", "assistant"]
    ]

    # 5. Process Multimodal Image input if present
    sources_list: List[SourceItem] = []
    assistant_reply = ""
    web_search_used = False

    if attached_images:
        img_record = attached_images[0]
        logger.info(f"Processing multimodal image analysis for file: {img_record.filename}")
        assistant_reply = llm_service.generate_multimodal(
            prompt=user_query,
            image_path=img_record.file_path,
            system_instruction="You are a helpful multimodal AI. Analyze the image carefully and answer the user's questions clearly."
        )

    else:
        # 6. RAG Retrieval (Document context)
        rag_context = ""
        doc_ids_to_query = [d.id for d in attached_docs] if attached_docs else None

        # Check for relevant chunks if docs are uploaded or in conversation
        relevant_chunks = rag_service.retrieve_relevant_chunks(
            db=db,
            query=user_query,
            document_ids=doc_ids_to_query,
            conversation_id=conversation_id,
            top_k=3
        )

        if relevant_chunks:
            rag_context = rag_service.format_context_for_prompt(relevant_chunks)
            for chk in relevant_chunks:
                sources_list.append(SourceItem(
                    type="document",
                    title=chk["filename"],
                    snippet=chk["text"][:180] + "...",
                    document_id=chk["document_id"],
                    score=chk["score"]
                ))

        # 7. Web Search Decision
        should_search = False
        if request.enable_web_search is True:
            should_search = True
        elif request.enable_web_search is None:
            should_search = should_search_web(user_query, has_attached_docs=bool(relevant_chunks or attached_docs))

        web_context = ""
        if should_search:
            web_search_used = True
            search_items = search_web(user_query, max_results=4)
            if search_items:
                web_context = "\n[WEB SEARCH RESULTS]\n"
                for idx, item in enumerate(search_items, 1):
                    web_context += f"Source [{idx}]: {item['title']}\nURL: {item['url']}\nSnippet: {item['snippet']}\n\n"
                    sources_list.append(SourceItem(
                        type="web",
                        title=item["title"],
                        url=item["url"],
                        snippet=item["snippet"][:180] + "..."
                    ))
                web_context += "[END WEB SEARCH RESULTS]\n"

                # Record search in database
                search_record = WebSearch(
                    conversation_id=conversation_id,
                    query=user_query,
                    results=search_items
                )
                db.add(search_record)
                db.commit()

        # 8. Build Prompt & System Instruction
        system_prompts = [
            "You are a helpful, versatile multimodal AI assistant capable of document understanding, web search synthesis, and supportive conversation.",
            "Always be clear, truthful, and helpful. If citing information from documents or web search results, reference your sources clearly."
        ]

        if emotion_result.get("empathy_prompt_instruction"):
            system_prompts.append(emotion_result["empathy_prompt_instruction"])

        full_prompt_parts = []
        if rag_context:
            full_prompt_parts.append(rag_context)
            full_prompt_parts.append("Note: Answer the user's question using the retrieved document context above. If the document doesn't contain the answer, say so.")

        if web_context:
            full_prompt_parts.append(web_context)
            full_prompt_parts.append("Note: Clearly distinguish information from web search from uploaded documents.")

        full_prompt_parts.append(f"User Query:\n{user_query}")
        final_prompt = "\n\n".join(full_prompt_parts)

        assistant_reply = llm_service.generate_text(
            prompt=final_prompt,
            system_instruction="\n\n".join(system_prompts),
            conversation_history=conversation_history
        )

    # 9. Optional TTS Speech generation
    audio_url = None
    if request.enable_tts:
        audio_url = generate_tts(assistant_reply)

    # 10. Persist Messages to Database
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=user_query,
        input_type=input_type,
        output_type="text",
        metadata_json={"file_ids": request.file_ids or []}
    )
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_reply,
        input_type="text",
        output_type="audio" if audio_url else "text",
        metadata_json={
            "sources": [s.model_dump() for s in sources_list],
            "web_search_used": web_search_used,
            "audio_url": audio_url
        }
    )
    db.add_all([user_msg, assistant_msg])
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    return ChatResponse(
        conversation_id=conversation_id,
        user_message=MessageResponse.model_validate(user_msg),
        assistant_message=MessageResponse.model_validate(assistant_msg),
        sources=sources_list,
        web_search_used=web_search_used,
        audio_url=audio_url,
        emotion_detected=emotion_result if emotion_result.get("detected_emotions") else None
    )

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(db: Session = Depends(get_db)):
    """Lists all conversations ordered by recent activity."""
    convs = db.query(Conversation).order_by(Conversation.updated_at.desc()).limit(30).all()
    results = []
    for c in convs:
        results.append(ConversationResponse(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=len(c.messages)
        ))
    return results

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(request: ConversationCreate, db: Session = Depends(get_db)):
    """Creates a new conversation session."""
    conv = Conversation(title=request.title or "New Conversation")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0
    )

@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_details(conversation_id: str, db: Session = Depends(get_db)):
    """Retrieves conversation details and full message history."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    return ConversationDetailResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=len(conv.messages),
        messages=[MessageResponse.model_validate(m) for m in conv.messages]
    )

@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Deletes a conversation and all its messages."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    db.delete(conv)
    db.commit()
    return {"success": True, "message": "Conversation deleted."}
