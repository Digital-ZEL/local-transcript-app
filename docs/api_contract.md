# API Contract

**Project:** Local Transcript App  
**Version:** 1.5  
**Base URL:** `http://localhost:8000/api`  
**Date:** February 2, 2026

---

## Overview

RESTful JSON API for job management, transcription, and export.

**Authentication:** None (local-only deployment)  
**Content-Type:** `application/json` (except file uploads)

---

## Common Response Formats

### Success Response
```json
{
  "ok": true,
  "data": { ... }
}
```

### Error Response
```json
{
  "ok": false,
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "File type not allowed. Supported: mp3, mp4, wav, m4a, webm, ogg, mkv, avi"
  }
}
```

### Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_FILE_TYPE` | 400 | Unsupported media format |
| `FILE_TOO_LARGE` | 413 | Exceeds max upload size |
| `INVALID_URL` | 400 | Malformed or disallowed URL |
| `FEATURE_DISABLED` | 403 | Feature flag not enabled |
| `JOB_NOT_FOUND` | 404 | Job ID doesn't exist |
| `EXPORT_NOT_READY` | 409 | Transcript not yet available |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Endpoints

### Health Check

#### GET /health

Check API server status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.5.0",
  "worker_connected": true
}
```

---

### File Upload

#### POST /api/upload

Upload an audio/video file for transcription.

**Request:**
- Content-Type: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | Media file (max 500MB) |
| `model` | string | No | Whisper model: `tiny`, `base`, `small`, `medium`, `large` (default: `small`) |
| `language` | string | No | ISO 639-1 code or `auto` (default: `auto`) |

**Allowed File Types:**
- Audio: `.mp3`, `.wav`, `.m4a`, `.ogg`
- Video: `.mp4`, `.webm`, `.mkv`, `.avi`

**Response (201 Created):**
```json
{
  "ok": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "queued",
    "created_at": "2026-02-02T12:00:00Z"
  }
}
```

**Errors:**
- `INVALID_FILE_TYPE` (400)
- `FILE_TOO_LARGE` (413)
- `RATE_LIMITED` (429)

---

### YouTube Intake

#### POST /api/youtube

Create a transcription job from a YouTube URL.

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "mode": "safe",
  "model": "small",
  "language": "auto"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | YouTube video URL |
| `mode` | string | No | `safe` (default) or `auto` |
| `model` | string | No | Whisper model (default: `small`) |
| `language` | string | No | Language code (default: `auto`) |

**Mode Behavior:**

| Mode | Requires Flag | Behavior |
|------|---------------|----------|
| `safe` | `YOUTUBE_SAFE_MODE=true` | Fetch captions only; fallback if unavailable |
| `auto` | `YOUTUBE_AUTO_INGEST=true` | Download audio and transcribe |

**Response (201 Created):**
```json
{
  "ok": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440001",
    "job_type": "youtube_captions",
    "status": "queued",
    "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "created_at": "2026-02-02T12:00:00Z"
  }
}
```

**Fallback Response (when captions unavailable in safe mode):**
```json
{
  "ok": true,
  "data": {
    "job_id": null,
    "status": "no_captions",
    "message": "No captions available for this video.",
    "fallback_options": [
      "Upload the audio/video file directly",
      "Paste caption text manually"
    ]
  }
}
```

**Errors:**
- `INVALID_URL` (400) — Not a valid YouTube URL
- `FEATURE_DISABLED` (403) — Mode not enabled via feature flag
- `RATE_LIMITED` (429)

---

#### POST /api/youtube/paste

Submit manually pasted captions for a YouTube video.

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "captions_text": "00:00 Hello everyone\n00:05 Today we're going to..."
}
```

**Response (201 Created):**
```json
{
  "ok": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440002",
    "job_type": "youtube_captions",
    "status": "queued",
    "created_at": "2026-02-02T12:00:00Z"
  }
}
```

---

### Jobs

#### GET /api/jobs

List all jobs with pagination.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `limit` | int | 20 | Items per page (max 100) |
| `status` | string | all | Filter by status |

**Response:**
```json
{
  "ok": true,
  "data": {
    "jobs": [
      {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "job_type": "file_upload",
        "status": "done",
        "original_filename": "interview.mp3",
        "created_at": "2026-02-02T12:00:00Z",
        "updated_at": "2026-02-02T12:05:00Z"
      },
      {
        "job_id": "550e8400-e29b-41d4-a716-446655440001",
        "job_type": "youtube_captions",
        "status": "running",
        "source_url": "https://youtube.com/watch?v=abc123",
        "created_at": "2026-02-02T12:10:00Z",
        "updated_at": "2026-02-02T12:10:30Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 42,
      "pages": 3
    }
  }
}
```

---

