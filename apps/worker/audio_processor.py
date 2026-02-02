"""
Audio Processor — ffmpeg audio extraction and normalization
============================================================
Handles:
- Extracting audio from video files
- Normalizing audio to consistent format for Whisper
- File format conversion
"""

import subprocess
import os
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class AudioProcessorError(Exception):
    """Raised when audio processing fails."""
    pass


class AudioProcessor:
    """
    Handles audio extraction and normalization using ffmpeg.
    
    Target format for Whisper:
    - 16kHz sample rate (Whisper's native rate)
    - Mono channel
    - 16-bit PCM WAV
    """
    
    # Supported input formats
    SUPPORTED_VIDEO = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v'}
    SUPPORTED_AUDIO = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma', '.opus'}
    
    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self._verify_ffmpeg()
    
    def _verify_ffmpeg(self) -> None:
        """Verify ffmpeg is installed and accessible."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise AudioProcessorError("ffmpeg not working properly")
            logger.info("ffmpeg verified OK")
        except FileNotFoundError:
            raise AudioProcessorError(
                "ffmpeg not found. Install with: apt install ffmpeg (Linux) "
                "or brew install ffmpeg (Mac)"
            )
        except subprocess.TimeoutExpired:
            raise AudioProcessorError("ffmpeg verification timed out")
    
    def get_media_info(self, input_path: str) -> dict:
        """
        Get media file info using ffprobe.
        
        Returns dict with:
        - duration: float (seconds)
        - has_audio: bool
        - has_video: bool
        - audio_codec: str or None
        - sample_rate: int or None
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise AudioProcessorError(f"File not found: {input_path}")
        
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(input_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise AudioProcessorError(f"ffprobe failed: {result.stderr}")
            
            import json
            data = json.loads(result.stdout)
            
            info = {
                "duration": float(data.get("format", {}).get("duration", 0)),
                "has_audio": False,
                "has_video": False,
                "audio_codec": None,
                "sample_rate": None,
            }
            
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    info["has_audio"] = True
                    info["audio_codec"] = stream.get("codec_name")
                    info["sample_rate"] = int(stream.get("sample_rate", 0))
                elif stream.get("codec_type") == "video":
                    info["has_video"] = True
            
            return info
            
        except subprocess.TimeoutExpired:
            raise AudioProcessorError("ffprobe timed out analyzing file")
        except json.JSONDecodeError:
            raise AudioProcessorError("Failed to parse ffprobe output")
    
    def is_supported(self, file_path: str) -> bool:
        """Check if file format is supported."""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_VIDEO or ext in self.SUPPORTED_AUDIO
    
    def normalize_audio(
        self,
        input_path: str,
        output_path: str,
        sample_rate: int = 16000,
        channels: int = 1,
        normalize_volume: bool = True,
        timeout: int = 600
    ) -> str:
        """
        Extract and normalize audio to Whisper-compatible format.
        
        Args:
            input_path: Source media file
            output_path: Destination WAV file
            sample_rate: Target sample rate (16000 for Whisper)
            channels: Number of audio channels (1 = mono)
            normalize_volume: Apply loudnorm filter for consistent volume
            timeout: Max processing time in seconds
        
        Returns:
            Path to normalized audio file
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise AudioProcessorError(f"Input file not found: {input_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get media info
        info = self.get_media_info(str(input_path))
        if not info["has_audio"]:
            raise AudioProcessorError("Input file has no audio track")
        
        logger.info(f"Processing audio: {input_path.name} (duration: {info['duration']:.1f}s)")
        
        # Build ffmpeg command
        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output
            "-i", str(input_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # 16-bit PCM
            "-ar", str(sample_rate),  # Sample rate
            "-ac", str(channels),  # Channels
        ]
        
        # Add volume normalization filter
        if normalize_volume:
            # Two-pass loudnorm is best but single-pass is faster
            # Using measured values typical for speech
            cmd.extend([
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=-20:measured_TP=-1:measured_LRA=9:measured_thresh=-31:offset=0:linear=true"
            ])
        
        cmd.append(str(output_path))
        
        try:
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
                raise AudioProcessorError(f"ffmpeg conversion failed: {error_msg}")
            
            if not output_path.exists():
                raise AudioProcessorError("ffmpeg completed but output file not created")
            
            output_size = output_path.stat().st_size
            logger.info(f"Audio normalized: {output_path.name} ({output_size / 1024 / 1024:.1f} MB)")
            
            return str(output_path)
            
        except subprocess.TimeoutExpired:
            # Clean up partial output
            if output_path.exists():
                output_path.unlink()
            raise AudioProcessorError(
                f"Audio processing timed out after {timeout}s. "
                f"File may be too long or corrupted."
            )
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds."""
        info = self.get_media_info(audio_path)
        return info["duration"]


# Convenience function for simple usage
def normalize_for_whisper(input_path: str, output_path: str) -> str:
    """
    Simple wrapper to normalize any media file to Whisper-compatible audio.
    
    Args:
        input_path: Source media file (video or audio)
        output_path: Destination .wav file
    
    Returns:
        Path to normalized audio file
    """
    processor = AudioProcessor()
    return processor.normalize_audio(input_path, output_path)


if __name__ == "__main__":
    # Quick test
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 3:
        print("Usage: python audio_processor.py <input> <output.wav>")
        sys.exit(1)
    
    try:
        result = normalize_for_whisper(sys.argv[1], sys.argv[2])
        print(f"✓ Normalized audio saved to: {result}")
    except AudioProcessorError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
