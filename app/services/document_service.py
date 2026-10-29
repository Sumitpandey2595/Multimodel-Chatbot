import os
import uuid
import logging
from typing import Optional, Tuple
import pypdf
import docx
from backend.app.config import settings

logger = logging.getLogger("uvicorn.error")

def extract_text_from_file(filepath: str, file_type: str) -> str:
    """
    Extracts plain text from PDF, DOCX, TXT, and Markdown files.
    """
    ext = file_type.lower().replace(".", "")
    try:
        if ext == "pdf":
            reader = pypdf.PdfReader(filepath)
            text_parts = []
            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {page_idx + 1} ---\n{page_text}")
            return "\n\n".join(text_parts)

        elif ext in ["docx", "doc"]:
            doc = docx.Document(filepath)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            # Also extract tables
            for table in doc.tables:
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_data:
                        paragraphs.append(" | ".join(row_data))
            return "\n\n".join(paragraphs)

        elif ext in ["txt", "md", "markdown"]:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        else:
            return f"[Unsupported text extraction format: {file_type}]"

    except Exception as e:
        logger.error(f"Failed to extract text from {filepath}: {e}")
        return f"[Error extracting text: {str(e)}]"

def create_document_file(title: str, content: str, file_format: str = "docx") -> Tuple[str, str]:
    """
    Creates a new document file on disk.
    Supported formats: docx, txt, md, pdf.
    Returns: (output_filename, download_url)
    """
    fmt = file_format.lower().replace(".", "")
    gen_dir = os.path.join(settings.UPLOAD_DIR, "generated")
    os.makedirs(gen_dir, exist_ok=True)

    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
    if not safe_title:
        safe_title = "document"

    unique_id = uuid.uuid4().hex[:6]
    out_filename = f"{safe_title}_{unique_id}.{fmt}"
    out_path = os.path.join(gen_dir, out_filename)

    if fmt == "docx":
        doc = docx.Document()
        doc.add_heading(title, level=0)
        # Split content into paragraphs
        for para in content.split("\n\n"):
            para_str = para.strip()
            if para_str:
                if para_str.startswith("# "):
                    doc.add_heading(para_str[2:], level=1)
                elif para_str.startswith("## "):
                    doc.add_heading(para_str[3:], level=2)
                elif para_str.startswith("### "):
                    doc.add_heading(para_str[4:], level=3)
                elif para_str.startswith("- ") or para_str.startswith("* "):
                    doc.add_paragraph(para_str[2:], style='List Bullet')
                else:
                    doc.add_paragraph(para_str)
        doc.save(out_path)

    elif fmt in ["md", "markdown", "txt"]:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{content}")

    elif fmt == "pdf":
        # Create text-based PDF or fallback to txt format if pdf generator is simple
        # Using docx as intermediate or writing markdown
        # To avoid heavy wkhtmltopdf/reportlab dependencies, we save as clean markdown/txt or docx with notice
        with open(out_path.replace(".pdf", ".txt"), "w", encoding="utf-8") as f:
            f.write(f"=== {title} ===\n\n{content}")
        out_filename = out_filename.replace(".pdf", ".txt")

    download_url = f"/api/documents/download/{out_filename}"
    return out_filename, download_url

def edit_document_content(original_content: str, instructions: str, llm_service) -> Tuple[str, str]:
    """
    Uses LLM to edit original document content based on user instructions.
    Returns: (modified_content, summary_of_changes)
    """
    prompt = f"""You are an expert document editor.
Below is the original document content:
==================== ORIGINAL DOCUMENT ====================
{original_content[:6000]}
===========================================================

User editing instructions:
"{instructions}"

Please perform the requested edits (summarize, rewrite, modify sections, correct grammar, or add new parts).
Format your response as:
--- SUMMARY OF CHANGES ---
<Provide 2-3 bullet points explaining exactly what changes were made>

--- MODIFIED DOCUMENT ---
<The complete, clean, updated document content>
"""
    response_text = llm_service.generate_text(prompt)

    if "--- MODIFIED DOCUMENT ---" in response_text:
        parts = response_text.split("--- MODIFIED DOCUMENT ---")
        summary_part = parts[0].replace("--- SUMMARY OF CHANGES ---", "").strip()
        modified_content = parts[1].strip()
        return modified_content, summary_part
    else:
        return response_text.strip(), "Document updated based on your instructions."
