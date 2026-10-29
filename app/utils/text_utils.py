import math
from typing import List

def clean_text(text: str) -> str:
    """Normalize whitespace and remove non-printable characters."""
    if not text:
        return ""
    # Replace multiple spaces/newlines with a single space or double newline
    lines = [line.strip() for line in text.splitlines()]
    clean_lines = [line for line in lines if line]
    return "\n\n".join(clean_lines)

def chunk_text(text: str, chunk_size: int = 700, chunk_overlap: int = 150) -> List[str]:
    """
    Split text into overlapping chunks using paragraph or sentence boundaries where possible.
    Beginner-friendly recursive sliding window chunker.
    """
    if not text or not text.strip():
        return []

    cleaned = clean_text(text)
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks = []
    start = 0
    text_len = len(cleaned)

    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            chunk = cleaned[start:text_len].strip()
            if chunk:
                chunks.append(chunk)
            break

        # Attempt to split at a natural sentence or newline boundary
        split_point = -1
        # Search backward for paragraph break
        para_break = cleaned.rfind("\n\n", start, end)
        if para_break != -1 and para_break > start + chunk_overlap:
            split_point = para_break + 2
        else:
            # Search backward for period or question mark
            period_break = max(
                cleaned.rfind(". ", start, end),
                cleaned.rfind("? ", start, end),
                cleaned.rfind("! ", start, end)
            )
            if period_break != -1 and period_break > start + chunk_overlap:
                split_point = period_break + 2
            else:
                # Search backward for single newline
                newline_break = cleaned.rfind("\n", start, end)
                if newline_break != -1 and newline_break > start + chunk_overlap:
                    split_point = newline_break + 1
                else:
                    # Search backward for space
                    space_break = cleaned.rfind(" ", start, end)
                    if space_break != -1 and space_break > start + chunk_overlap:
                        split_point = space_break + 1
                    else:
                        split_point = end

        chunk = cleaned[start:split_point].strip()
        if chunk:
            chunks.append(chunk)

        # Move forward, respecting overlap
        start = max(split_point - chunk_overlap, start + 1)

    return chunks

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0

    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    return dot / (norm1 * norm2)
