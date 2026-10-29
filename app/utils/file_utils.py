import os
import re
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from backend.app.config import settings

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and invalid characters."""
    # Strip paths
    base_name = os.path.basename(filename)
    # Remove any character that is not alphanumeric, dot, dash, or underscore
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', base_name)
    if not clean_name:
        clean_name = f"file_{uuid.uuid4().hex[:8]}"
    return clean_name

def get_file_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext.lower()

def determine_file_category(filename: str) -> str:
    ext = get_file_extension(filename)
    if ext in settings.ALLOWED_IMAGE_EXTENSIONS:
        return "image"
    elif ext in settings.ALLOWED_DOC_EXTENSIONS:
        return "document"
    elif ext in settings.ALLOWED_AUDIO_EXTENSIONS:
        return "audio"
    else:
        return "unsupported"

async def save_upload_file(upload_file: UploadFile, category: str = "document") -> tuple[str, str, int]:
    """
    Saves an uploaded file to the appropriate folder.
    Returns: (sanitized_filename, relative_file_path, file_size_in_bytes)
    """
    sanitized = sanitize_filename(upload_file.filename)
    unique_prefix = uuid.uuid4().hex[:8]
    unique_filename = f"{unique_prefix}_{sanitized}"

    folder_map = {
        "image": "images",
        "document": "documents",
        "audio": "audio"
    }
    subfolder = folder_map.get(category, "documents")
    target_dir = os.path.join(settings.UPLOAD_DIR, subfolder)
    os.makedirs(target_dir, exist_ok=True)

    dest_path = os.path.join(target_dir, unique_filename)

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    total_size = 0

    async with aiofiles.open(dest_path, "wb") as out_file:
        while content := await upload_file.read(1024 * 64):  # 64KB chunks
            total_size += len(content)
            if total_size > max_bytes:
                await out_file.close()
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
                )
            await out_file.write(content)

    return sanitized, dest_path.replace("\\", "/"), total_size
