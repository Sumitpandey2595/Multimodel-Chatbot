from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class MessageBase(BaseModel):
    role: str
    content: str
    input_type: str = "text"
    output_type: str = "text"
    metadata_json: Optional[Dict[str, Any]] = None

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    title: str = "New Conversation"

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True

class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []

class SourceItem(BaseModel):
    type: str  # "document" or "web"
    title: str
    snippet: str
    url: Optional[str] = None
    document_id: Optional[str] = None
    score: Optional[float] = None

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1, description="User prompt or question")
    file_ids: Optional[List[str]] = Field(default=[], description="Uploaded document or image IDs to query")
    enable_web_search: Optional[bool] = Field(default=None, description="Force web search or let AI auto-decide")
    enable_tts: Optional[bool] = Field(default=False, description="Generate audio speech response")

class ChatResponse(BaseModel):
    conversation_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse
    sources: List[SourceItem] = []
    web_search_used: bool = False
    generated_doc_url: Optional[str] = None
    audio_url: Optional[str] = None
    emotion_detected: Optional[Dict[str, Any]] = None
