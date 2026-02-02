"""
SQLite database connection and CRUD operations for Local Transcript App
"""
import aiosqlite
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from models import JobStatus, JobType, ModelSize, TranscriptSegment

logger = logging.getLogger(__name__)

# Database path - always under data directory
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DB_PATH = DATA_DIR / "transcript.db"

# Ensure data directories exist
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"


async def init_db():
    """Initialize database and create tables if they don't exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Jobs table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL DEFAULT 'file_upload',
                source_url TEXT,
                original_filename TEXT,
                stored_filename TEXT,
                status TEXT NOT NULL DEFAULT 'queued',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                model TEXT NOT NULL DEFAULT 'small',
                language TEXT NOT NULL DEFAULT 'auto',
                error_message TEXT
            )
        """)
        
        # Transcripts table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transcripts (
                job_id TEXT PRIMARY KEY,
                segments_json_path TEXT,
                plain_text_path TEXT,
                srt_path TEXT,
                vtt_path TEXT,
                edited_text TEXT,
                edited_segments_json TEXT,
                last_edited_at TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            )
        """)
        
        await db.commit()
        logger.info(f"Database initialized at {DB_PATH}")


async def get_db():
    """Get database connection (for FastAPI dependency injection)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


# ----- Job CRUD -----

async def create_job(
    db: aiosqlite.Connection,
    job_type: JobType,
    model: ModelSize = ModelSize.SMALL,
    language: str = "auto",
    original_filename: Optional[str] = None,
    stored_filename: Optional[str] = None,
    source_url: Optional[str] = None,
) -> str:
    """Create a new job and return its ID"""
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    await db.execute("""
        INSERT INTO jobs (id, job_type, source_url, original_filename, stored_filename, 
                         status, created_at, updated_at, model, language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (job_id, job_type.value, source_url, original_filename, stored_filename,
          JobStatus.QUEUED.value, now, now, model.value, language))
    await db.commit()
    
    logger.info(f"Created job {job_id} (type={job_type.value})")
    return job_id


async def get_job(db: aiosqlite.Connection, job_id: str) -> Optional[dict]:
    """Get a single job by ID"""
    async with db.execute(
        "SELECT * FROM jobs WHERE id = ?", (job_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            return dict(row)
    return None


async def list_jobs(
    db: aiosqlite.Connection,
    limit: int = 100,
    offset: int = 0,
    status: Optional[JobStatus] = None
) -> list[dict]:
    """List jobs with optional filtering"""
    query = "SELECT * FROM jobs"
    params = []
    
    if status:
        query += " WHERE status = ?"
        params.append(status.value)
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    async with db.execute(query, params) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_job_status(
    db: aiosqlite.Connection,
    job_id: str,
    status: JobStatus,
    error_message: Optional[str] = None
) -> bool:
    """Update job status"""
    now = datetime.utcnow().isoformat()
    
    if error_message:
        await db.execute("""
            UPDATE jobs SET status = ?, updated_at = ?, error_message = ? WHERE id = ?
        """, (status.value, now, error_message, job_id))
    else:
        await db.execute("""
            UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?
        """, (status.value, now, job_id))
    
    await db.commit()
    return True


# ----- Transcript CRUD -----

async def create_transcript_record(
    db: aiosqlite.Connection,
    job_id: str,
    segments_json_path: str,
    plain_text_path: str,
    srt_path: str,
    vtt_path: str,
) -> bool:
    """Create transcript record after worker completes"""
    await db.execute("""
        INSERT INTO transcripts (job_id, segments_json_path, plain_text_path, srt_path, vtt_path)
        VALUES (?, ?, ?, ?, ?)
    """, (job_id, segments_json_path, plain_text_path, srt_path, vtt_path))
    await db.commit()
    return True


async def get_transcript(db: aiosqlite.Connection, job_id: str) -> Optional[dict]:
    """Get transcript record for a job"""
    async with db.execute(
        "SELECT * FROM transcripts WHERE job_id = ?", (job_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            return dict(row)
    return None


async def save_transcript_edits(
    db: aiosqlite.Connection,
    job_id: str,
    edited_text: str,
    edited_segments: Optional[list[dict]] = None
) -> bool:
    """Save user edits to transcript"""
    now = datetime.utcnow().isoformat()
    segments_json = json.dumps(edited_segments) if edited_segments else None
    
    # Check if transcript exists
    existing = await get_transcript(db, job_id)
    
    if existing:
        await db.execute("""
            UPDATE transcripts 
            SET edited_text = ?, edited_segments_json = ?, last_edited_at = ?
            WHERE job_id = ?
        """, (edited_text, segments_json, now, job_id))
    else:
        # Create record with just edits (for captions-only jobs)
        await db.execute("""
            INSERT INTO transcripts (job_id, edited_text, edited_segments_json, last_edited_at)
            VALUES (?, ?, ?, ?)
        """, (job_id, edited_text, segments_json, now))
    
    await db.commit()
    logger.info(f"Saved transcript edits for job {job_id}")
    return True


# ----- Utility Functions -----

def get_job_output_dir(job_id: str) -> Path:
    """Get output directory for a job (safe path)"""
    # Sanitize job_id to prevent path traversal
    safe_id = "".join(c for c in job_id if c.isalnum() or c == "-")
    return OUTPUTS_DIR / safe_id


async def load_transcript_segments(job_id: str) -> list[TranscriptSegment]:
    """Load transcript segments from file"""
    output_dir = get_job_output_dir(job_id)
    segments_path = output_dir / "segments.json"
    
    if not segments_path.exists():
        return []
    
    with open(segments_path, "r") as f:
        data = json.load(f)
    
    return [TranscriptSegment(**seg) for seg in data]


async def load_transcript_text(job_id: str) -> str:
    """Load plain text transcript from file"""
    output_dir = get_job_output_dir(job_id)
    text_path = output_dir / "transcript.txt"
    
    if not text_path.exists():
        return ""
    
    with open(text_path, "r") as f:
        return f.read()


def get_safe_upload_path(filename: str) -> Path:
    """
    Generate safe upload path. 
    NEVER uses user-provided paths - only sanitized filename.
    """
    # Extract just the filename (remove any path components)
    basename = os.path.basename(filename)
    
    # Remove potentially dangerous characters
    safe_name = "".join(c for c in basename if c.isalnum() or c in ".-_")
    
    # Ensure it's not empty
    if not safe_name:
        safe_name = "upload"
    
    # Add UUID prefix to prevent collisions
    unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    
    return UPLOADS_DIR / unique_name