#### GET /api/jobs/{job_id}

Get detailed job status.

**Response (done):**
```json
{
  "ok": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_type": "file_upload",
    "status": "done",
    "original_filename": "interview.mp3",
    "source_url": null,
    "model": "small",
    "language": "en",
    "created_at": "2026-02-02T12:00:00Z",
    "updated_at": "2026-02-02T12:05:00Z",
    "duration_seconds": 300,
    "transcript_available": true
  }
}
```

**Response (failed):**
```json
{
  "ok": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440003",
    "job_type": "file_upload",
    "status": "failed",
    "original_filename": "corrupted.mp4",
    "error_message": "ffmpeg: Invalid data found when processing input",
    "created_at": "2026-02-02T12:00:00Z",
    "updated_at": "2026-02-02T12:01:00Z"
  }
}
```

**Errors:**
- `JOB_NOT_FOUND` (404)

---

#### DELETE /api/jobs/{job_id}

Delete a job and its associated files.

**Response:**
```json
{
  "ok": true,
  "data": {
    "deleted": true,
    "job_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Errors:**
- `JOB_NOT_FOUND` (404)

---

### Transcripts

#### GET /api/jobs/{job_id}/transcript

Get transcript content.

**Response:**
```json
{
  "ok": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "text": "Hello everyone. Today we're going to discuss...",
    "segments": [
      {
        "id": 0,
        "start": 0.0,
        "end": 2.5,
        "text": "Hello everyone."
      },
      {
        "id": 1,
        "start": 2.5,
        "end": 5.8,
        "text": "Today we're going to discuss..."
      }
    ],
    "language": "en",
    "duration": 300.0,
    "is_edited": false,
    "last_edited_at": null
  }
}
```

**Errors:**
- `JOB_NOT_FOUND` (404)
- `EXPORT_NOT_READY` (409) — Job not done yet

---

#### PUT /api/jobs/{job_id}/transcript

Update transcript text (save edits).

**Request:**
```json
{
  "text": "Hello everyone! Today we're going to discuss...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 2.5,
      "text": "Hello everyone!"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Full edited transcript |
| `segments` | array | No | Updated segment timestamps/text |

**Response:**
```json
{
  "ok": true,
  "data": {
    "saved": true,
    "last_edited_at": "2026-02-02T13:00:00Z"
  }
}
```

**Errors:**
- `JOB_NOT_FOUND` (404)
- `EXPORT_NOT_READY` (409)

---

### Export

#### GET /api/jobs/{job_id}/export

Download transcript in specified format.

**Query Parameters:**
| Param | Type | Default | Options |
|-------|------|---------|---------|
| `format` | string | txt | `txt`, `srt`, `vtt`, `json` |
| `edited` | bool | true | Use edited version if available |

**Response:**
- Content-Type varies by format
- Content-Disposition: `attachment; filename="transcript.{ext}"`

| Format | Content-Type | Description |
|--------|--------------|-------------|
| `txt` | text/plain | Plain text |
| `srt` | text/plain | SubRip subtitles |
| `vtt` | text/vtt | WebVTT subtitles |
| `json` | application/json | Segments with timestamps |

**Example JSON export:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "language": "en",
  "duration": 300.0,
  "segments": [
    {"id": 0, "start": 0.0, "end": 2.5, "text": "Hello everyone."},
    {"id": 1, "start": 2.5, "end": 5.8, "text": "Today we discuss..."}
  ]
}
```

**Example SRT export:**
```
1
00:00:00,000 --> 00:00:02,500
Hello everyone.

2
00:00:02,500 --> 00:00:05,800
Today we discuss...
```

**Errors:**
- `JOB_NOT_FOUND` (404)
- `EXPORT_NOT_READY` (409)

---

### Feature Flags

#### GET /api/config

Get current feature flag states.

**Response:**
```json
{
  "ok": true,
  "data": {
    "youtube_safe_mode": true,
    "youtube_auto_ingest": false,
    "max_upload_size_mb": 500,
    "allowed_file_types": ["mp3", "mp4", "wav", "m4a", "webm", "ogg", "mkv", "avi"],
    "default_model": "small"
  }
}
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /api/upload | 5 requests | 1 minute |
| POST /api/youtube | 10 requests | 1 minute |
| GET /api/jobs/* | 60 requests | 1 minute |
| All others | 100 requests | 1 minute |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1706875260
```

---

## WebSocket (Future)

Reserved for real-time job status updates:
```
WS /api/ws/jobs/{job_id}
```

Not implemented in v1.5 (polling used instead).

---

## Changelog

| Version | Changes |
|---------|---------|
| 1.5 | Added YouTube endpoints, feature flags |
| 1.0 | Initial API: upload, jobs, transcript, export |
