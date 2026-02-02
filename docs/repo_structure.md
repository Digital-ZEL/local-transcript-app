# Repository Structure

**Project:** Local Transcript App  
**Date:** February 2, 2026

---

## Overview

Monorepo structure with three main applications and shared configuration.

```
local-transcript-app/
├── apps/
│   ├── api/          # FastAPI backend
│   ├── worker/       # Transcription worker
│   └── web/          # React frontend
├── data/             # Runtime data (gitignored)
├── docs/             # Documentation
├── scripts/          # Utility scripts
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

---

## Full Directory Tree

```
local-transcript-app/
│
├── apps/
│   │
│   ├── api/                          # FastAPI Backend
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py               # FastAPI app entry point
│   │   │   ├── config.py             # Settings and env vars
│   │   │   ├── database.py           # SQLite connection + helpers
│   │   │   │
│   │   │   ├── routers/              # API route handlers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── health.py         # GET /health
│   │   │   │   ├── upload.py         # POST /api/upload
│   │   │   │   ├── youtube.py        # POST /api/youtube, /api/youtube/paste
│   │   │   │   ├── jobs.py           # GET/DELETE /api/jobs/*
│   │   │   │   ├── transcripts.py    # GET/PUT /api/jobs/{id}/transcript
│   │   │   │   ├── export.py         # GET /api/jobs/{id}/export
│   │   │   │   └── config.py         # GET /api/config
│   │   │   │
│   │   │   ├── models/               # Pydantic models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── job.py            # Job request/response models
│   │   │   │   ├── transcript.py     # Transcript models
│   │   │   │   └── youtube.py        # YouTube request models
│   │   │   │
│   │   │   ├── services/             # Business logic
│   │   │   │   ├── __init__.py
│   │   │   │   ├── job_service.py    # Job CRUD operations
│   │   │   │   ├── file_service.py   # File validation + storage
│   │   │   │   ├── youtube_service.py # YouTube URL validation + caption fetch
│   │   │   │   └── export_service.py # Format conversion
│   │   │   │
│   │   │   ├── middleware/           # Request middleware
│   │   │   │   ├── __init__.py
│   │   │   │   └── rate_limit.py     # Rate limiting
│   │   │   │
│   │   │   └── utils/                # Shared utilities
│   │   │       ├── __init__.py
│   │   │       ├── validators.py     # Input validation helpers
│   │   │       └── exceptions.py     # Custom exception classes
│   │   │
│   │   ├── tests/                    # API tests
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py           # Pytest fixtures
│   │   │   ├── test_upload.py
│   │   │   ├── test_youtube.py
│   │   │   ├── test_jobs.py
│   │   │   └── test_export.py
│   │   │
│   │   ├── migrations/               # Database migrations
│   │   │   └── 001_initial.sql
│   │   │
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── worker/                       # Transcription Worker
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py               # Worker entry point
│   │   │   ├── config.py             # Worker settings
│   │   │   ├── database.py           # Shared DB connection
│   │   │   │
│   │   │   ├── handlers/             # Job type handlers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py           # Base handler class
│   │   │   │   ├── file_upload.py    # file_upload job handler
│   │   │   │   ├── youtube_captions.py  # youtube_captions handler
│   │   │   │   └── youtube_auto.py   # youtube_auto_ingest handler
│   │   │   │
│   │   │   ├── transcription/        # Whisper integration
│   │   │   │   ├── __init__.py
│   │   │   │   ├── engine.py         # Whisper wrapper (faster-whisper)
│   │   │   │   └── formats.py        # Output format generators (SRT, VTT)
│   │   │   │
│   │   │   ├── media/                # Media processing
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ffmpeg.py         # Audio extraction + normalization
│   │   │   │   └── youtube.py        # yt-dlp wrapper (auto mode only)
│   │   │   │
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       └── logging.py        # Per-job logging
│   │   │
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py
│   │   │   ├── test_transcription.py
│   │   │   └── test_handlers.py
│   │   │
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   └── web/                          # React Frontend
│       ├── public/
│       │   ├── index.html
│       │   └── favicon.ico
│       │
│       ├── src/
│       │   ├── main.tsx              # App entry point
│       │   ├── App.tsx               # Root component
│       │   ├── vite-env.d.ts
│       │   │
│       │   ├── components/           # Reusable UI components
│       │   │   ├── Layout/
│       │   │   │   ├── Header.tsx
│       │   │   │   ├── Sidebar.tsx
│       │   │   │   └── index.tsx
│       │   │   ├── Upload/
│       │   │   │   ├── FileDropzone.tsx
│       │   │   │   ├── UploadProgress.tsx
│       │   │   │   └── index.tsx
│       │   │   ├── YouTube/
│       │   │   │   ├── YouTubeInput.tsx
│       │   │   │   ├── ModeSelector.tsx
│       │   │   │   ├── CaptionsPaste.tsx
│       │   │   │   └── index.tsx
│       │   │   ├── Jobs/
│       │   │   │   ├── JobList.tsx
│       │   │   │   ├── JobCard.tsx
│       │   │   │   ├── JobStatus.tsx
│       │   │   │   └── index.tsx
│       │   │   ├── Transcript/
│       │   │   │   ├── TranscriptViewer.tsx
│       │   │   │   ├── TranscriptEditor.tsx
│       │   │   │   ├── SegmentList.tsx
│       │   │   │   ├── ExportButtons.tsx
│       │   │   │   └── index.tsx
│       │   │   └── common/
│       │   │       ├── Button.tsx
│       │   │       ├── Input.tsx
│       │   │       ├── Modal.tsx
│       │   │       ├── Spinner.tsx
│       │   │       └── Toast.tsx
│       │   │
│       │   ├── pages/                # Route pages
│       │   │   ├── HomePage.tsx      # Upload + YouTube intake
│       │   │   ├── JobsPage.tsx      # Job list
│       │   │   ├── TranscriptPage.tsx # View/edit transcript
│       │   │   └── NotFoundPage.tsx
│       │   │
│       │   ├── hooks/                # Custom React hooks
│       │   │   ├── useJobs.ts        # Job list + polling
│       │   │   ├── useJob.ts         # Single job status
│       │   │   ├── useTranscript.ts  # Transcript CRUD
│       │   │   ├── useUpload.ts      # File upload logic
│       │   │   └── useConfig.ts      # Feature flags
│       │   │
│       │   ├── api/                  # API client
│       │   │   ├── client.ts         # Axios instance
│       │   │   ├── jobs.ts           # Job endpoints
│       │   │   ├── transcripts.ts    # Transcript endpoints
│       │   │   ├── youtube.ts        # YouTube endpoints
│       │   │   └── types.ts          # TypeScript types
│       │   │
│       │   ├── utils/                # Utilities
│       │   │   ├── formatters.ts     # Time/date formatting
│       │   │   └── validators.ts     # Client-side validation
│       │   │
│       │   └── styles/               # Global styles
│       │       ├── globals.css
│       │       └── variables.css
│       │
│       ├── tests/                    # Frontend tests
│       │   ├── setup.ts
│       │   └── components/
│       │       └── Upload.test.tsx
│       │
│       ├── Dockerfile
│       ├── package.json
│       ├── tsconfig.json
│       ├── vite.config.ts
│       └── tailwind.config.js
│
├── data/                             # Runtime data (GITIGNORED)
│   ├── db/
│   │   └── jobs.db                   # SQLite database
│   ├── uploads/                      # Uploaded files
│   │   └── {job_id}/
│   │       └── original.{ext}
│   ├── outputs/                      # Processed transcripts
│   │   └── {job_id}/
│   │       ├── audio.wav
│   │       ├── segments.json
│   │       ├── transcript.txt
│   │       ├── transcript.srt
│   │       └── transcript.vtt
│   └── logs/                         # Worker logs
│       └── {job_id}.log
│
├── docs/                             # Documentation
│   ├── architecture.md               # System architecture
│   ├── api_contract.md               # API specification
│   ├── db_schema.md                  # Database schema
│   ├── repo_structure.md             # This file
│   ├── requirements.md               # User stories (PM)
│   ├── test_plan.md                  # QA test plan
│   ├── security_checklist.md         # Security requirements
│   ├── local_dev.md                  # Development setup
│   ├── troubleshooting.md            # Common issues
│   ├── performance.md                # CPU vs GPU guidance
│   └── youtube_modes.md              # YouTube feature docs
│
├── scripts/                          # Utility scripts
│   ├── init-db.sh                    # Initialize database
│   ├── reset-data.sh                 # Clear all data
│   └── download-models.sh            # Pre-download Whisper models
│
├── .github/                          # GitHub config
│   └── workflows/
│       └── ci.yml                    # CI pipeline
│
├── docker-compose.yml                # Container orchestration
├── docker-compose.dev.yml            # Development overrides
├── Makefile                          # Common commands
├── .env.example                      # Environment template
├── .gitignore
├── LICENSE
└── README.md
```

---

## Component Details

### apps/api

**Purpose:** REST API server  
**Tech:** Python 3.11+, FastAPI, SQLite  
**Port:** 8000

**Key Files:**
- `main.py` — FastAPI app initialization, CORS, middleware
- `config.py` — Environment variables via Pydantic settings
- `database.py` — SQLite connection pool, query helpers

**Dependencies (requirements.txt):**
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6
pydantic>=2.5.0
pydantic-settings>=2.1.0
aiosqlite>=0.19.0
```

