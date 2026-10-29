import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class WebSearch(Base):
    __tablename__ = "web_searches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(String(500), nullable=False)
    results = Column(JSON, nullable=False, default=list)  # list of {title, url, snippet}
    created_at = Column(DateTime, default=utc_now)

    conversation = relationship("Conversation", back_populates="web_searches")
