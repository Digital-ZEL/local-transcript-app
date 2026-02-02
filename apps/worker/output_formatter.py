"""
Output Formatter — Generate transcript output files
====================================================
Handles:
- segments.json (timestamps + text, machine-readable)
- transcript.txt (plain text)
- transcript.srt (SubRip subtitle format)
- transcript.vtt (WebVTT subtitle format)
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class Segment:
    """A transcript segment with timing."""
    start: float  # seconds
    end: float    # seconds  
    text: str
    
    def to_dict(self) -> dict:
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "text": self.text.strip()
        }


class OutputFormatterError(Exception):
    """Raised when output formatting fails."""
    pass


class OutputFormatter:
    """
    Formats transcript segments into various output formats.
    
    Supported formats:
    - JSON: Machine-readable segments with timestamps
    - TXT: Plain text transcript
    - SRT: SubRip subtitle format (widely supported)
    - VTT: WebVTT format (web standard)
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize formatter.
        
        Args:
            output_dir: Directory to write output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format time for SRT (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def _format_vtt_time(seconds: float) -> str:
        """Format time for VTT (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    @staticmethod
    def _clean_text_for_subtitles(text: str) -> str:
        """Clean text for subtitle output."""
        # Remove extra whitespace
        text = " ".join(text.split())
        # Escape special characters if needed
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return text
    
    def generate_json(
        self,
        segments: List[Segment],
        output_name: str = "segments.json",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Generate JSON output with segments and metadata.
        
        Args:
            segments: List of transcript segments
            output_name: Output filename
            metadata: Optional metadata to include
            
        Returns:
            Path to generated file
        """
        output_path = self.output_dir / output_name
        
        data = {
            "segments": [seg.to_dict() for seg in segments],
            "segment_count": len(segments),
        }
        
        # Calculate total duration
        if segments:
            data["duration"] = round(segments[-1].end, 2)
        
        # Add metadata if provided
        if metadata:
            data["metadata"] = metadata
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated JSON: {output_path}")
        return str(output_path)
    
    def generate_txt(
        self,
        segments: List[Segment],
        output_name: str = "transcript.txt",
        include_timestamps: bool = False
    ) -> str:
        """
        Generate plain text transcript.
        
        Args:
            segments: List of transcript segments
            output_name: Output filename
            include_timestamps: Add timestamps as [MM:SS] prefixes
            
        Returns:
            Path to generated file
        """
        output_path = self.output_dir / output_name
        
        lines = []
        for seg in segments:
            text = seg.text.strip()
            if not text:
                continue
                
            if include_timestamps:
                mins = int(seg.start // 60)
                secs = int(seg.start % 60)
                lines.append(f"[{mins:02d}:{secs:02d}] {text}")
            else:
                lines.append(text)
        
        # Join with spaces for natural reading, or newlines for timestamped
        separator = "\n" if include_timestamps else " "
        content = separator.join(lines)
        
        # Clean up multiple spaces
        content = re.sub(r' +', ' ', content)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Generated TXT: {output_path}")
        return str(output_path)
    
    def generate_srt(
        self,
        segments: List[Segment],
        output_name: str = "transcript.srt"
    ) -> str:
        """
        Generate SRT (SubRip) subtitle file.
        
        Format:
        1
        00:00:01,000 --> 00:00:04,500
        Hello world
        
        2
        00:00:05,000 --> 00:00:08,000
        This is a test
        
        Args:
            segments: List of transcript segments
            output_name: Output filename
            
        Returns:
            Path to generated file
        """
        output_path = self.output_dir / output_name
        
        srt_lines = []
        for i, seg in enumerate(segments, start=1):
            text = self._clean_text_for_subtitles(seg.text)
            if not text:
                continue
            
            start_time = self._format_srt_time(seg.start)
            end_time = self._format_srt_time(seg.end)
            
            srt_lines.append(str(i))
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text)
            srt_lines.append("")  # Blank line between entries
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines))
        
        logger.info(f"Generated SRT: {output_path}")
        return str(output_path)
    
    def generate_vtt(
        self,
        segments: List[Segment],
        output_name: str = "transcript.vtt"
    ) -> str:
        """
        Generate WebVTT subtitle file.
        
        Format:
        WEBVTT
        
        00:00:01.000 --> 00:00:04.500
        Hello world
        
        00:00:05.000 --> 00:00:08.000
        This is a test
        
        Args:
            segments: List of transcript segments
            output_name: Output filename
            
        Returns:
            Path to generated file
        """
        output_path = self.output_dir / output_name
        
        vtt_lines = ["WEBVTT", ""]  # Header
        
        for seg in segments:
            text = self._clean_text_for_subtitles(seg.text)
            if not text:
                continue
            
            start_time = self._format_vtt_time(seg.start)
            end_time = self._format_vtt_time(seg.end)
            
            vtt_lines.append(f"{start_time} --> {end_time}")
            vtt_lines.append(text)
            vtt_lines.append("")  # Blank line
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(vtt_lines))
        
        logger.info(f"Generated VTT: {output_path}")
        return str(output_path)
    
    def generate_all(
        self,
        segments: List[Segment],
        base_name: str = "transcript",
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Generate all output formats at once.
        
        Args:
            segments: List of transcript segments
            base_name: Base filename (without extension)
            metadata: Optional metadata for JSON output
            
        Returns:
            Dict with paths to all generated files
        """
        paths = {
            "json": self.generate_json(
                segments, 
                f"{base_name}_segments.json",
                metadata
            ),
            "txt": self.generate_txt(segments, f"{base_name}.txt"),
            "srt": self.generate_srt(segments, f"{base_name}.srt"),
            "vtt": self.generate_vtt(segments, f"{base_name}.vtt"),
        }
        
        logger.info(f"Generated all formats in {self.output_dir}")
        return paths


def segments_from_dicts(segment_dicts: List[dict]) -> List[Segment]:
    """Convert list of dicts to Segment objects."""
    return [
        Segment(
            start=d["start"],
            end=d["end"],
            text=d["text"]
        )
        for d in segment_dicts
    ]


def format_transcript_outputs(
    segments: List[dict],
    output_dir: str,
    metadata: Optional[dict] = None
) -> dict:
    """
    Convenience function to generate all transcript outputs.
    
    Args:
        segments: List of segment dicts with start, end, text
        output_dir: Where to write files
        metadata: Optional metadata
        
    Returns:
        Dict with paths to all generated files
    """
    formatter = OutputFormatter(output_dir)
    segment_objects = segments_from_dicts(segments)
    return formatter.generate_all(segment_objects, metadata=metadata)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample data
    test_segments = [
        Segment(start=0.0, end=2.5, text="Hello and welcome to this test."),
        Segment(start=2.5, end=5.0, text="This is a sample transcript."),
        Segment(start=5.0, end=8.0, text="We're testing all output formats."),
        Segment(start=8.0, end=12.0, text="Including JSON, TXT, SRT, and VTT."),
    ]
    
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/transcript_test"
    
    formatter = OutputFormatter(output_dir)
    paths = formatter.generate_all(
        test_segments,
        metadata={"test": True, "language": "en"}
    )
    
    print(f"\n{'='*60}")
    print("Generated files:")
    for fmt, path in paths.items():
        print(f"  {fmt.upper()}: {path}")
    print(f"{'='*60}\n")
    
    # Show sample content
    print("SRT Preview:")
    print("-" * 40)
    with open(paths["srt"]) as f:
        print(f.read()[:500])
