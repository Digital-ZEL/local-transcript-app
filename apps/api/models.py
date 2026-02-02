"""
Pydantic models for Local Transcript App API
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator
import re


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class JobType(str, Enum):
    FILE_UPLOAD = "file_upload"
    YOUTUBE_CAPTIONS = "youtube_captions"
    YOUTUBE_AUTO_INGEST = "youtube_auto_ingest"


class ModelSize(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class ExportFormat(str, Enum):
    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"
    JSON = "json"


class YouTubeMode(str, Enum):
    SAFE = "safe"
    AUTO = "auto"


# ----- Request Models -----

class UploadParams(BaseModel):
    """Optional parameters for file upload"""
    model: ModelSize = ModelSize.SMALL
    language: str = Field(default="auto", max_length=10)


class YouTubeRequest(BaseModel):
    """Request body for YouTube URL intake"""
    url: str
    mode: YouTubeMode = YouTubeMode.SAFE
    model: ModelSize = ModelSize.SMALL
    language: str = Field(default="auto", max_length=10)

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        """Strict allowlist: only youtube.com and youtu.be"""
        youtube_patterns = [
            r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
            r'^https?://(www\.)?youtube\.com/shorts/[\w-]+',
            r'^https?://youtu\.be/[\w-]+',
            r'^https?://(www\.)?youtube\.com/embed/[\w-]+',
        ]
        if not any(re.match(pattern, v) for pattern in youtube_patterns):
            raise ValueError("Invalid YouTube URL. Only youtube.com and youtu.be links are allowed.")
        return v


class TranscriptSegment(BaseModel):
    """A single segment of transcript with timing"""
    id: int
    start: float  # seconds
    end: float    # seconds
    text: str


class TranscriptEditRequest(BaseModel):
    """Request body for saving transcript edits"""
    text: str
    segments: Optional[list[TranscriptSegment]] = None


# ----- Response Models -----

class JobCreateResponse(BaseModel):
    """Response when a job is created"""
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    message: str = "Job created successfully"


class JobSummary(BaseModel):
    """Summary of a job for list view"""
    id: str
    job_type: JobType
    original_filename: Optional[str] = None
    source_url: Optional[str] = None
    status: JobStatus
    created_at: datetime
    model: ModelSize
    language: str


class JobDetail(BaseModel):
    """Full job details"""
    id: str
    job_type: JobType
    original_filename: Optional[str] = None
    stored_filename: Optional[str] = None
    source_url: Optional[str] = None
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    model: ModelSize
    language: str
    error_message: Optional[str] = None


class TranscriptResponse(BaseModel):
    """Transcript data response"""
    job_id: str
    text: str
    segments: list[TranscriptSegment]
    edited: bool = False
    last_edited_at: Optional[datetime] = None


class TranscriptEditResponse(BaseModel):
    """Response after saving transcript edits"""
    ok: bool = True
    message: str = "Transcript saved"


class YouTubeInfoResponse(BaseModel):
    """Response for YouTube safe mode when captions unavailable"""
    job_id: Optional[str] = None
    has_captions: bool = False
    title: Optional[str] = None
    duration_seconds: Optional[int] = None
    message: str
    fallback_options: list[str] = []


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "ok"
    service: str = "local-transcript-api"
    version: str = "1.0.0"
