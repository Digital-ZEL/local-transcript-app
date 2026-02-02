"""
File upload endpoint for Local Transcript App
"""
import logging
import os
from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

import database as db
from models import JobCreateResponse, JobType, ModelSize, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])

# ----- Configuration -----

# Allowed file types (MIME type -> extensions)
ALLOWED_TYPES = {
    # Audio
    "audio/mpeg": [".mp3"],
    "audio/mp3": [".mp3"],
    "audio/wav": [".wav"],
    "audio/x-wav": [".wav"],
    "audio/wave": [".wav"],
    "audio/flac": [".flac"],
    "audio/x-flac": [".flac"],
    "audio/ogg": [".ogg"],
    "audio/x-m4a": [".m4a"],
    "audio/mp4": [".m4a"],
    "audio/aac": [".aac"],
    "audio/webm": [".webm"],
    # Video
    "video/mp4": [".mp4"],
    "video/mpeg": [".mpeg", ".mpg"],
    "video/webm": [".webm"],
    "video/x-matroska": [".mkv"],
    "video/quicktime": [".mov"],
    "video/x-msvideo": [".avi"],
}

# Allowed extensions (for additional validation)
ALLOWED_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".webm",
    ".mp4", ".mpeg", ".mpg", ".mkv", ".mov", ".avi"
}

# Max file size: 2GB (configurable via env)
MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE_MB", "2048")) * 1024 * 1024


def validate_file_type(filename: str, content_type: str) -> bool:
    """
    Validate file type against allowlist.
    Checks both MIME type and extension.
    """
    ext = Path(filename).suffix.lower()
    
    # Check extension
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Rejected file: extension {ext} not allowed")
        return False
    
    # Check MIME type if provided
    if content_type and content_type != "application/octet-stream":
        if content_type not in ALLOWED_TYPES:
            logger.warning(f"Rejected file: MIME type {content_type} not allowed")
            return False
    
    return True


@router.post(
    "/upload",
    response_model=JobCreateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        413: {"model": ErrorResponse, "description": "File too large"},
        415: {"model": ErrorResponse, "description": "Unsupported media type"},
    },
)
async def upload_file(
    file: Annotated[UploadFile, File(description="Audio or video file to transcribe")],
    model: Annotated[ModelSize, Form()] = ModelSize.SMALL,
    language: Annotated[str, Form()] = "auto",
    conn: aiofiles.base.AiofilesContextManager = Depends(db.get_db),
):
    """
    Upload an audio/video file for transcription.
    
    - **file**: Audio or video file (mp3, wav, mp4, etc.)
    - **model**: Whisper model size (tiny, base, small, medium, large)
    - **language**: Language code or 'auto' for detection
    
    Returns job_id for tracking transcription progress.
    """
    # Validate filename exists
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    # Validate file type
    if not validate_file_type(file.filename, file.content_type or ""):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    
    # Get safe upload path (NEVER uses user paths)
    upload_path = db.get_safe_upload_path(file.filename)
    
    # Stream file to disk with size check
    total_size = 0
    try:
        async with aiofiles.open(upload_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    # Clean up partial file
                    await f.close()
                    upload_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
                    )
                await f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save upload: {e}")
        upload_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )
    
    logger.info(f"Saved upload: {upload_path} ({total_size} bytes)")
    
    # Create job in database
    async for conn in db.get_db():
        job_id = await db.create_job(
            conn,
            job_type=JobType.FILE_UPLOAD,
            model=model,
            language=language,
            original_filename=file.filename,
            stored_filename=upload_path.name,
        )
        break
    
    return JobCreateResponse(
        job_id=job_id,
        message=f"File uploaded successfully. Transcription queued with model={model.value}"
    )
