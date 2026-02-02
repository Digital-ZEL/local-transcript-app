"""
Worker Service — Local Transcript App
======================================

Handles transcription job processing:
- File uploads → normalize → transcribe → outputs
- YouTube captions → fetch → convert → outputs
- YouTube auto-ingest → download → transcribe → outputs

Usage:
    python -m apps.worker.main
    
    # Or directly:
    cd apps/worker && python main.py
"""

from .audio_processor import AudioProcessor, AudioProcessorError, normalize_for_whisper
from .transcriber import Transcriber, TranscriberError, TranscriptSegment, TranscriptionResult
from .youtube_handler import (
    YouTubeHandler,
    YouTubeHandlerError,
    YouTubeNoCaptionsError,
    YouTubeDurationExceededError,
    validate_youtube_url
)
from .output_formatter import OutputFormatter, Segment, format_transcript_outputs

__all__ = [
    # Audio processing
    "AudioProcessor",
    "AudioProcessorError", 
    "normalize_for_whisper",
    
    # Transcription
    "Transcriber",
    "TranscriberError",
    "TranscriptSegment",
    "TranscriptionResult",
    
    # YouTube handling
    "YouTubeHandler",
    "YouTubeHandlerError",
    "YouTubeNoCaptionsError",
    "YouTubeDurationExceededError",
    "validate_youtube_url",
    
    # Output formatting
    "OutputFormatter",
    "Segment",
    "format_transcript_outputs",
]
