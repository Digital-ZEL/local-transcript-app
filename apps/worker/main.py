"""
Worker Main — Job polling and processing loop
==============================================
The worker service that:
1. Polls for queued jobs from the database
2. Processes jobs based on type (file_upload, youtube_captions, youtube_auto_ingest)
3. Updates job status (running → done/failed)
4. Generates transcript outputs

Run with: python main.py
"""

import os
import sys
import time
import logging
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Local imports
from audio_processor import AudioProcessor, AudioProcessorError
from transcriber import Transcriber, TranscriberError, TranscriptSegment
from youtube_handler import (
    YouTubeHandler, 
    YouTubeHandlerError,
    YouTubeNoCaptionsError,
    YouTubeDurationExceededError
)
from output_formatter import OutputFormatter, Segment

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("worker")

# Configuration from environment
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/transcripts.db")
DATA_DIR = Path(os.environ.get("DATA_DIR", "./data"))
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"

# Worker settings
POLL_INTERVAL = int(os.environ.get("WORKER_POLL_INTERVAL", "5"))
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "auto")

# YouTube settings
YOUTUBE_AUTO_INGEST_ENABLED = os.environ.get("YOUTUBE_AUTO_INGEST", "false").lower() == "true"
YOUTUBE_MAX_DURATION = int(os.environ.get("YOUTUBE_MAX_DURATION", "3600"))  # 1 hour
YOUTUBE_MAX_SIZE_MB = int(os.environ.get("YOUTUBE_MAX_SIZE_MB", "500"))

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


class WorkerShutdown(Exception):
    """Raised when worker receives shutdown signal."""
    pass


