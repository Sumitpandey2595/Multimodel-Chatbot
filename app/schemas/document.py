from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    extracted_text_preview: Optional[str] = None
    chunk_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    download_url: str
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, description="Document title")
    content: str = Field(..., min_length=1, description="Document body content")
    file_format: str = Field("docx", description="Output format: docx, txt, md, or pdf")
    conversation_id: Optional[str] = None

class DocumentEditRequest(BaseModel):
    document_id: str = Field(..., description="ID of the document to edit")
    instructions: str = Field(..., min_length=1, description="Edit instructions e.g. 'Add Python to skills and improve objective'")
    target_format: Optional[str] = Field(None, description="Optional target format if format conversion is desired")
    conversation_id: Optional[str] = None

class DocumentActionResponse(BaseModel):
    success: bool
    filename: str
    download_url: str
    summary_of_changes: str
    message: str
