# Architecture Document

**Project:** Local Transcript App  
**Version:** 1.5 (Safe Link Mode)  
**Author:** Tech Lead / Architect  
**Date:** February 2, 2026

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LOCAL TRANSCRIPT APP                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐        │
│   │              │  HTTP   │              │  Queue  │              │        │
│   │   Frontend   │◄───────►│   API Server │◄───────►│    Worker    │        │
│   │   (React)    │         │   (FastAPI)  │         │  (Whisper)   │        │
│   │              │         │              │         │              │        │
│   └──────────────┘         └──────┬───────┘         └──────┬───────┘        │
│        :3000                      │ :8000                  │                │
│                                   │                        │                │
│                            ┌──────▼────────────────────────▼──────┐         │
│                            │           Shared Storage             │         │
│                            │  ┌─────────────┐  ┌───────────────┐  │         │
│                            │  │   SQLite    │  │  Filesystem   │  │         │
│                            │  │  (jobs.db)  │  │   (./data/)   │  │         │
│                            │  └─────────────┘  └───────────────┘  │         │
│                            └──────────────────────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Boundaries

### 2.1 Frontend (apps/web)

**Responsibility:** User interface for all interactions  
**Technology:** React + Vite + TypeScript  
**Port:** 3000

**Capabilities:**
- File upload with progress tracking
- YouTube URL input with mode selection
- Job list with status polling (5-second intervals)
- Transcript viewer with timestamp navigation
- Inline transcript editing
- Export downloads (TXT, SRT, VTT, JSON)

**Does NOT:**
- Process files directly
- Access SQLite database
- Make external network calls (except to local API)

---

### 2.2 API Server (apps/api)

**Responsibility:** REST API, validation, job orchestration  
**Technology:** Python 3.11+ / FastAPI  
**Port:** 8000

**Capabilities:**
- File upload validation (type, size)
- YouTube URL validation (domain allowlist)
- Job creation and status management
- Transcript retrieval and updates
- Export file generation
- Feature flag enforcement

**Does NOT:**
- Run transcription directly
- Download YouTube content (delegates to worker)
- Serve the frontend (separate container)

---

### 2.3 Worker Service (apps/worker)

**Responsibility:** Media processing and transcription  
**Technology:** Python 3.11+ / faster-whisper / ffmpeg

**Capabilities:**
- Poll for queued jobs
- Normalize audio via ffmpeg
- Run Whisper transcription
- Generate output formats (TXT, SRT, VTT, JSON)
- Handle YouTube caption parsing (safe mode)
- Handle YouTube audio extraction (auto mode, if enabled)

**Does NOT:**
- Expose HTTP endpoints
- Accept direct user input
- Modify job records (except status updates)

---

### 2.4 Storage Layer

#### SQLite Database (./data/db/jobs.db)
- Job records with status lifecycle
- Transcript metadata and paths
- Feature flags state (optional)

#### Filesystem (./data/)
```
./data/
├── db/
│   └── jobs.db              # SQLite database
├── uploads/                 # Incoming media files
│   └── {job_id}/
│       └── original.{ext}   # Uploaded file
├── outputs/                 # Processed transcripts
│   └── {job_id}/
│       ├── audio.wav        # Normalized audio
│       ├── segments.json    # Timestamped segments
│       ├── transcript.txt   # Plain text
│       ├── transcript.srt   # SubRip format
│       ├── transcript.vtt   # WebVTT format
│       └── edited.txt       # User edits (if any)
└── logs/                    # Worker logs per job
    └── {job_id}.log
```

---

## 3. Data Flow Diagrams

### 3.1 File Upload Flow

```
User                Frontend              API                  Worker
 │                     │                   │                     │
 │──Upload file───────►│                   │                     │
 │                     │──POST /api/upload─►│                    │
 │                     │                   │──Validate file──────│
 │                     │                   │──Store in uploads/──│
 │                     │                   │──Create job (queued)│
 │                     │◄──{job_id}────────│                     │
 │◄──Show job status───│                   │                     │
 │                     │                   │                     │
 │                     │                   │◄──Poll for jobs─────│
 │                     │                   │                     │──Process:
 │                     │                   │                     │  1. ffmpeg normalize
 │                     │                   │                     │  2. whisper transcribe
 │                     │                   │                     │  3. generate outputs
 │                     │                   │◄──Update status─────│
 │                     │                   │   (done/failed)     │
 │                     │──GET /api/jobs/{id}►│                   │
 │                     │◄──{status: done}──│                     │
 │◄──Transcript ready──│                   │                     │
```

### 3.2 YouTube Safe Mode Flow

