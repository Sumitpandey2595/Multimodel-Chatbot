import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.document import Document, DocumentChunk
from backend.app.utils.text_utils import chunk_text, cosine_similarity
from backend.app.services.llm_service import llm_service

logger = logging.getLogger("uvicorn.error")

class RAGService:
    """
    RAG (Retrieval-Augmented Generation) pipeline:
    - Ingestion & Text extraction
    - Text chunking with overlap
    - Vector embedding generation
    - Similarity search & context retrieval
    - Prompt construction with citations
    """

    def ingest_document(self, db: Session, document: Document) -> int:
        """
        Processes an uploaded document:
        1. Breaks extracted text into overlapping chunks.
        2. Generates vector embeddings for each chunk.
        3. Stores DocumentChunk records in PostgreSQL/SQLite.
        """
        if not document.extracted_text or not document.extracted_text.strip():
            logger.warning(f"Document {document.id} ({document.filename}) has no text to ingest.")
            return 0

        chunks = chunk_text(document.extracted_text, chunk_size=700, chunk_overlap=150)
        logger.info(f"Ingesting document '{document.filename}' into {len(chunks)} chunks.")

        created_chunks = []
        for idx, text_chunk in enumerate(chunks):
            embedding = llm_service.generate_embedding(text_chunk)
            chunk_record = DocumentChunk(
                document_id=document.id,
                chunk_index=idx,
                chunk_text=text_chunk,
                embedding=embedding,
                metadata_json={
                    "filename": document.filename,
                    "chunk_index": idx,
                    "total_chunks": len(chunks)
                }
            )
            created_chunks.append(chunk_record)

        db.add_all(created_chunks)
        db.commit()
        logger.info(f"Successfully stored {len(created_chunks)} chunks for '{document.filename}'.")
        return len(created_chunks)

    def retrieve_relevant_chunks(
        self,
        db: Session,
        query: str,
        document_ids: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search to find the most relevant document chunks.
        Compatible with both pgvector and portable JSON embeddings.
        """
        if not query.strip():
            return []

        # 1. Query candidate chunks from DB
        chunk_query = db.query(DocumentChunk).join(Document)

        if document_ids and len(document_ids) > 0:
            chunk_query = chunk_query.filter(DocumentChunk.document_id.in_(document_ids))
        elif conversation_id:
            chunk_query = chunk_query.filter(Document.conversation_id == conversation_id)

        all_chunks = chunk_query.all()
        if not all_chunks:
            return []

        # 2. Generate embedding for query
        query_embedding = llm_service.generate_query_embedding(query)

        # 3. Calculate similarity score for each candidate chunk
        scored_chunks = []
        for chunk in all_chunks:
            chunk_embedding = chunk.embedding
            if not chunk_embedding:
                continue

            score = cosine_similarity(query_embedding, chunk_embedding)
            scored_chunks.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "filename": chunk.document.filename if chunk.document else "Document",
                "chunk_index": chunk.chunk_index,
                "text": chunk.chunk_text,
                "score": round(score, 4)
            })

        # 4. Sort by highest similarity
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)

        # 5. Return top K
        top_results = scored_chunks[:top_k]
        logger.info(f"Retrieved {len(top_results)} relevant chunks for query: '{query[:40]}...'")
        return top_results

    def format_context_for_prompt(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved chunks into a clean context block for the LLM prompt.
        """
        if not chunks:
            return ""

        context_lines = ["\n[RETRIEVED DOCUMENT CONTEXT]"]
        for idx, chunk in enumerate(chunks, 1):
            source_tag = f"Source {idx} ({chunk['filename']}, Part {chunk['chunk_index'] + 1}, Relevance: {int(chunk['score'] * 100)}%):"
            context_lines.append(f"{source_tag}\n{chunk['text']}\n")
        context_lines.append("[END DOCUMENT CONTEXT]\n")

        return "\n".join(context_lines)

rag_service = RAGService()
