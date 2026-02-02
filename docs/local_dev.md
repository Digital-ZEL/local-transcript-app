# Local Development Setup

Get the Local Transcript App running on your machine.

## Prerequisites

- **Docker** (20.10+) and **Docker Compose** (v2)
- **Git** for cloning the repo
- 4GB+ RAM recommended (for Whisper models)

### Check Prerequisites

```bash
docker --version    # Docker version 20.10+
docker compose version  # Docker Compose v2+
```

## Quick Start

### 1. Clone and Navigate

```bash
cd ~/clawd/projects/local-transcript-app
```

### 2. Initialize Project

```bash
make init
```

This creates:
- `./data/uploads/` — uploaded media files
- `./data/outputs/` — transcription outputs
- `./data/db/` — SQLite database
- `.env` — environment config (copied from `.env.example`)

### 3. Start Services

```bash
make up
```

Or with build and logs:

```bash
make dev
```

### 4. Verify It Works

- **Web UI:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "features": {
    "youtube_safe_mode": true,
    "youtube_auto_ingest": false,
    "whisper_model": "small",
    "max_upload_mb": 500
  }
}
```

## Configuration

Edit `.env` to customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | 8000 | API server port |
| `WEB_PORT` | 3000 | Web UI port |
| `WHISPER_MODEL` | small | tiny/base/small/medium/large |
| `WHISPER_DEVICE` | cpu | cpu or cuda (GPU) |
| `MAX_UPLOAD_SIZE_MB` | 500 | Max file upload size |
| `YOUTUBE_SAFE_MODE` | true | Captions-only mode |
| `YOUTUBE_AUTO_INGEST` | false | Auto-download (risky) |

### Whisper Model Sizes

| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | ~1GB | Fastest | Lower |
| base | ~1GB | Fast | OK |
| small | ~2GB | Good | Good |
| medium | ~5GB | Slower | Better |
| large | ~10GB | Slowest | Best |

For most use cases, `small` is the best balance.

## Common Commands

```bash
make up          # Start all services (detached)
make down        # Stop all services
make logs        # Follow all logs
make logs-api    # API logs only
make logs-worker # Worker logs only
make shell       # Shell into API container
make build       # Rebuild containers
make clean       # Remove containers and images
make status      # Check service status
```

## Development Workflow

### Hot Reload

All services support hot reload in development:
- **API:** Python files auto-reload via uvicorn
- **Web:** Vite HMR for React changes
- **Worker:** Restart needed for changes (or use `make down && make up`)

### Accessing Containers

```bash
# API container (Python)
make shell-api
pip install some-package

# Worker container (Python + ffmpeg)
make shell-worker
ffmpeg -version

# Web container (Node)
make shell-web
npm install some-package
```

### Database Access

SQLite database is at `./data/db/transcript.db`:

```bash
# From host
sqlite3 data/db/transcript.db

# Or from API container
make shell-api
sqlite3 /data/db/transcript.db
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Or change ports in .env
API_PORT=8001
WEB_PORT=3001
```

### Container Won't Start

```bash
# Check logs
docker compose logs api
docker compose logs worker
docker compose logs web

# Rebuild from scratch
make clean
make build
make up
```

### Whisper Model Download

First run downloads the model (~500MB for `small`). If it fails:

```bash
# Shell into worker and download manually
make shell-worker
python -c "from faster_whisper import WhisperModel; WhisperModel('small')"
```

### Permission Issues

```bash
# Fix data directory permissions
sudo chown -R $(whoami):$(whoami) data/
chmod -R 755 data/
```

## GPU Support (Optional)

For NVIDIA GPU acceleration:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Update `.env`:
   ```
   WHISPER_DEVICE=cuda
   ```

3. Add to `docker-compose.yml` under `worker` service:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```

4. Rebuild: `make build && make up`

## Project Structure

```
local-transcript-app/
├── apps/
│   ├── api/           # FastAPI backend
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── worker/        # Transcription worker
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── web/           # React frontend
│       ├── src/
│       ├── Dockerfile
│       ├── package.json
│       └── vite.config.ts
├── data/              # Persistent storage
│   ├── uploads/
│   ├── outputs/
│   └── db/
├── docs/
│   └── local_dev.md   # This file
├── docker-compose.yml
├── Makefile
├── .env.example
└── PROJECT_SPEC.md
```

## Next Steps

Once running:
1. Access the web UI at http://localhost:3000
2. Check API docs at http://localhost:8000/docs
3. Upload a test audio file
4. Watch the job progress and view the transcript
