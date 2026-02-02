"""
Transcriber — Whisper transcription with faster-whisper
========================================================
Handles:
- Model loading and caching
- Audio transcription with timestamps
- Language detection
- Segment generation
"""

import logging
from pathlib import Path
from typing import Optional, List, Iterator
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    """A single segment of transcribed text with timing info."""
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str     # Transcribed text
    
    def to_dict(self) -> dict:
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "text": self.text.strip()
        }


@dataclass 
class TranscriptionResult:
    """Complete transcription result."""
    segments: List[TranscriptSegment]
    language: str
    language_probability: float
    duration: float
    
    @property
    def text(self) -> str:
        """Full transcript as plain text."""
        return " ".join(seg.text.strip() for seg in self.segments)
    
    def to_dict(self) -> dict:
        return {
            "segments": [seg.to_dict() for seg in self.segments],
            "language": self.language,
            "language_probability": round(self.language_probability, 3),
            "duration": round(self.duration, 2),
            "text": self.text
        }


class TranscriberError(Exception):
    """Raised when transcription fails."""
    pass


class Transcriber:
    """
    Whisper-based transcription using faster-whisper.
    
    faster-whisper is a reimplementation of OpenAI's Whisper
    using CTranslate2, which is 4x faster with similar accuracy.
    """
    
    VALID_MODELS = {"tiny", "base", "small", "medium", "large-v2", "large-v3"}
    DEFAULT_MODEL = "small"
    
    # Model download location (uses HuggingFace cache by default)
    MODEL_CACHE_DIR = os.environ.get(
        "WHISPER_MODEL_DIR",
        os.path.expanduser("~/.cache/huggingface/hub")
    )
    
    def __init__(
        self,
        model_size: str = DEFAULT_MODEL,
        device: str = "auto",
        compute_type: str = "auto"
    ):
        """
        Initialize the transcriber.
        
        Args:
            model_size: Whisper model size (tiny/base/small/medium/large-v2/large-v3)
            device: "cpu", "cuda", or "auto" (auto-detect GPU)
            compute_type: Quantization ("float16", "int8", "auto")
        """
        if model_size not in self.VALID_MODELS:
            raise TranscriberError(
                f"Invalid model: {model_size}. Valid: {self.VALID_MODELS}"
            )
        
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
        
    def _load_model(self):
        """Lazy-load the model on first use."""
        if self._model is not None:
            return
        
        logger.info(f"Loading Whisper model: {self.model_size} (device={self.device})")
        
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise TranscriberError(
                "faster-whisper not installed. Run: pip install faster-whisper"
            )
        
        # Auto-detect best settings
        device = self.device
        compute_type = self.compute_type
        
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        
        if compute_type == "auto":
            compute_type = "float16" if device == "cuda" else "int8"
        
        logger.info(f"Using device={device}, compute_type={compute_type}")
        
        try:
            self._model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type,
                download_root=self.MODEL_CACHE_DIR
            )
            logger.info(f"Model loaded successfully")
        except Exception as e:
            raise TranscriberError(f"Failed to load model: {e}")
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        beam_size: int = 5,
        word_timestamps: bool = False,
        vad_filter: bool = True,
        vad_min_silence_duration_ms: int = 500
    ) -> TranscriptionResult:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to audio file (WAV recommended)
            language: Language code (e.g., "en") or None for auto-detect
            task: "transcribe" or "translate" (translate to English)
            beam_size: Beam size for decoding (higher = better but slower)
            word_timestamps: Include word-level timestamps
            vad_filter: Use voice activity detection to filter silence
            vad_min_silence_duration_ms: Min silence duration for VAD
        
        Returns:
            TranscriptionResult with segments and metadata
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise TranscriberError(f"Audio file not found: {audio_path}")
        
        # Load model
        self._load_model()
        
        logger.info(f"Transcribing: {audio_path.name}")
        
        try:
            segments_gen, info = self._model.transcribe(
                str(audio_path),
                language=language,
                task=task,
                beam_size=beam_size,
                word_timestamps=word_timestamps,
                vad_filter=vad_filter,
                vad_parameters={
                    "min_silence_duration_ms": vad_min_silence_duration_ms
                }
            )
            
            # Convert generator to list of segments
            segments = []
            for seg in segments_gen:
                segments.append(TranscriptSegment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text
                ))
                
                # Log progress every 50 segments
                if len(segments) % 50 == 0:
                    logger.debug(f"Processed {len(segments)} segments...")
            
            logger.info(
                f"Transcription complete: {len(segments)} segments, "
                f"language={info.language} ({info.language_probability:.0%})"
            )
            
            return TranscriptionResult(
                segments=segments,
                language=info.language,
                language_probability=info.language_probability,
                duration=info.duration
            )
            
        except Exception as e:
            raise TranscriberError(f"Transcription failed: {e}")
    
    def transcribe_with_progress(
        self,
        audio_path: str,
        progress_callback=None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe with progress reporting.
        
        Args:
            audio_path: Path to audio file
            progress_callback: Function called with (current_time, total_duration)
            **kwargs: Passed to transcribe()
        
        Returns:
            TranscriptionResult
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise TranscriberError(f"Audio file not found: {audio_path}")
        
        self._load_model()
        
        logger.info(f"Transcribing with progress: {audio_path.name}")
        
        try:
            segments_gen, info = self._model.transcribe(
                str(audio_path),
                **kwargs
            )
            
            segments = []
            total_duration = info.duration
            
            for seg in segments_gen:
                segments.append(TranscriptSegment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text
                ))
                
                if progress_callback and total_duration > 0:
                    progress_callback(seg.end, total_duration)
            
            return TranscriptionResult(
                segments=segments,
                language=info.language,
                language_probability=info.language_probability,
                duration=info.duration
            )
            
        except Exception as e:
            raise TranscriberError(f"Transcription failed: {e}")


# Factory function
def create_transcriber(model: str = "small") -> Transcriber:
    """Create a transcriber with the specified model."""
    return Transcriber(model_size=model)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python transcriber.py <audio_file> [model]")
        print("Models: tiny, base, small, medium, large-v2, large-v3")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "small"
    
    try:
        transcriber = create_transcriber(model)
        result = transcriber.transcribe(audio_file)
        
        print(f"\n{'='*60}")
        print(f"Language: {result.language} ({result.language_probability:.0%})")
        print(f"Duration: {result.duration:.1f}s")
        print(f"Segments: {len(result.segments)}")
        print(f"{'='*60}\n")
        
        for seg in result.segments[:10]:
            print(f"[{seg.start:6.2f} -> {seg.end:6.2f}] {seg.text}")
        
        if len(result.segments) > 10:
            print(f"... and {len(result.segments) - 10} more segments")
            
    except TranscriberError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