---

### apps/worker

**Purpose:** Background transcription processing  
**Tech:** Python 3.11+, faster-whisper, ffmpeg  
**Port:** None (background process)

**Key Files:**
- `main.py` — Polling loop, job dispatcher
- `handlers/` — Job type-specific processing logic
- `transcription/engine.py` — Whisper model loading + inference

**Dependencies (requirements.txt):**
```
faster-whisper>=0.10.0
ffmpeg-python>=0.2.0
yt-dlp>=2024.1.0  # Optional, for auto mode
pydantic>=2.5.0
aiosqlite>=0.19.0
```

---

### apps/web

**Purpose:** User interface  
**Tech:** React 18, Vite, TypeScript, Tailwind CSS  
**Port:** 3000

**Key Files:**
- `src/App.tsx` — Router setup
- `src/api/client.ts` — Axios instance with base URL
- `src/hooks/` — State management via custom hooks

**Dependencies (package.json):**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.17.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "typescript": "^5.3.0",
    "tailwindcss": "^3.4.0",
    "@types/react": "^18.2.0"
  }
}
```

---

## Environment Configuration

### .env.example

```bash
# API Server
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=./data/db/jobs.db

# Worker
WHISPER_MODEL=small
WHISPER_DEVICE=cpu  # or 'cuda' for GPU
POLL_INTERVAL_SECONDS=5

