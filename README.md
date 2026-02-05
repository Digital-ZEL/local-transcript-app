# Local Transcript App

A self-hosted transcription API that runs entirely on your local machine. No cloud services, no API keys, no data leaving your computer.

## Features

- 🎬 **YouTube Captions** — Paste a YouTube URL, get captions instantly
- 🎤 **Local Transcription** — Upload audio/video files for transcription via [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- 📝 **Export Formats** — SRT, VTT, TXT, JSON
- 🔒 **100% Local** — No cloud APIs, your data stays on your machine
- ⚡ **Fast** — YouTube captions in ~2 seconds, local transcription depends on your hardware

## Quick Start

### Requirements
- Python 3.10+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (for YouTube captions)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (for local transcription)

### Install & Run

```bash
# Clone the repo
git clone https://github.com/Digital-ZEL/local-transcript-app.git
cd local-transcript-app

# Set up the API
cd apps/api
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run the server
python main.py
```

Server runs on `http://localhost:8765`

## API Endpoints

### Health Check
```bash
curl http://localhost:8765/health
```

### YouTube Captions
```bash
# Extract captions from YouTube video
curl -X POST http://localhost:8765/api/youtube \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'

# Response: { "job_id": "abc-123", "status": "completed", ... }
```

### Get Transcript
```bash
# Get transcript segments
curl http://localhost:8765/api/jobs/{job_id}/transcript

# Export as SRT
curl http://localhost:8765/api/jobs/{job_id}/export?fmt=srt

# Export as VTT
curl http://localhost:8765/api/jobs/{job_id}/export?fmt=vtt
```

### Upload File (Local Transcription)
```bash
curl -X POST http://localhost:8765/api/upload \
  -F "file=@audio.mp3" \
  -F "model=small"  # tiny, base, small, medium, large
```

### Job Status
```bash
curl http://localhost:8765/api/jobs/{job_id}
```

## Models

For local transcription, choose a model based on your hardware:

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | 39M | Fastest | Lower |
| base | 74M | Fast | Moderate |
| small | 244M | Moderate | Good |
| medium | 769M | Slow | Better |
| large | 1.5G | Slowest | Best |

## Project Structure

```
apps/
  api/           # FastAPI backend
    routes/      # API endpoints
    models.py    # Pydantic models
    database.py  # SQLite operations
    main.py      # Entry point
data/
  uploads/       # Uploaded files
  outputs/       # Generated transcripts
  transcript.db  # SQLite database
docs/            # API documentation
```

## Tech Stack

- **Backend**: Python, FastAPI, SQLite
- **Transcription**: faster-whisper (Whisper optimized with CTranslate2)
- **YouTube**: yt-dlp for caption extraction

## License

MIT

---

Built by [@Digital_Zel](https://twitter.com/Digital_Zel)
