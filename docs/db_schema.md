# Database Schema

**Project:** Local Transcript App  
**Database:** SQLite 3  
**Location:** `./data/db/jobs.db`  
**Date:** February 2, 2026

---

## Overview

Single SQLite database file for simplicity. Local-first design means no concurrent access concerns for MVP.

---

## Schema Diagram

```
┌─────────────────────────────────────┐
│              jobs                    │
├─────────────────────────────────────┤
│ id (PK)                             │
│ job_type                            │
│ status                              │
│ source_url                          │
│ original_filename                   │
│ stored_filename                     │
│ model                               │
│ language                            │
│ duration_seconds                    │
│ error_message                       │
│ created_at                          │
│ updated_at                          │
└──────────────┬──────────────────────┘
               │ 1:1
               ▼
┌─────────────────────────────────────┐
│           transcripts                │
├─────────────────────────────────────┤
│ id (PK)                             │
│ job_id (FK → jobs.id)               │
│ segments_json_path                  │
│ plain_text_path                     │
│ srt_path                            │
│ vtt_path                            │
│ edited_text                         │
│ edited_segments_json                │
│ last_edited_at                      │
│ created_at                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          feature_flags               │
├─────────────────────────────────────┤
│ key (PK)                            │
│ value                               │
│ updated_at                          │
└─────────────────────────────────────┘
```

---

## Table Definitions

### jobs

Primary table tracking all transcription jobs.

```sql
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,                    -- UUID v4
    job_type TEXT NOT NULL                  -- 'file_upload' | 'youtube_captions' | 'youtube_auto_ingest'
        CHECK (job_type IN ('file_upload', 'youtube_captions', 'youtube_auto_ingest')),
    status TEXT NOT NULL DEFAULT 'queued'   -- 'queued' | 'running' | 'done' | 'failed'
        CHECK (status IN ('queued', 'running', 'done', 'failed')),
    
    -- Source information
    source_url TEXT,                        -- YouTube URL (for youtube_* job types)
    original_filename TEXT,                 -- Original uploaded filename (for file_upload)
    stored_filename TEXT,                   -- Sanitized filename in storage
    
    -- Processing options
    model TEXT NOT NULL DEFAULT 'small'     -- Whisper model: tiny, base, small, medium, large
        CHECK (model IN ('tiny', 'base', 'small', 'medium', 'large')),
    language TEXT NOT NULL DEFAULT 'auto',  -- ISO 639-1 code or 'auto'
    
    -- Results
    duration_seconds REAL,                  -- Media duration in seconds
    error_message TEXT,                     -- Error details if status = 'failed'
    
    -- Timestamps
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON jobs(job_type);
```

**Column Details:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | TEXT | No | UUID v4, e.g., `550e8400-e29b-41d4-a716-446655440000` |
| `job_type` | TEXT | No | Enum: `file_upload`, `youtube_captions`, `youtube_auto_ingest` |
| `status` | TEXT | No | Enum: `queued`, `running`, `done`, `failed` |
| `source_url` | TEXT | Yes | YouTube URL for YouTube job types |
| `original_filename` | TEXT | Yes | User's original filename |
| `stored_filename` | TEXT | Yes | UUID-based storage name |
| `model` | TEXT | No | Whisper model size |
| `language` | TEXT | No | Target language or `auto` |
| `duration_seconds` | REAL | Yes | Detected media duration |
| `error_message` | TEXT | Yes | Error details for failed jobs |
| `created_at` | TEXT | No | ISO 8601 timestamp |
| `updated_at` | TEXT | No | ISO 8601 timestamp |

---

### transcripts

Stores transcript metadata and file paths.

```sql
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL UNIQUE,            -- Foreign key to jobs.id
    
    -- Generated output paths (relative to ./data/outputs/{job_id}/)
    segments_json_path TEXT,                -- segments.json
    plain_text_path TEXT,                   -- transcript.txt
    srt_path TEXT,                          -- transcript.srt
    vtt_path TEXT,                          -- transcript.vtt
    
    -- User edits (stored inline for simplicity)
    edited_text TEXT,                       -- Full edited transcript text
    edited_segments_json TEXT,              -- JSON string of edited segments
    last_edited_at TEXT,                    -- When user last saved edits
    
    -- Timestamps
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_transcripts_job_id ON transcripts(job_id);
```

**Column Details:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | No | Auto-increment primary key |
| `job_id` | TEXT | No | References `jobs.id` |
| `segments_json_path` | TEXT | Yes | Path to segments.json |
| `plain_text_path` | TEXT | Yes | Path to transcript.txt |
| `srt_path` | TEXT | Yes | Path to transcript.srt |
| `vtt_path` | TEXT | Yes | Path to transcript.vtt |
| `edited_text` | TEXT | Yes | User-edited full text |
| `edited_segments_json` | TEXT | Yes | JSON array of edited segments |
| `last_edited_at` | TEXT | Yes | ISO 8601 timestamp |
| `created_at` | TEXT | No | ISO 8601 timestamp |

---

### feature_flags

Runtime configuration for feature toggles.