# Storage paths
UPLOAD_DIR=./data/uploads
OUTPUT_DIR=./data/outputs
LOG_DIR=./data/logs

# Limits
MAX_UPLOAD_SIZE_MB=500
ALLOWED_EXTENSIONS=mp3,mp4,wav,m4a,webm,ogg,mkv,avi

# Feature flags
YOUTUBE_SAFE_MODE=true
YOUTUBE_AUTO_INGEST=false

# Frontend
VITE_API_URL=http://localhost:8000
```

---

## Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: ./apps/api
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=/app/data/db/jobs.db
      - UPLOAD_DIR=/app/data/uploads
      - OUTPUT_DIR=/app/data/outputs
    depends_on:
      - init

  worker:
    build: ./apps/worker
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=/app/data/db/jobs.db
      - WHISPER_MODEL=${WHISPER_MODEL:-small}
      - WHISPER_DEVICE=${WHISPER_DEVICE:-cpu}
    depends_on:
      - api

  web:
    build: ./apps/web
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - api

  init:
    image: alpine
    volumes:
      - ./data:/data
    command: >
      sh -c "mkdir -p /data/db /data/uploads /data/outputs /data/logs"
```

---

## Makefile Commands

```makefile
.PHONY: up down logs dev test clean

# Start all services
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

# View logs
logs:
	docker compose logs -f

# Development mode (with hot reload)
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Run tests
test:
	cd apps/api && pytest
	cd apps/worker && pytest
	cd apps/web && npm test

# Clean data (careful!)
clean:
	rm -rf data/uploads/* data/outputs/* data/logs/*
	@echo "Uploads, outputs, and logs cleared. Database preserved."

# Full reset (destructive!)
reset:
	rm -rf data/*
	@echo "All data cleared."

# Initialize database
init-db:
	./scripts/init-db.sh

# Download Whisper models
models:
	./scripts/download-models.sh
```

---

## Conventions

### Naming
- **Files:** snake_case for Python, PascalCase for React components
- **Variables:** snake_case for Python, camelCase for TypeScript
- **Constants:** SCREAMING_SNAKE_CASE

### Code Style
- **Python:** Black + isort + ruff
- **TypeScript:** ESLint + Prettier
- **Commits:** Conventional commits (feat:, fix:, docs:, etc.)

### API Responses
- Always return `{"ok": true/false, "data": ...}` wrapper
- Use HTTP status codes correctly (201 for create, 404 for not found)

### File Storage
- Never use user-supplied filenames directly
- Always use job_id as directory name
- Keep original extension for debugging
