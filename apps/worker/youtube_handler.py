"""
YouTube Handler — Captions fetching and auto-ingest
====================================================
Handles:
- URL validation and parsing
- Caption/subtitle fetching (Safe Link Mode)
- Audio download via yt-dlp (Auto Ingest Mode)
- Duration and size limit enforcement
"""

import re
import logging
import subprocess
import os
import json
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


# Security: STRICT allowlist of domains
ALLOWED_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "www.youtu.be"
}


@dataclass
class YouTubeVideoInfo:
    """Metadata about a YouTube video."""
    video_id: str
    title: str
    duration: int  # seconds
    channel: str
    upload_date: str
    has_captions: bool
    caption_languages: List[str]


@dataclass
class CaptionSegment:
    """A caption segment with timing."""
    start: float
    end: float
    text: str
    
    def to_dict(self) -> dict:
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "text": self.text.strip()
        }


class YouTubeHandlerError(Exception):
    """Raised when YouTube handling fails."""
    pass


class YouTubeURLBlockedError(YouTubeHandlerError):
    """Raised when URL is not from allowed domain."""
    pass


class YouTubeDurationExceededError(YouTubeHandlerError):
    """Raised when video exceeds duration limit."""
    pass


class YouTubeNoCaptionsError(YouTubeHandlerError):
    """Raised when no captions are available."""
    pass


