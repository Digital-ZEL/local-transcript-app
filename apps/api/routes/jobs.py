"""
Job management endpoints for Local Transcript App
"""
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

import database as db
from models import (
    ErrorResponse,
    JobDetail,
    JobStatus,
    JobSummary,
    JobType,
    ModelSize,
    TranscriptEditRequest,
    TranscriptEditResponse,
    TranscriptResponse,
    TranscriptSegment,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def row_to_job_summary(row: dict) -> JobSummary:
    """Convert database row to JobSummary model"""
    return JobSummary(
        id=row["id"],
        job_type=JobType(row["job_type"]),
        original_filename=row["original_filename"],
        source_url=row["source_url"],
        status=JobStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        model=ModelSize(row["model"]),
        language=row["language"],
    )


def row_to_job_detail(row: dict) -> JobDetail:
    """Convert database row to JobDetail model"""
    return JobDetail(
        id=row["id"],
        job_type=JobType(row["job_type"]),
        original_filename=row["original_filename"],
        stored_filename=row["stored_filename"],
        source_url=row["source_url"],
        status=JobStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        model=ModelSize(row["model"]),
        language=row["language"],
        error_message=row["error_message"],
    )


@router.get(
    "",
    response_model=list[JobSummary],
    summary="List all jobs",
)
async def list_jobs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[JobStatus] = Query(default=None, alias="status"),
):
    """
    List all transcription jobs with optional filtering.
    
    - **limit**: Max number of jobs to return (1-500)
    - **offset**: Pagination offset
    - **status**: Filter by status (queued, running, done, failed)
    """
    async for conn in db.get_db():
        jobs = await db.list_jobs(conn, limit=limit, offset=offset, status=status_filter)
        return [row_to_job_summary(job) for job in jobs]


@router.get(
    "/{job_id}",
    response_model=JobDetail,
    responses={404: {"model": ErrorResponse}},
    summary="Get job details",
)
async def get_job(job_id: str):
    """
    Get detailed information about a specific job.
    
    - **job_id**: UUID of the job
    """
    async for conn in db.get_db():
        job = await db.get_job(conn, job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        return row_to_job_detail(job)


@router.get(
    "/{job_id}/transcript",
    response_model=TranscriptResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job or transcript not found"},
        409: {"model": ErrorResponse, "description": "Transcript not ready"},
    },
    summary="Get transcript for a job",
)
async def get_transcript(job_id: str):
    """
    Get the transcript text and segments for a completed job.
    
    Returns edited version if available, otherwise original.
    """
    async for conn in db.get_db():
        # Check job exists and is done
        job = await db.get_job(conn, job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job["status"] != JobStatus.DONE.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Transcript not ready. Job status: {job['status']}"
            )
        
        # Get transcript record
        transcript = await db.get_transcript(conn, job_id)
        
        # Check for edited version first
        if transcript and transcript.get("edited_text"):
            text = transcript["edited_text"]
            edited = True
            last_edited = datetime.fromisoformat(transcript["last_edited_at"]) if transcript.get("last_edited_at") else None
            
            # Load edited segments if available
            if transcript.get("edited_segments_json"):
                segments_data = json.loads(transcript["edited_segments_json"])
                segments = [TranscriptSegment(**seg) for seg in segments_data]
            else:
                # Fall back to original segments
                segments = await db.load_transcript_segments(job_id)
        else:
            # Load original transcript
            text = await db.load_transcript_text(job_id)
            segments = await db.load_transcript_segments(job_id)
            edited = False
            last_edited = None
        
        if not text and not segments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript files not found"
            )
        
        return TranscriptResponse(
            job_id=job_id,
            text=text,
            segments=segments,
            edited=edited,
            last_edited_at=last_edited,
        )


@router.post(
    "/{job_id}/transcript",
    response_model=TranscriptEditResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Job not completed"},
    },
    summary="Save transcript edits",
)
async def save_transcript(job_id: str, request: TranscriptEditRequest):
    """
    Save user edits to the transcript.
    
    - **text**: Full edited transcript text
    - **segments**: Optional list of edited segments with timings
    """
    async for conn in db.get_db():
        # Verify job exists
        job = await db.get_job(conn, job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job["status"] != JobStatus.DONE.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot edit transcript for incomplete job"
            )
        
        # Save edits
        segments_data = [seg.model_dump() for seg in request.segments] if request.segments else None
        await db.save_transcript_edits(conn, job_id, request.text, segments_data)
        
        logger.info(f"Saved transcript edits for job {job_id}")
        return TranscriptEditResponse(ok=True, message="Transcript saved successfully")
