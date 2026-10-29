import os
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List

from backend.app.database.session import get_db
from backend.app.config import settings
from backend.app.models.document import Document
from backend.app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentCreateRequest,
    DocumentEditRequest,
    DocumentActionResponse
)
from backend.app.utils.file_utils import (
    save_upload_file,
    determine_file_category,
    get_file_extension
)
from backend.app.services.document_service import (
    extract_text_from_file,
    create_document_file,
    edit_document_content
)
from backend.app.services.rag_service import rag_service
from backend.app.services.llm_service import llm_service

router = APIRouter(tags=["Documents & Files"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_file_endpoint(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Accepts images, PDFs, Word docs, TXT, MD, or audio.
    Saves file, extracts text, and automatically triggers RAG chunking & vectorization for documents.
    """
    category = determine_file_category(file.filename)
    if category == "unsupported":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported extensions: {', '.join(settings.ALLOWED_DOC_EXTENSIONS + settings.ALLOWED_IMAGE_EXTENSIONS + settings.ALLOWED_AUDIO_EXTENSIONS)}"
        )

    # Save to disk
    sanitized_name, relative_path, file_size = await save_upload_file(file, category=category)
    ext = get_file_extension(sanitized_name).replace(".", "")

    extracted_text = ""
    chunk_count = 0

    # If it is a document, extract text and ingest into RAG
    if category == "document":
        extracted_text = extract_text_from_file(relative_path, ext)
        # Create DB record
        doc_record = Document(
            conversation_id=conversation_id,
            filename=sanitized_name,
            file_type=ext,
            file_path=relative_path,
            file_size=file_size,
            extracted_text=extracted_text
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        # Ingest into RAG pipeline
        chunk_count = rag_service.ingest_document(db, doc_record)

    else:
        # Image or Audio record
        doc_record = Document(
            conversation_id=conversation_id,
            filename=sanitized_name,
            file_type=ext,
            file_path=relative_path,
            file_size=file_size,
            extracted_text=f"[{category.capitalize()} file: {sanitized_name}]"
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

    preview = (extracted_text[:300] + "...") if len(extracted_text) > 300 else extracted_text

    return DocumentUploadResponse(
        id=doc_record.id,
        filename=doc_record.filename,
        file_type=doc_record.file_type,
        file_size=doc_record.file_size,
        extracted_text_preview=preview,
        chunk_count=chunk_count,
        created_at=doc_record.created_at
    )

@router.post("/documents/create", response_model=DocumentActionResponse)
def create_document_endpoint(
    request: DocumentCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Creates a new document (DOCX, TXT, MD) and returns a downloadable link.
    """
    filename, download_url = create_document_file(
        title=request.title,
        content=request.content,
        file_format=request.file_format
    )

    # Register in database
    gen_path = os.path.join(settings.UPLOAD_DIR, "generated", filename).replace("\\", "/")
    doc_record = Document(
        conversation_id=request.conversation_id,
        filename=filename,
        file_type=request.file_format,
        file_path=gen_path,
        file_size=os.path.getsize(gen_path) if os.path.exists(gen_path) else 0,
        extracted_text=request.content
    )
    db.add(doc_record)
    db.commit()

    return DocumentActionResponse(
        success=True,
        filename=filename,
        download_url=download_url,
        summary_of_changes="New document created successfully.",
        message=f"Document '{filename}' is ready for download."
    )

@router.post("/documents/edit", response_model=DocumentActionResponse)
def edit_document_endpoint(
    request: DocumentEditRequest,
    db: Session = Depends(get_db)
):
    """
    Modifies an existing document according to instructions (summarize, rewrite, add sections).
    Generates an updated document without overwriting the original.
    """
    original_doc = db.query(Document).filter(Document.id == request.document_id).first()
    if not original_doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not original_doc.extracted_text:
        raise HTTPException(status_code=400, detail="Original document does not contain readable text to edit.")

    # Apply edits via LLM
    updated_text, summary = edit_document_content(
        original_content=original_doc.extracted_text,
        instructions=request.instructions,
        llm_service=llm_service
    )

    fmt = request.target_format or original_doc.file_type or "docx"
    base_name, _ = os.path.splitext(original_doc.filename)
    new_title = f"{base_name}_updated"

    out_filename, download_url = create_document_file(
        title=new_title,
        content=updated_text,
        file_format=fmt
    )

    # Save as new document record
    gen_path = os.path.join(settings.UPLOAD_DIR, "generated", out_filename).replace("\\", "/")
    new_doc = Document(
        conversation_id=request.conversation_id or original_doc.conversation_id,
        filename=out_filename,
        file_type=fmt,
        file_path=gen_path,
        file_size=os.path.getsize(gen_path) if os.path.exists(gen_path) else 0,
        extracted_text=updated_text
    )
    db.add(new_doc)
    db.commit()

    # Ingest new document chunks for future questions
    rag_service.ingest_document(db, new_doc)

    return DocumentActionResponse(
        success=True,
        filename=out_filename,
        download_url=download_url,
        summary_of_changes=summary,
        message="Document modified successfully."
    )

@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    """Lists all uploaded and generated documents."""
    docs = db.query(Document).order_by(Document.created_at.desc()).limit(50).all()
    results = []
    for d in docs:
        results.append(DocumentResponse(
            id=d.id,
            filename=d.filename,
            file_type=d.file_type,
            file_size=d.file_size,
            download_url=f"/api/documents/download/{os.path.basename(d.file_path)}",
            created_at=d.created_at
        ))
    return results

@router.get("/documents/download/{filename}")
def download_document_file(filename: str):
    """Safely serves generated or uploaded files for download."""
    # Check generated folder
    gen_path = os.path.join(settings.UPLOAD_DIR, "generated", filename)
    doc_path = os.path.join(settings.UPLOAD_DIR, "documents", filename)

    target_file = None
    if os.path.exists(gen_path):
        target_file = gen_path
    elif os.path.exists(doc_path):
        target_file = doc_path
    else:
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(
        target_file,
        filename=filename,
        media_type="application/octet-stream"
    )