class YouTubeHandler:
    """
    Handles YouTube video processing for transcription.
    
    Two modes:
    1. Safe Link Mode: Fetch existing captions only
    2. Auto Ingest Mode: Download audio and transcribe locally
    """
    
    def __init__(
        self,
        max_duration_seconds: int = 3600,  # 1 hour default
        max_file_size_mb: int = 500,
        yt_dlp_path: str = "yt-dlp",
        download_dir: Optional[str] = None
    ):
        self.max_duration = max_duration_seconds
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.yt_dlp_path = yt_dlp_path
        self.download_dir = download_dir or "/tmp/youtube_downloads"
        
        # Ensure download dir exists
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
    
    def validate_url(self, url: str) -> str:
        """
        Validate YouTube URL and extract video ID.
        
        Args:
            url: YouTube URL to validate
            
        Returns:
            Video ID if valid
            
        Raises:
            YouTubeURLBlockedError: If URL is not from allowed domain
            YouTubeHandlerError: If URL format is invalid
        """
        try:
            parsed = urlparse(url)
        except Exception:
            raise YouTubeHandlerError(f"Invalid URL format: {url}")
        
        # Check domain against strict allowlist
        domain = parsed.netloc.lower()
        if domain not in ALLOWED_DOMAINS:
            raise YouTubeURLBlockedError(
                f"Domain '{domain}' not allowed. "
                f"Only YouTube URLs are accepted: youtube.com, youtu.be"
            )
        
        # Extract video ID
        video_id = None
        
        if "youtu.be" in domain:
            # Short URL: youtu.be/VIDEO_ID
            video_id = parsed.path.strip("/").split("/")[0]
        else:
            # Standard URL: youtube.com/watch?v=VIDEO_ID
            query_params = parse_qs(parsed.query)
            if "v" in query_params:
                video_id = query_params["v"][0]
            elif "/shorts/" in parsed.path:
                # Shorts: youtube.com/shorts/VIDEO_ID
                video_id = parsed.path.split("/shorts/")[1].split("/")[0]
            elif "/embed/" in parsed.path:
                # Embed: youtube.com/embed/VIDEO_ID
                video_id = parsed.path.split("/embed/")[1].split("/")[0]
        
        if not video_id or not re.match(r'^[A-Za-z0-9_-]{11}$', video_id):
            raise YouTubeHandlerError(
                f"Could not extract valid video ID from URL: {url}"
            )
        
        return video_id
    
    def get_video_info(self, url: str) -> YouTubeVideoInfo:
        """
        Get video metadata without downloading.
        
        Args:
            url: YouTube URL
            
        Returns:
            YouTubeVideoInfo with video metadata
        """
        video_id = self.validate_url(url)
        
        cmd = [
            self.yt_dlp_path,
            "--dump-json",
            "--no-download",
            "--no-warnings",
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                raise YouTubeHandlerError(
                    f"Failed to get video info: {result.stderr[:200]}"
                )
            
            data = json.loads(result.stdout)
            
            # Extract caption info
            subtitles = data.get("subtitles", {})
            auto_captions = data.get("automatic_captions", {})
            all_captions = {**subtitles, **auto_captions}
            
            return YouTubeVideoInfo(
                video_id=video_id,
                title=data.get("title", "Unknown"),
                duration=data.get("duration", 0),
                channel=data.get("channel", data.get("uploader", "Unknown")),
                upload_date=data.get("upload_date", ""),
                has_captions=len(all_captions) > 0,
                caption_languages=list(subtitles.keys())  # Only manual captions
            )
            
        except subprocess.TimeoutExpired:
            raise YouTubeHandlerError("Timeout fetching video info")
        except json.JSONDecodeError:
            raise YouTubeHandlerError("Failed to parse video info")
    
    def check_duration_limit(self, url: str) -> YouTubeVideoInfo:
        """
        Check if video is within duration limit.
        
        Returns:
            Video info if within limit
            
        Raises:
            YouTubeDurationExceededError: If video exceeds limit
        """
        info = self.get_video_info(url)
        
        if info.duration > self.max_duration:
            raise YouTubeDurationExceededError(
                f"Video duration ({info.duration}s) exceeds limit "
                f"({self.max_duration}s / {self.max_duration // 60} min)"
            )
        
        return info
    
    def fetch_captions(
        self,
        url: str,
        language: str = "en"
    ) -> List[CaptionSegment]:
        """
        Fetch existing captions from YouTube (Safe Link Mode).
        
        Args:
            url: YouTube URL
            language: Preferred caption language
            
        Returns:
            List of CaptionSegment objects
            
        Raises:
            YouTubeNoCaptionsError: If no captions available
        """
        video_id = self.validate_url(url)
        
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._errors import (
                TranscriptsDisabled, 
                NoTranscriptFound,
                VideoUnavailable
            )
        except ImportError:
            raise YouTubeHandlerError(
                "youtube-transcript-api not installed. "
                "Run: pip install youtube-transcript-api"
            )
        
        try:
            # Try to get transcript in preferred language
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Priority: manual transcript > auto-generated
            transcript = None
            try:
                transcript = transcript_list.find_manually_created_transcript([language, 'en'])
            except NoTranscriptFound:
                try:
                    transcript = transcript_list.find_generated_transcript([language, 'en'])
                except NoTranscriptFound:
                    pass
            
            if transcript is None:
                # Fall back to any available transcript
                try:
                    transcript = transcript_list.find_transcript(['en', language])
                except NoTranscriptFound:
                    available = [t.language_code for t in transcript_list]
                    if available:
                        transcript = transcript_list.find_transcript(available)
                    else:
                        raise YouTubeNoCaptionsError(
                            f"No captions available for video: {video_id}"
                        )
            
            # Fetch the transcript data
            caption_data = transcript.fetch()
            
            segments = []
            for item in caption_data:
                segments.append(CaptionSegment(
                    start=item["start"],
                    end=item["start"] + item.get("duration", 0),
                    text=item["text"]
                ))
            
            logger.info(f"Fetched {len(segments)} caption segments (lang: {transcript.language_code})")
            return segments
            
        except TranscriptsDisabled:
            raise YouTubeNoCaptionsError(
                f"Captions are disabled for this video: {video_id}"
            )
        except VideoUnavailable:
            raise YouTubeHandlerError(
                f"Video unavailable: {video_id}"
            )
        except Exception as e:
            if "No transcript" in str(e):
                raise YouTubeNoCaptionsError(f"No captions available: {video_id}")
            raise YouTubeHandlerError(f"Failed to fetch captions: {e}")
    
    def download_audio(
        self,
        url: str,
        output_path: Optional[str] = None,
        format: str = "bestaudio/best"
    ) -> str:
        """
        Download audio from YouTube (Auto Ingest Mode).
        
        ⚠️ WARNING: This may violate YouTube ToS. Use responsibly.
        
        Args:
            url: YouTube URL
            output_path: Where to save the audio (auto-generated if None)
            format: yt-dlp format string
            
        Returns:
            Path to downloaded audio file
        """
        info = self.check_duration_limit(url)
        video_id = info.video_id
        
        if output_path is None:
            output_path = os.path.join(
                self.download_dir, 
                f"{video_id}.%(ext)s"
            )
        
        cmd = [
            self.yt_dlp_path,
            "--no-warnings",
            "-f", format,
            "-x",  # Extract audio
            "--audio-format", "wav",
            "--audio-quality", "0",  # Best quality
            "--max-filesize", str(self.max_file_size_bytes),
            "-o", output_path,
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        
        logger.info(f"Downloading audio: {info.title} ({info.duration}s)")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                error = result.stderr[-500:] if result.stderr else "Unknown error"
                raise YouTubeHandlerError(f"Download failed: {error}")
            
            # Find the actual output file (yt-dlp adds extension)
            expected_path = output_path.replace("%(ext)s", "wav")
            if os.path.exists(expected_path):
                logger.info(f"Downloaded: {expected_path}")
                return expected_path
            
            # Search for the file
            base_path = output_path.rsplit(".", 1)[0].replace("%(ext)s", "")
            for ext in ["wav", "m4a", "mp3", "opus", "webm"]:
                candidate = f"{base_path}.{ext}"
                if os.path.exists(candidate):
                    logger.info(f"Downloaded: {candidate}")
                    return candidate
            
            # Check if file exists with video_id
            for f in os.listdir(self.download_dir):
                if video_id in f:
                    return os.path.join(self.download_dir, f)
            
            raise YouTubeHandlerError("Download completed but file not found")
            
        except subprocess.TimeoutExpired:
            raise YouTubeHandlerError("Download timed out (10 min limit)")
    
    def cleanup_download(self, file_path: str) -> None:
        """Remove downloaded file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {e}")


def validate_youtube_url(url: str) -> str:
    """Quick validation that URL is from allowed YouTube domain."""
    handler = YouTubeHandler()
    return handler.validate_url(url)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python youtube_handler.py <youtube_url> [captions|download|info]")
        sys.exit(1)
    
    url = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "info"
    
    handler = YouTubeHandler()
    
    try:
        if action == "info":
            info = handler.get_video_info(url)
            print(f"\n{'='*60}")
            print(f"Title: {info.title}")
            print(f"Channel: {info.channel}")
            print(f"Duration: {info.duration}s ({info.duration // 60}m {info.duration % 60}s)")
            print(f"Has Captions: {info.has_captions}")
            print(f"Caption Languages: {info.caption_languages}")
            print(f"{'='*60}\n")
            
        elif action == "captions":
            segments = handler.fetch_captions(url)
            print(f"\nFetched {len(segments)} segments:\n")
            for seg in segments[:10]:
                print(f"[{seg.start:6.2f} -> {seg.end:6.2f}] {seg.text}")
            if len(segments) > 10:
                print(f"... and {len(segments) - 10} more")
                
        elif action == "download":
            path = handler.download_audio(url)
            print(f"✓ Downloaded to: {path}")
            
        else:
            print(f"Unknown action: {action}")
            sys.exit(1)
            
    except YouTubeHandlerError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