```
User                Frontend              API                  Worker
 │                     │                   │                     │
 │──Paste YT URL──────►│                   │                     │
 │                     │──POST /api/youtube─►│                   │
 │                     │   {url, mode:safe} │──Validate URL──────│
 │                     │                   │──Check captions────►│ (external)
 │                     │                   │◄──Captions found────│
 │                     │                   │──Create job─────────│
 │                     │◄──{job_id}────────│                     │
 │                     │                   │                     │
 │                     │                   │◄──Poll for jobs─────│
 │                     │                   │                     │──Parse captions
 │                     │                   │                     │──Generate outputs
 │                     │                   │◄──Update status─────│
 │◄──Transcript ready──│                   │                     │
```

### 3.3 YouTube Auto Mode Flow (v2, Feature-Flagged)

```
User                Frontend              API                  Worker
 │                     │                   │                     │
 │──Paste YT URL──────►│                   │                     │
 │                     │──POST /api/youtube─►│                   │
 │                     │   {url, mode:auto} │──Check flag────────│
 │                     │                   │   YOUTUBE_AUTO_INGEST?
 │                     │                   │──Create job─────────│
 │                     │◄──{job_id}────────│                     │
 │                     │                   │                     │
 │                     │                   │◄──Poll for jobs─────│
 │                     │                   │                     │──yt-dlp extract
 │                     │                   │                     │──ffmpeg normalize
 │                     │                   │                     │──whisper transcribe
 │                     │                   │◄──Update status─────│
 │◄──Transcript ready──│                   │                     │
```

---

## 4. Job Types

| Job Type | Source | Processing | Feature Flag |
|----------|--------|------------|--------------|
| `file_upload` | User-uploaded media file | ffmpeg → whisper | Always enabled |
| `youtube_captions` | YouTube URL (captions available) | Parse existing captions | `YOUTUBE_SAFE_MODE` |
| `youtube_auto_ingest` | YouTube URL (no captions) | yt-dlp → ffmpeg → whisper | `YOUTUBE_AUTO_INGEST` |

---

## 5. Job State Machine

```
                    ┌─────────┐
                    │ QUEUED  │
                    └────┬────┘
                         │ Worker picks up
                         ▼
                    ┌─────────┐
              ┌─────│ RUNNING │─────┐
              │     └─────────┘     │
              │ Success             │ Error
              ▼                     ▼
         ┌────────┐           ┌────────┐
         │  DONE  │           │ FAILED │
         └────────┘           └────────┘
```

**Status Values:**
- `queued` — Job created, waiting for worker
- `running` — Worker processing
- `done` — Transcript available
- `failed` — Error occurred (see error_message)

---

## 6. Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `YOUTUBE_SAFE_MODE` | `true` | Enable YouTube caption fetching |
| `YOUTUBE_AUTO_INGEST` | `false` | Enable YouTube audio extraction (ToS risk) |

**Enforcement:**
- API checks flags before creating YouTube jobs
- Frontend hides/disables UI based on flag state
- Worker skips incompatible job types

---

## 7. Security Boundaries

### 7.1 Input Validation
- **File types:** Allowlist only (mp3, mp4, m4a, wav, webm, ogg, mkv, avi)
- **File size:** Max 500MB (configurable)
- **YouTube domains:** `youtube.com`, `youtu.be`, `www.youtube.com` only
- **Filenames:** Sanitized, stored by job_id

### 7.2 Path Isolation
- All files stored under `./data/` only
- Job IDs are UUIDs (non-guessable)
- No user-supplied paths accepted

### 7.3 Rate Limiting
- Upload: 5 requests/minute per IP
- YouTube: 10 requests/minute per IP
- API-level enforcement via middleware

---

## 8. Scalability Considerations

### MVP (Current)
- Single worker process
- SQLite for persistence
- In-memory job queue (polling-based)

### Future (v2+)
- Redis + Celery for reliable queuing
- Multiple worker replicas
- PostgreSQL for concurrent access
- Horizontal scaling via Docker Swarm/K8s

---

## 9. Error Handling Strategy

| Error Type | Handling |
|------------|----------|
| Invalid file type | 400 response, job not created |
| File too large | 413 response, job not created |
| Invalid YouTube URL | 400 response with guidance |
| Transcription failure | Job marked `failed`, error logged |
| Worker crash | Job stays `running`, manual intervention |

**Recovery:**
- Stale `running` jobs (>1 hour) flagged for review
- Failed jobs retain partial outputs if available
- Logs stored per job for debugging

---

## 10. Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| SQLite over Postgres | Local-first, zero config, sufficient for single-user |
| Filesystem for media | Simpler than blob storage, better for large files |
| Separate worker process | Isolates long-running tasks, enables future scaling |
| Feature flags for YouTube | Legal flexibility, clear opt-in for risky features |
| UUID job IDs | Non-enumerable, secure by default |
| Polling over WebSockets | Simpler implementation, acceptable latency |
