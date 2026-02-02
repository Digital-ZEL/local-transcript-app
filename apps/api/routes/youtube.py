"""
YouTube URL intake endpoints for Local Transcript App

Supports two modes:
- Safe Mode (v1.5): Try to get existing captions, fallback to upload guidance
- Auto Mode (v2): Download and transcribe (requires YOUTUBE_AUTO_INGEST=true)
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

import database as db
from models import (
    ErrorResponse,
    JobCreateResponse,
    JobType,
    ModelSize,
    YouTubeInfoResponse,
    YouTubeMode,
    YouTubeRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["youtube"])

# Feature flags
YOUTUBE_AUTO_INGEST_ENABLED = os.getenv("YOUTUBE_AUTO_INGEST", "false").lower() == "true"

# Duration limit for auto-ingest (in seconds) - default 2 hours
MAX_DURATION_SECONDS = int(os.getenv("YOUTUBE_MAX_DURATION_SECONDS", "7200"))


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


async def get_video_info(url: str) -> dict:
    """
    Get video metadata using yt-dlp (no download).
    Returns title, duration, whether captions exist.
    """
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Check for available captions
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            has_manual_captions = bool(subtitles)
            has_auto_captions = bool(automatic_captions)
            
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'has_manual_captions': has_manual_captions,
                'has_auto_captions': has_auto_captions,
                'available_caption_langs': list(subtitles.keys()) + list(automatic_captions.keys()),
                'video_id': info.get('id'),
            }
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch video info: {str(e)}"
        )


async def fetch_captions(url: str, lang: str = "en") -> Optional[str]:
    """
    Fetch existing captions from YouTube (if available).
    Tries manual captions first, then auto-generated.
    """
    try:
        import yt_dlp
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = os.path.join(tmpdir, '%(id)s')
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': [lang, 'en'],
                'subtitlesformat': 'vtt',
                'outtmpl': output_template,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Look for downloaded caption files
            for f in Path(tmpdir).glob('*.vtt'):
                with open(f, 'r') as caption_file:
                    return caption_file.read()
        
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch captions: {e}")
        return None


def parse_vtt_to_segments(vtt_content: str) -> list[dict]:
    """Parse VTT content to segments with timings"""
    segments = []
    lines = vtt_content.strip().split('\n')
    
    i = 0
    segment_id = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for timestamp line (00:00:00.000 --> 00:00:05.000)
        if '-->' in line:
            times = line.split('-->')
            if len(times) == 2:
                start_str = times[0].strip()
                end_str = times[1].strip().split()[0]  # Remove positioning info
                
                # Parse timestamps
                start = parse_vtt_timestamp(start_str)
                end = parse_vtt_timestamp(end_str)
                
                # Collect text lines until empty line
                i += 1
                text_lines = []
                while i < len(lines) and lines[i].strip():
                    # Remove VTT formatting tags
                    text = re.sub(r'<[^>]+>', '', lines[i].strip())
                    if text:
                        text_lines.append(text)
                    i += 1
                
                if text_lines:
                    segments.append({
                        'id': segment_id,
                        'start': start,
                        'end': end,
                        'text': ' '.join(text_lines),
                    })
                    segment_id += 1
        i += 1
    
    return segments


def parse_vtt_timestamp(ts: str) -> float:
    """Convert VTT timestamp to seconds"""
    parts = ts.replace(',', '.').split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return 0.0


@router.post(
    "/youtube",
    response_model=JobCreateResponse | YouTubeInfoResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid URL or fetch failed"},
        403: {"model": ErrorResponse, "description": "Auto mode disabled"},
        422: {"model": ErrorResponse, "description": "Video too long"},
    },
    summary="Process YouTube URL",
)
async def process_youtube_url(request: YouTubeRequest):
    """
    Process a YouTube URL for transcription.
    
    **Safe Mode (default):**
    - Attempts to fetch existing captions
    - If captions found, creates a job with caption data
    - If not, returns guidance for alternatives (upload, paste)
    
    **Auto Mode (requires YOUTUBE_AUTO_INGEST=true):**
    - Downloads audio and queues for local transcription
    - Subject to duration limits
    """
    video_id = extract_video_id(request.url)
    if not video_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract video ID from URL"
        )
    
    # Get video info
    info = await get_video_info(request.url)
    
    if request.mode == YouTubeMode.SAFE:
        return await handle_safe_mode(request, info)
    elif request.mode == YouTubeMode.AUTO:
        return await handle_auto_mode(request, info)


async def handle_safe_mode(request: YouTubeRequest, info: dict) -> JobCreateResponse | YouTubeInfoResponse:
    """Handle Safe Link Mode - try captions, fallback to guidance"""
    
    has_captions = info['has_manual_captions'] or info['has_auto_captions']
    
    if has_captions:
        # Try to fetch captions
        lang = request.language if request.language != "auto" else "en"
        captions = await fetch_captions(request.url, lang)
        
        if captions:
            # Parse captions to segments
            segments = parse_vtt_to_segments(captions)
            text = ' '.join(seg['text'] for seg in segments)
            
            # Create job and save captions directly
            async for conn in db.get_db():
                job_id = await db.create_job(
                    conn,
                    job_type=JobType.YOUTUBE_CAPTIONS,
                    model=request.model,
                    language=lang,
                    source_url=request.url,
                    original_filename=f"{info['title']}.vtt",
                )
                
                # Create output directory and save transcript files
                output_dir = db.get_job_output_dir(job_id)
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Save segments
                with open(output_dir / "segments.json", "w") as f:
                    json.dump(segments, f, indent=2)
                
                # Save plain text
                with open(output_dir / "transcript.txt", "w") as f:
                    f.write(text)
                
                # Save original VTT
                with open(output_dir / "transcript.vtt", "w") as f:
                    f.write(captions)
                
                # Create transcript record and mark job done
                await db.create_transcript_record(
                    conn, job_id,
                    segments_json_path=str(output_dir / "segments.json"),
                    plain_text_path=str(output_dir / "transcript.txt"),
                    srt_path="",  # Will generate on export
                    vtt_path=str(output_dir / "transcript.vtt"),
                )
                await db.update_job_status(conn, job_id, db.JobStatus.DONE)
                
                logger.info(f"Created caption job {job_id} for {request.url}")
                
                return JobCreateResponse(
                    job_id=job_id,
                    message=f"Captions retrieved successfully from YouTube ({len(segments)} segments)"
                )
    
    # No captions available - return guidance
    return YouTubeInfoResponse(
        has_captions=False,
        title=info['title'],
        duration_seconds=info['duration'],
        message="No captions available for this video",
        fallback_options=[
            "Upload the audio/video file directly",
            "Download the video yourself and upload it",
            "Paste captions manually if you have them",
        ]
    )


async def handle_auto_mode(request: YouTubeRequest, info: dict) -> JobCreateResponse:
    """Handle Auto Ingest Mode - download and transcribe"""
    
    # Check if auto mode is enabled
    if not YOUTUBE_AUTO_INGEST_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auto Ingest Mode is disabled. Set YOUTUBE_AUTO_INGEST=true to enable."
        )
    
    # Check duration limit
    if info['duration'] > MAX_DURATION_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Video too long ({info['duration']}s). Maximum: {MAX_DURATION_SECONDS}s"
        )
    
    # Create job for worker to process
    async for conn in db.get_db():
        job_id = await db.create_job(
            conn,
            job_type=JobType.YOUTUBE_AUTO_INGEST,
            model=request.model,
            language=request.language,
            source_url=request.url,
            original_filename=f"{info['title']}",
        )
        
        logger.info(f"Created auto-ingest job {job_id} for {request.url}")
        
        return JobCreateResponse(
            job_id=job_id,
            message=f"Auto ingest queued. Video: {info['title']} ({info['duration']}s)"
        )