class Worker:
    """
    Job processing worker.
    
    Handles three job types:
    1. file_upload: Local file → normalize → transcribe → outputs
    2. youtube_captions: YouTube URL → fetch captions → outputs
    3. youtube_auto_ingest: YouTube URL → download → normalize → transcribe → outputs
    """
    
    def __init__(self):
        # Database connection
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        
        # Processing components (lazy-loaded)
        self._audio_processor = None
        self._transcriber = None
        self._youtube_handler = None
        
        # Shutdown flag
        self.running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    @property
    def audio_processor(self) -> AudioProcessor:
        """Lazy-load audio processor."""
        if self._audio_processor is None:
            self._audio_processor = AudioProcessor()
        return self._audio_processor
    
    @property
    def transcriber(self) -> Transcriber:
        """Lazy-load transcriber."""
        if self._transcriber is None:
            self._transcriber = Transcriber(
                model_size=WHISPER_MODEL,
                device=WHISPER_DEVICE
            )
        return self._transcriber
    
    @property
    def youtube_handler(self) -> YouTubeHandler:
        """Lazy-load YouTube handler."""
        if self._youtube_handler is None:
            self._youtube_handler = YouTubeHandler(
                max_duration_seconds=YOUTUBE_MAX_DURATION,
                max_file_size_mb=YOUTUBE_MAX_SIZE_MB,
                download_dir=str(DATA_DIR / "youtube_temp")
            )
        return self._youtube_handler
    
    def get_next_job(self) -> Optional[dict]:
        """
        Poll database for next queued job.
        
        Returns job dict or None if no jobs available.
        """
        with self.Session() as session:
            # Get oldest queued job
            result = session.execute(text("""
                SELECT id, job_type, source_url, original_filename, stored_filename,
                       model, language
                FROM jobs 
                WHERE status = 'queued'
                ORDER BY created_at ASC
                LIMIT 1
            """))
            
            row = result.fetchone()
            if row is None:
                return None
            
            return {
                "id": row[0],
                "job_type": row[1],
                "source_url": row[2],
                "original_filename": row[3],
                "stored_filename": row[4],
                "model": row[5] or WHISPER_MODEL,
                "language": row[6]
            }
    
    def update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Update job status in database."""
        with self.Session() as session:
            if error_message:
                session.execute(text("""
                    UPDATE jobs 
                    SET status = :status, 
                        error_message = :error,
                        updated_at = :now
                    WHERE id = :id
                """), {
                    "status": status,
                    "error": error_message[:1000],  # Truncate long errors
                    "now": datetime.utcnow().isoformat(),
                    "id": job_id
                })
            else:
                session.execute(text("""
                    UPDATE jobs 
                    SET status = :status,
                        updated_at = :now
                    WHERE id = :id
                """), {
                    "status": status,
                    "now": datetime.utcnow().isoformat(),
                    "id": job_id
                })
            session.commit()
        
        logger.info(f"Job {job_id}: status → {status}")
    
    def save_transcript_paths(
        self,
        job_id: str,
        paths: dict
    ) -> None:
        """Save transcript file paths to database."""
        with self.Session() as session:
            # Check if transcript record exists
            result = session.execute(text(
                "SELECT job_id FROM transcripts WHERE job_id = :id"
            ), {"id": job_id})
            
            if result.fetchone():
                # Update existing
                session.execute(text("""
                    UPDATE transcripts
                    SET segments_json_path = :json,
                        plain_text_path = :txt,
                        srt_path = :srt,
                        vtt_path = :vtt
                    WHERE job_id = :id
                """), {
                    "json": paths.get("json"),
                    "txt": paths.get("txt"),
                    "srt": paths.get("srt"),
                    "vtt": paths.get("vtt"),
                    "id": job_id
                })
            else:
                # Insert new
                session.execute(text("""
                    INSERT INTO transcripts 
                    (job_id, segments_json_path, plain_text_path, srt_path, vtt_path)
                    VALUES (:id, :json, :txt, :srt, :vtt)
                """), {
                    "id": job_id,
                    "json": paths.get("json"),
                    "txt": paths.get("txt"),
                    "srt": paths.get("srt"),
                    "vtt": paths.get("vtt")
                })
            
            session.commit()
    
    def process_file_upload(self, job: dict) -> dict:
        """
        Process a file upload job.
        
        Flow: stored file → normalize audio → transcribe → generate outputs
        """
        job_id = job["id"]
        stored_filename = job["stored_filename"]
        model = job["model"]
        language = job.get("language")
        
        # Setup paths
        input_path = UPLOADS_DIR / stored_filename
        job_output_dir = OUTPUTS_DIR / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)
        
        normalized_path = job_output_dir / "audio_normalized.wav"
        
        if not input_path.exists():
            raise FileNotFoundError(f"Uploaded file not found: {input_path}")
        
        # Step 1: Normalize audio
        logger.info(f"[{job_id}] Normalizing audio...")
        self.audio_processor.normalize_audio(
            str(input_path),
            str(normalized_path)
        )
        
        # Step 2: Transcribe
        logger.info(f"[{job_id}] Transcribing with model={model}...")
        
        # Use job-specific model if different from default
        if model != WHISPER_MODEL:
            transcriber = Transcriber(model_size=model, device=WHISPER_DEVICE)
        else:
            transcriber = self.transcriber
        
        result = transcriber.transcribe(
            str(normalized_path),
            language=language
        )
        
        # Step 3: Generate outputs
        logger.info(f"[{job_id}] Generating outputs...")
        
        segments = [
            Segment(start=s.start, end=s.end, text=s.text)
            for s in result.segments
        ]
        
        formatter = OutputFormatter(str(job_output_dir))
        paths = formatter.generate_all(
            segments,
            metadata={
                "job_id": job_id,
                "model": model,
                "language": result.language,
                "language_probability": result.language_probability,
                "duration": result.duration,
                "original_filename": job.get("original_filename")
            }
        )
        
        # Cleanup normalized audio (keep only transcripts)
        try:
            normalized_path.unlink()
        except Exception:
            pass
        
        return paths
    
    def process_youtube_captions(self, job: dict) -> dict:
        """
        Process YouTube captions job (Safe Link Mode).
        
        Flow: URL → fetch captions → convert to segments → generate outputs
        """
        job_id = job["id"]
        source_url = job["source_url"]
        
        if not source_url:
            raise ValueError("YouTube job missing source_url")
        
        # Setup output directory
        job_output_dir = OUTPUTS_DIR / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Fetch captions
        logger.info(f"[{job_id}] Fetching captions from YouTube...")
        
        language = job.get("language") or "en"
        caption_segments = self.youtube_handler.fetch_captions(
            source_url,
            language=language
        )
        
        # Get video info for metadata
        video_info = self.youtube_handler.get_video_info(source_url)
        
        # Step 2: Convert to our segment format
        segments = [
            Segment(start=s.start, end=s.end, text=s.text)
            for s in caption_segments
        ]
        
        # Step 3: Generate outputs
        logger.info(f"[{job_id}] Generating outputs...")
        
        formatter = OutputFormatter(str(job_output_dir))
        paths = formatter.generate_all(
            segments,
            metadata={
                "job_id": job_id,
                "source": "youtube_captions",
                "video_id": video_info.video_id,
                "title": video_info.title,
                "channel": video_info.channel,
                "duration": video_info.duration,
                "source_url": source_url
            }
        )
        
        return paths
    
    def process_youtube_auto_ingest(self, job: dict) -> dict:
        """
        Process YouTube auto-ingest job (downloads and transcribes).
        
        Flow: URL → download audio → normalize → transcribe → generate outputs
        
        ⚠️ This mode must be explicitly enabled via YOUTUBE_AUTO_INGEST=true
        """
        if not YOUTUBE_AUTO_INGEST_ENABLED:
            raise ValueError(
                "YouTube auto-ingest is disabled. "
                "Set YOUTUBE_AUTO_INGEST=true to enable."
            )
        
        job_id = job["id"]
        source_url = job["source_url"]
        model = job["model"]
        language = job.get("language")
        
        if not source_url:
            raise ValueError("YouTube job missing source_url")
        
        # Setup paths
        job_output_dir = OUTPUTS_DIR / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_path = None
        normalized_path = job_output_dir / "audio_normalized.wav"
        
        try:
            # Step 1: Check duration limit and get info
            logger.info(f"[{job_id}] Checking video info...")
            video_info = self.youtube_handler.check_duration_limit(source_url)
            
            # Step 2: Download audio
            logger.info(f"[{job_id}] Downloading audio: {video_info.title}...")
            downloaded_path = self.youtube_handler.download_audio(source_url)
            
            # Step 3: Normalize audio
            logger.info(f"[{job_id}] Normalizing audio...")
            self.audio_processor.normalize_audio(
                downloaded_path,
                str(normalized_path)
            )
            
            # Step 4: Transcribe
            logger.info(f"[{job_id}] Transcribing with model={model}...")
            
            if model != WHISPER_MODEL:
                transcriber = Transcriber(model_size=model, device=WHISPER_DEVICE)
            else:
                transcriber = self.transcriber
            
            result = transcriber.transcribe(
                str(normalized_path),
                language=language
            )
            
            # Step 5: Generate outputs
            logger.info(f"[{job_id}] Generating outputs...")
            
            segments = [
                Segment(start=s.start, end=s.end, text=s.text)
                for s in result.segments
            ]
            
            formatter = OutputFormatter(str(job_output_dir))
            paths = formatter.generate_all(
                segments,
                metadata={
                    "job_id": job_id,
                    "source": "youtube_auto_ingest",
                    "model": model,
                    "language": result.language,
                    "language_probability": result.language_probability,
                    "video_id": video_info.video_id,
                    "title": video_info.title,
                    "channel": video_info.channel,
                    "duration": video_info.duration,
                    "source_url": source_url
                }
            )
            
            return paths
            
        finally:
            # Cleanup temporary files
            if downloaded_path:
                self.youtube_handler.cleanup_download(downloaded_path)
            try:
                normalized_path.unlink()
            except Exception:
                pass
    
    def process_job(self, job: dict) -> None:
        """
        Process a job based on its type.
        
        Updates status to 'running' before processing, then 'done' or 'failed'.
        """
        job_id = job["id"]
        job_type = job["job_type"]
        
        logger.info(f"Processing job {job_id} (type={job_type})")
        
        # Mark as running
        self.update_job_status(job_id, "running")
        
        try:
            # Route to appropriate handler
            if job_type == "file_upload":
                paths = self.process_file_upload(job)
            elif job_type == "youtube_captions":
                paths = self.process_youtube_captions(job)
            elif job_type == "youtube_auto_ingest":
                paths = self.process_youtube_auto_ingest(job)
            else:
                raise ValueError(f"Unknown job type: {job_type}")
            
            # Save transcript paths
            self.save_transcript_paths(job_id, paths)
            
            # Mark as done
            self.update_job_status(job_id, "done")
            logger.info(f"Job {job_id} completed successfully")
            
        except YouTubeNoCaptionsError as e:
            # Special handling: not really an error, just no captions
            self.update_job_status(
                job_id, "failed",
                f"No captions available. Please upload a file instead. ({e})"
            )
        except YouTubeDurationExceededError as e:
            self.update_job_status(job_id, "failed", str(e))
        except (AudioProcessorError, TranscriberError, YouTubeHandlerError) as e:
            logger.error(f"Job {job_id} failed: {e}")
            self.update_job_status(job_id, "failed", str(e))
        except FileNotFoundError as e:
            logger.error(f"Job {job_id} failed: {e}")
            self.update_job_status(job_id, "failed", f"File not found: {e}")
        except Exception as e:
            logger.exception(f"Job {job_id} failed with unexpected error")
            self.update_job_status(job_id, "failed", f"Unexpected error: {e}")
    
    def run(self) -> None:
        """
        Main worker loop.
        
        Polls for jobs and processes them until shutdown.
        """
        logger.info("=" * 60)
        logger.info("Worker started")
        logger.info(f"  Database: {DATABASE_URL}")
        logger.info(f"  Whisper model: {WHISPER_MODEL}")
        logger.info(f"  Poll interval: {POLL_INTERVAL}s")
        logger.info(f"  YouTube auto-ingest: {YOUTUBE_AUTO_INGEST_ENABLED}")
        logger.info("=" * 60)
        
        while self.running:
            try:
                # Check for next job
                job = self.get_next_job()
                
                if job:
                    self.process_job(job)
                else:
                    # No jobs, wait before polling again
                    time.sleep(POLL_INTERVAL)
                    
            except Exception as e:
                logger.exception(f"Error in worker loop: {e}")
                # Wait before retrying to avoid tight error loop
                time.sleep(POLL_INTERVAL * 2)
        
        logger.info("Worker shutdown complete")


def main():
    """Entry point."""
    worker = Worker()
    worker.run()


if __name__ == "__main__":
    main()
