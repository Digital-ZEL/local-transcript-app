"""
Export endpoints for Local Transcript App
Supports TXT, SRT, VTT, JSON formats
"""
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, Response

import database as db
from models import ErrorResponse, ExportFormat, JobStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["export"])


def format_timestamp_srt(seconds: float) -> str:
    """Format seconds to SRT timestamp: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """Format seconds to VTT timestamp: HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def segments_to_srt(segments: list[dict]) -> str:
    """Convert segments to SRT format"""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp_srt(seg['start'])
        end = format_timestamp_srt(seg['end'])
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(seg['text'])
        lines.append("")
    return "\n".join(lines)


def segments_to_vtt(segments: list[dict]) -> str:
    """Convert segments to VTT format"""
    lines = ["WEBVTT", ""]
    for i, seg in enumerate(segments, 1):
        start = format_timestamp_vtt(seg['start'])
        end = format_timestamp_vtt(seg['end'])
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(seg['text'])
        lines.append("")
    return "\n".join(lines)


@router.get(
    "/{job_id}/export",
    responses={
        200: {"description": "File download"},
        404: {"model": ErrorResponse, "description": "Job or transcript not found"},
        409: {"model": ErrorResponse, "description": "Transcript not ready"},
    },
    summary="Export transcript",
)
async def export_transcript(
    job_id: str,
    fmt: ExportFormat = Query(default=ExportFormat.TXT, alias="fmt"),
):
    """
    Export transcript in the specified format.
    
    - **fmt**: Export format (txt, srt, vtt, json)
    
    Returns the transcript as a downloadable file.
    Uses edited version if available.
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
        
        # Determine filename base
        original_name = job.get("original_filename", "transcript")
        if original_name:
            # Remove extension from original filename
            base_name = Path(original_name).stem
        else:
            base_name = f"transcript_{job_id[:8]}"
        
        # Load data (prefer edited version)
        if transcript and transcript.get("edited_segments_json"):
            segments = json.loads(transcript["edited_segments_json"])
        else:
            segments = [seg.model_dump() for seg in await db.load_transcript_segments(job_id)]
        
        if transcript and transcript.get("edited_text"):
            text = transcript["edited_text"]
        else:
            text = await db.load_transcript_text(job_id)
        
        if not segments and not text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript data not found"
            )
        
        # Generate export content
        if fmt == ExportFormat.TXT:
            content = text or " ".join(seg["text"] for seg in segments)
            media_type = "text/plain"
            filename = f"{base_name}.txt"
        
        elif fmt == ExportFormat.SRT:
            if not segments:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SRT export requires segment data with timestamps"
                )
            content = segments_to_srt(segments)
            media_type = "application/x-subrip"
            filename = f"{base_name}.srt"
        
        elif fmt == ExportFormat.VTT:
            if not segments:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="VTT export requires segment data with timestamps"
                )
            content = segments_to_vtt(segments)
            media_type = "text/vtt"
            filename = f"{base_name}.vtt"
        
        elif fmt == ExportFormat.JSON:
            export_data = {
                "job_id": job_id,
                "original_filename": job.get("original_filename"),
                "source_url": job.get("source_url"),
                "text": text,
                "segments": segments,
                "model": job.get("model"),
                "language": job.get("language"),
            }
            content = json.dumps(export_data, indent=2, ensure_ascii=False)
            media_type = "application/json"
            filename = f"{base_name}.json"
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {fmt}"
            )
        
        logger.info(f"Exported job {job_id} as {fmt.value}")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
