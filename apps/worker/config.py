"""
Worker Configuration
====================
Centralized configuration for the worker service.
All settings can be overridden via environment variables.
"""

import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class WorkerConfig:
    """Worker service configuration."""
    
    # Database
    database_url: str = "sqlite:///./data/transcripts.db"
    
    # Directories
    data_dir: Path = Path("./data")
    uploads_dir: Path = Path("./data/uploads")
    outputs_dir: Path = Path("./data/outputs")
    youtube_temp_dir: Path = Path("./data/youtube_temp")
    
    # Worker behavior
    poll_interval: int = 5  # seconds
    max_retries: int = 3
    
    # Whisper transcription
    whisper_model: str = "small"  # tiny, base, small, medium, large-v2, large-v3
    whisper_device: str = "auto"  # cpu, cuda, auto
    whisper_compute_type: str = "auto"  # float16, int8, auto
    
    # YouTube settings
    youtube_auto_ingest_enabled: bool = False
    youtube_max_duration: int = 3600  # 1 hour
    youtube_max_size_mb: int = 500
    
    # Audio processing
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    audio_normalize_volume: bool = True
    audio_timeout: int = 600  # 10 minutes
    
    @classmethod
    def from_env(cls) -> "WorkerConfig":
        """Load configuration from environment variables."""
        data_dir = Path(os.environ.get("DATA_DIR", "./data"))
        
        return cls(
            # Database
            database_url=os.environ.get(
                "DATABASE_URL", 
                f"sqlite:///{data_dir}/transcripts.db"
            ),
            
            # Directories
            data_dir=data_dir,
            uploads_dir=data_dir / "uploads",
            outputs_dir=data_dir / "outputs",
            youtube_temp_dir=data_dir / "youtube_temp",
            
            # Worker behavior
            poll_interval=int(os.environ.get("WORKER_POLL_INTERVAL", "5")),
            max_retries=int(os.environ.get("WORKER_MAX_RETRIES", "3")),
            
            # Whisper
            whisper_model=os.environ.get("WHISPER_MODEL", "small"),
            whisper_device=os.environ.get("WHISPER_DEVICE", "auto"),
            whisper_compute_type=os.environ.get("WHISPER_COMPUTE_TYPE", "auto"),
            
            # YouTube
            youtube_auto_ingest_enabled=os.environ.get(
                "YOUTUBE_AUTO_INGEST", "false"
            ).lower() == "true",
            youtube_max_duration=int(os.environ.get("YOUTUBE_MAX_DURATION", "3600")),
            youtube_max_size_mb=int(os.environ.get("YOUTUBE_MAX_SIZE_MB", "500")),
            
            # Audio
            audio_sample_rate=int(os.environ.get("AUDIO_SAMPLE_RATE", "16000")),
            audio_channels=int(os.environ.get("AUDIO_CHANNELS", "1")),
            audio_normalize_volume=os.environ.get(
                "AUDIO_NORMALIZE", "true"
            ).lower() == "true",
            audio_timeout=int(os.environ.get("AUDIO_TIMEOUT", "600")),
        )
    
    def ensure_directories(self) -> None:
        """Create all required directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.youtube_temp_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = WorkerConfig.from_env()


# Model size recommendations
MODEL_INFO = {
    "tiny": {
        "params": "39M",
        "vram": "~1GB",
        "speed": "~32x realtime",
        "quality": "Low - good for quick tests",
    },
    "base": {
        "params": "74M", 
        "vram": "~1GB",
        "speed": "~16x realtime",
        "quality": "Fair - usable for clear audio",
    },
    "small": {
        "params": "244M",
        "vram": "~2GB", 
        "speed": "~6x realtime",
        "quality": "Good - recommended default",
    },
    "medium": {
        "params": "769M",
        "vram": "~5GB",
        "speed": "~2x realtime",
        "quality": "Great - best quality/speed balance",
    },
    "large-v2": {
        "params": "1.5B",
        "vram": "~10GB",
        "speed": "~1x realtime",
        "quality": "Excellent - best accuracy",
    },
    "large-v3": {
        "params": "1.5B",
        "vram": "~10GB", 
        "speed": "~1x realtime",
        "quality": "Excellent - latest model",
    },
}


def print_config():
    """Print current configuration."""
    cfg = config
    print("\n" + "=" * 60)
    print("Worker Configuration")
    print("=" * 60)
    print(f"Database:              {cfg.database_url}")
    print(f"Data directory:        {cfg.data_dir}")
    print(f"Poll interval:         {cfg.poll_interval}s")
    print(f"")
    print(f"Whisper model:         {cfg.whisper_model}")
    print(f"Whisper device:        {cfg.whisper_device}")
    print(f"")
    print(f"YouTube auto-ingest:   {cfg.youtube_auto_ingest_enabled}")
    print(f"YouTube max duration:  {cfg.youtube_max_duration}s ({cfg.youtube_max_duration // 60} min)")
    print(f"YouTube max size:      {cfg.youtube_max_size_mb} MB")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_config()
    
    print("\nModel options:")
    for name, info in MODEL_INFO.items():
        print(f"  {name:12} - {info['quality']}")