```sql
CREATE TABLE IF NOT EXISTS feature_flags (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,                    -- JSON-encoded value
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Insert default values
INSERT OR IGNORE INTO feature_flags (key, value) VALUES
    ('YOUTUBE_SAFE_MODE', 'true'),
    ('YOUTUBE_AUTO_INGEST', 'false'),
    ('MAX_UPLOAD_SIZE_MB', '500'),
    ('DEFAULT_MODEL', '"small"');
```

---

## Triggers

### Auto-update `updated_at`

```sql
CREATE TRIGGER IF NOT EXISTS jobs_updated_at
AFTER UPDATE ON jobs
FOR EACH ROW
BEGIN
    UPDATE jobs SET updated_at = datetime('now') WHERE id = OLD.id;
END;
```

---

## Migration Scripts

### V1: Initial Schema

```sql
-- migrations/001_initial.sql

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Create jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL CHECK (job_type IN ('file_upload', 'youtube_captions', 'youtube_auto_ingest')),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'done', 'failed')),
    source_url TEXT,
    original_filename TEXT,
    stored_filename TEXT,
    model TEXT NOT NULL DEFAULT 'small' CHECK (model IN ('tiny', 'base', 'small', 'medium', 'large')),
    language TEXT NOT NULL DEFAULT 'auto',
    duration_seconds REAL,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Create transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL UNIQUE,
    segments_json_path TEXT,
    plain_text_path TEXT,
    srt_path TEXT,
    vtt_path TEXT,
    edited_text TEXT,
    edited_segments_json TEXT,
    last_edited_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- Create feature_flags table
CREATE TABLE IF NOT EXISTS feature_flags (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_transcripts_job_id ON transcripts(job_id);

-- Create trigger
CREATE TRIGGER IF NOT EXISTS jobs_updated_at
AFTER UPDATE ON jobs
FOR EACH ROW
BEGIN
    UPDATE jobs SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- Insert default feature flags
INSERT OR IGNORE INTO feature_flags (key, value) VALUES
    ('YOUTUBE_SAFE_MODE', 'true'),
    ('YOUTUBE_AUTO_INGEST', 'false'),
    ('MAX_UPLOAD_SIZE_MB', '500'),
    ('DEFAULT_MODEL', '"small"');
```

---

## Sample Queries

### Create a new job

```sql
INSERT INTO jobs (id, job_type, original_filename, stored_filename, model, language)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'file_upload',
    'interview.mp3',
    '550e8400-e29b-41d4-a716-446655440000.mp3',
    'small',
    'en'
);
```

### Get queued jobs for worker

```sql
SELECT id, job_type, source_url, stored_filename, model, language
FROM jobs
WHERE status = 'queued'
ORDER BY created_at ASC
LIMIT 1;
```

### Update job status

```sql
UPDATE jobs
SET status = 'running'
WHERE id = '550e8400-e29b-41d4-a716-446655440000';
```

### Mark job complete with transcript

```sql
-- Update job
UPDATE jobs
SET status = 'done', duration_seconds = 300.5
WHERE id = '550e8400-e29b-41d4-a716-446655440000';

-- Insert transcript record
INSERT INTO transcripts (job_id, segments_json_path, plain_text_path, srt_path, vtt_path)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'outputs/550e8400-e29b-41d4-a716-446655440000/segments.json',
    'outputs/550e8400-e29b-41d4-a716-446655440000/transcript.txt',
    'outputs/550e8400-e29b-41d4-a716-446655440000/transcript.srt',
    'outputs/550e8400-e29b-41d4-a716-446655440000/transcript.vtt'
);
```

### Get job with transcript

```sql
SELECT 
    j.id,
    j.job_type,
    j.status,
    j.original_filename,
    j.source_url,
    j.duration_seconds,
    j.created_at,
    t.plain_text_path,
    t.edited_text,
    t.last_edited_at
FROM jobs j
LEFT JOIN transcripts t ON j.id = t.job_id
WHERE j.id = '550e8400-e29b-41d4-a716-446655440000';
```

### Save transcript edits

```sql
UPDATE transcripts
SET 
    edited_text = 'Hello everyone! Today we discuss...',
    edited_segments_json = '[{"id":0,"start":0.0,"end":2.5,"text":"Hello everyone!"}]',
    last_edited_at = datetime('now')
WHERE job_id = '550e8400-e29b-41d4-a716-446655440000';
```

### Get feature flag

```sql
SELECT value FROM feature_flags WHERE key = 'YOUTUBE_AUTO_INGEST';
```

### List recent jobs with pagination

```sql
SELECT 
    id,
    job_type,
    status,
    original_filename,
    source_url,
    created_at
FROM jobs
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

### Delete job and cascade

```sql
-- Foreign key ON DELETE CASCADE handles transcripts
DELETE FROM jobs WHERE id = '550e8400-e29b-41d4-a716-446655440000';
```

### Find stale running jobs (for recovery)

```sql
SELECT id, job_type, created_at
FROM jobs
WHERE status = 'running'
AND datetime(updated_at) < datetime('now', '-1 hour');
```

---

## Notes

1. **SQLite Pragmas** — Enable `PRAGMA foreign_keys = ON` at connection time
2. **Timestamps** — Stored as ISO 8601 text for readability and sorting
3. **JSON Storage** — `edited_segments_json` uses SQLite's JSON1 extension
4. **Migration Strategy** — Version files in `migrations/` folder, run in order
5. **Backup** — Simple file copy of `jobs.db` for full backup
