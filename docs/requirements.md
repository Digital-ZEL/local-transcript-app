# Requirements Document — Local Transcript App

**Version:** 1.0  
**Author:** Product Manager  
**Date:** Feb 2, 2026

---

## Executive Summary

Local Transcript App is a self-hosted transcription tool that runs entirely on your machine. It converts audio/video files to timestamped text transcripts with editing and export capabilities. Version 1.5 adds YouTube URL support with a privacy-first approach.

---

## Version Roadmap

| Version | Codename | Focus | Risk Level |
|---------|----------|-------|------------|
| **MVP (v1.0)** | Core Engine | File upload → transcript → export | Low |
| **v1.5** | Safe Link Mode | YouTube captions retrieval (compliant) | Low |
| **v2.0** | Auto Ingest Mode | YouTube download + transcribe | Medium |

---

## MVP (v1.0) — Core Transcription

### Scope

The MVP delivers a complete local transcription workflow:

**IN SCOPE:**
- Upload audio/video files via browser
- Queue-based job processing with visible status
- Whisper-based local transcription with timestamps
- View and edit transcripts in browser
- Export to TXT, SRT, VTT, JSON formats
- Single-command Docker Compose startup
- SQLite storage (no external DB required)

**OUT OF SCOPE (MVP):**
- YouTube URL intake (deferred to v1.5)
- Speaker diarization
- Real-time streaming transcription
- Cloud/API integrations
- User authentication
- Multi-language UI

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| MVP-1 | User can upload audio files (mp3, wav, m4a, ogg, flac) | P0 |
| MVP-2 | User can upload video files (mp4, webm, mkv, mov) | P0 |
| MVP-3 | System creates job with unique ID on upload | P0 |
| MVP-4 | User can view job status (queued/running/done/failed) | P0 |
| MVP-5 | Worker normalizes media via ffmpeg before transcription | P0 |
| MVP-6 | Worker transcribes using faster-whisper or whisper.cpp | P0 |
| MVP-7 | Transcript includes word-level or segment timestamps | P0 |
| MVP-8 | User can view transcript with timestamps in browser | P0 |
| MVP-9 | User can edit transcript text and save changes | P0 |
| MVP-10 | User can export transcript as TXT (plain text) | P0 |
| MVP-11 | User can export transcript as SRT (subtitles) | P0 |
| MVP-12 | User can export transcript as VTT (web subtitles) | P0 |
| MVP-13 | User can export transcript as JSON (structured) | P0 |
| MVP-14 | Failed jobs show error message | P1 |
| MVP-15 | User can select transcription model (small/medium/large) | P1 |
| MVP-16 | User can set language hint (auto-detect default) | P1 |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Single-command startup | `docker compose up` |
| NFR-2 | Max upload size | 500MB (configurable) |
| NFR-3 | Supported audio codecs | MP3, WAV, M4A, OGG, FLAC |
| NFR-4 | Supported video codecs | MP4, WebM, MKV, MOV |
| NFR-5 | Offline operation | 100% local after model download |
| NFR-6 | Startup time | < 30 seconds |
| NFR-7 | Transcription speed | ~1x realtime (CPU), ~10x (GPU) |

---

## v1.5 — Safe Link Mode (YouTube Captions)

### Scope

v1.5 adds the ability to paste YouTube URLs and retrieve existing captions without downloading video content.

**IN SCOPE:**
- YouTube URL input field
- Caption availability check (compliant method)
- Auto-import captions when available
- Fallback guidance when captions unavailable
- Job type: `youtube_captions`

**OUT OF SCOPE (v1.5):**
- Automatic video/audio download
- Transcription of videos without captions
- Non-YouTube platforms

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| YT-1 | User can paste YouTube URL in dedicated input | P0 |
| YT-2 | System validates URL format (youtube.com, youtu.be only) | P0 |
| YT-3 | System checks for available captions | P0 |
| YT-4 | If captions exist: import and create transcript job | P0 |
| YT-5 | If no captions: show clear fallback message | P0 |
| YT-6 | Fallback offers: upload file OR paste captions manually | P0 |
| YT-7 | Imported captions stored in standard transcript format | P0 |
| YT-8 | User can edit imported captions like any transcript | P0 |
| YT-9 | Export works identically for caption-sourced transcripts | P0 |
| YT-10 | Job shows source_url in job details | P1 |

### Fallback Scenarios

| Scenario | User Message | Action Options |
|----------|--------------|----------------|
| No captions available | "This video doesn't have captions. You can upload the audio/video file or paste captions manually." | [Upload File] [Paste Captions] |
| Captions disabled by owner | "Captions are disabled for this video." | [Upload File] [Paste Captions] |
| Private/unavailable video | "This video is private or unavailable." | [Try Another URL] |
| Invalid URL | "Please enter a valid YouTube URL." | (stay on form) |
| Rate limited | "Too many requests. Please wait a moment." | (auto-retry or manual retry) |

---

## v2.0 — Auto Ingest Mode (Feature-Flagged)

### Scope

v2.0 adds the ability to automatically download YouTube audio and transcribe it locally. **This feature is disabled by default** and requires explicit opt-in.

**IN SCOPE:**
- YouTube audio extraction via yt-dlp
- Local transcription of downloaded audio
- Feature flag: `YOUTUBE_AUTO_INGEST=false` (default)
- Clear warning UI when enabled
- Duration limits and rate limiting
- Job type: `youtube_auto_ingest`

**OUT OF SCOPE (v2.0):**
- Other video platforms
- Playlist support
- Live stream transcription

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| AUTO-1 | Feature disabled by default (env flag) | P0 |
| AUTO-2 | When enabled: mode toggle visible in UI | P0 |
| AUTO-3 | Warning shown before first Auto Ingest use | P0 |
| AUTO-4 | System downloads audio-only (no video) | P0 |
| AUTO-5 | Max duration limit enforced (default: 2 hours) | P0 |
| AUTO-6 | Downloaded audio processed through normal transcription | P0 |
| AUTO-7 | Temporary audio files cleaned up after transcription | P0 |
| AUTO-8 | Rate limiting: max 5 requests per hour per IP | P1 |
| AUTO-9 | Progress indicator for download + transcription | P1 |
| AUTO-10 | Error handling for blocked/unavailable videos | P0 |

### Warning Message (Required Display)

```
⚠️ Auto Ingest Mode

This feature downloads audio from YouTube for local transcription.

• Only use for content you have rights to transcribe
• Downloading may violate YouTube's Terms of Service
• This tool is for personal/educational use only
• You are responsible for compliance with applicable laws

[I Understand, Continue] [Cancel]
```

### Configuration

```env
# Feature Flags
YOUTUBE_SAFE_MODE=true          # Always enabled
YOUTUBE_AUTO_INGEST=false       # Disabled by default

# Limits (when Auto Ingest enabled)
YOUTUBE_MAX_DURATION_MINUTES=120
YOUTUBE_RATE_LIMIT_PER_HOUR=5
```

---

## Success Metrics

### MVP Success Criteria

| Metric | Target |
|--------|--------|
| Upload → Transcript success rate | > 95% |
| Transcription accuracy (WER) | < 15% on clear audio |
| Export format correctness | 100% valid SRT/VTT |
| Startup without errors | 100% |
| Fresh install to first transcript | < 15 minutes |

### v1.5 Success Criteria

| Metric | Target |
|--------|--------|
| Valid YouTube URL acceptance | 100% |
| Caption retrieval success (when available) | > 90% |
| Clear fallback messaging | 100% |

### v2.0 Success Criteria

| Metric | Target |
|--------|--------|
| Feature flag respects default=off | 100% |
| Warning displayed before first use | 100% |
| Duration limit enforced | 100% |
| Cleanup of temp files | 100% |

---

## Dependencies

### External Dependencies

| Dependency | Purpose | Required By |
|------------|---------|-------------|
| ffmpeg | Audio normalization | MVP |
| faster-whisper / whisper.cpp | Transcription | MVP |
| SQLite | Job & transcript storage | MVP |
| Docker | Containerization | MVP |
| yt-dlp | YouTube audio extraction | v2.0 only |

### Model Dependencies

| Model | Size | Accuracy | Speed |
|-------|------|----------|-------|
| whisper-small | ~500MB | Good | Fast |
| whisper-medium | ~1.5GB | Better | Medium |
| whisper-large | ~3GB | Best | Slow |

---

## Constraints

1. **Privacy First:** All processing must happen locally. No data leaves the machine.
2. **Offline Capable:** After initial model download, internet not required.
3. **Single Command:** Must boot with `docker compose up` or equivalent.
4. **No Authentication:** MVP targets single-user local use.
5. **Legal Compliance:** Auto Ingest mode requires explicit user acknowledgment.

---

## Appendix: File Type Allowlist

### Audio (MVP)
- `.mp3` — MPEG Audio Layer 3
- `.wav` — Waveform Audio
- `.m4a` — MPEG-4 Audio
- `.ogg` — Ogg Vorbis
- `.flac` — Free Lossless Audio Codec

### Video (MVP)
- `.mp4` — MPEG-4 Part 14
- `.webm` — WebM
- `.mkv` — Matroska Video
- `.mov` — QuickTime

### YouTube URL Patterns (v1.5+)
- `https://www.youtube.com/watch?v=XXXXXXXXXXX`
- `https://youtube.com/watch?v=XXXXXXXXXXX`
- `https://youtu.be/XXXXXXXXXXX`
- `https://www.youtube.com/embed/XXXXXXXXXXX`
