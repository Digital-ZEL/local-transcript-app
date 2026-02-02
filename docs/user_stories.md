# User Stories — Local Transcript App

**Version:** 1.0  
**Author:** Product Manager  
**Date:** Feb 2, 2026

---

## Story Format

Each user story follows this template:
- **As a** [user type]
- **I want to** [action]
- **So that** [benefit]
- **Acceptance Criteria:** Testable conditions
- **Error Scenarios:** What can go wrong and how we handle it

---

## Epic 1: File Upload & Transcription (MVP)

### US-1.1: Upload Audio File

**As a** user  
**I want to** upload an audio file from my computer  
**So that** I can get a text transcript of the audio content

**Acceptance Criteria:**
- [ ] Upload button/dropzone is visible on main page
- [ ] Drag-and-drop is supported
- [ ] Accepted formats: MP3, WAV, M4A, OGG, FLAC
- [ ] File size limit: 500MB (configurable)
- [ ] Upload progress indicator shows percentage
- [ ] On success: redirect to job status page
- [ ] Job ID is displayed to user

**Error Scenarios:**

| Error | Message | UX |
|-------|---------|-----|
| Invalid file type | "Unsupported file format. Please upload MP3, WAV, M4A, OGG, or FLAC." | Reject upload, stay on page |
| File too large | "File exceeds 500MB limit. Please use a smaller file." | Reject upload, show limit |
| Upload interrupted | "Upload failed. Please try again." | Show retry button |
| Server error | "Something went wrong. Please try again later." | Log error, show retry |

---

### US-1.2: Upload Video File

**As a** user  
**I want to** upload a video file from my computer  
**So that** I can extract and transcribe the audio track

**Acceptance Criteria:**
- [ ] Accepted formats: MP4, WebM, MKV, MOV
- [ ] Same upload UX as audio files
- [ ] System extracts audio track automatically
- [ ] Video file stored temporarily, audio extracted for processing
- [ ] Job created with original filename preserved

**Error Scenarios:**

| Error | Message | UX |
|-------|---------|-----|
| Invalid video format | "Unsupported video format. Please upload MP4, WebM, MKV, or MOV." | Reject upload |
| No audio track | "This video has no audio track." | Show message, suggest different file |
| Corrupt file | "File appears to be corrupted. Please try a different file." | Reject, suggest re-download |

---

### US-1.3: View Job Status

**As a** user  
**I want to** see the status of my transcription job  
**So that** I know when my transcript is ready

**Acceptance Criteria:**
- [ ] Job list shows all jobs (newest first)
- [ ] Each job displays: filename, status, created time
- [ ] Status values: Queued → Running → Done / Failed
- [ ] Running jobs show progress indicator (spinner or %)
- [ ] Auto-refresh every 5 seconds while job is active
- [ ] Clicking a job opens job detail page

**Status Indicators:**

| Status | Visual | Behavior |
|--------|--------|----------|
| Queued | 🕐 Gray badge | "Waiting to start" |
| Running | 🔄 Blue spinner | "Processing..." with elapsed time |
| Done | ✅ Green badge | "Complete" — clickable to view transcript |
| Failed | ❌ Red badge | "Failed" — shows error message |

**Error Scenarios:**

| Error | Message | UX |
|-------|---------|-----|
| Job not found | "Job not found. It may have been deleted." | Show message, link to job list |
| Server unavailable | "Cannot connect to server. Retrying..." | Auto-retry with backoff |

---

### US-1.4: View Transcript

**As a** user  
**I want to** view my completed transcript  
**So that** I can read and review the transcribed text

**Acceptance Criteria:**
- [ ] Transcript displays in readable format
- [ ] Timestamps shown for each segment (e.g., `[00:01:23]`)
- [ ] Segments are visually separated
- [ ] Scrollable for long transcripts
- [ ] Copy-to-clipboard button available
- [ ] Navigation to export and edit options visible

**Layout Example:**
```
[00:00:00] Welcome to the podcast. Today we're discussing...
[00:00:15] Our guest is a renowned expert in the field.
[00:00:32] Thank you for having me. I'm excited to be here.
```

---

### US-1.5: Edit Transcript

**As a** user  
**I want to** edit the transcript text  
**So that** I can fix transcription errors before exporting

**Acceptance Criteria:**
- [ ] Edit button enters edit mode
- [ ] Text is editable in-place (contenteditable or textarea)
- [ ] Timestamps are NOT editable (protected)
- [ ] Unsaved changes indicator shown (e.g., "Unsaved changes")
- [ ] Save button commits changes to database
- [ ] Cancel button discards changes (with confirmation if changes exist)
- [ ] Original transcript preserved (can restore)
- [ ] Last edited timestamp displayed

**Error Scenarios:**

| Error | Message | UX |
|-------|---------|-----|
| Save failed | "Could not save changes. Please try again." | Keep edit mode, show retry |
| Concurrent edit | "Transcript was modified elsewhere. Refresh to see latest." | Offer refresh or force save |
| Empty transcript | "Transcript cannot be empty." | Block save |

---

### US-1.6: Export Transcript

**As a** user  
**I want to** export my transcript in various formats  
**So that** I can use it in other applications

**Acceptance Criteria:**
- [ ] Export dropdown/buttons for: TXT, SRT, VTT, JSON
- [ ] TXT: Plain text with optional timestamps
- [ ] SRT: Valid SubRip subtitle format
- [ ] VTT: Valid WebVTT format
- [ ] JSON: Structured data with segments array
- [ ] Download starts immediately on click
- [ ] Filename matches original file (e.g., `interview.srt`)

**Export Format Specifications:**

**TXT Format:**
```
Welcome to the podcast. Today we're discussing...
Our guest is a renowned expert in the field.
Thank you for having me. I'm excited to be here.
```

**SRT Format:**
```
1
00:00:00,000 --> 00:00:15,000
Welcome to the podcast. Today we're discussing...

2
00:00:15,000 --> 00:00:32,000
Our guest is a renowned expert in the field.
```

**VTT Format:**
```
WEBVTT

00:00:00.000 --> 00:00:15.000
Welcome to the podcast. Today we're discussing...

00:00:15.000 --> 00:00:32.000
Our guest is a renowned expert in the field.
```

**JSON Format:**
```json
{
  "job_id": "abc123",
  "duration": 3600,
  "segments": [
    {"start": 0.0, "end": 15.0, "text": "Welcome to the podcast..."},
    {"start": 15.0, "end": 32.0, "text": "Our guest is a renowned expert..."}
  ]
}
```

---

## Epic 2: YouTube Safe Link Mode (v1.5)

### US-2.1: Paste YouTube URL

**As a** user  
**I want to** paste a YouTube video URL  
**So that** I can get a transcript without downloading the video manually

**Acceptance Criteria:**
- [ ] YouTube URL input field on main page (alongside file upload)
- [ ] Field validates URL format on blur/submit
- [ ] Accepted patterns: youtube.com/watch, youtu.be/, youtube.com/embed
- [ ] Submit button labeled "Get Transcript"
- [ ] Loading state while checking for captions

**URL Validation:**

| Input | Valid? | Action |
|-------|--------|--------|
| `https://www.youtube.com/watch?v=dQw4w9WgXcQ` | ✅ | Process |
| `https://youtu.be/dQw4w9WgXcQ` | ✅ | Process |
| `https://youtube.com/embed/dQw4w9WgXcQ` | ✅ | Process |
| `https://vimeo.com/123456` | ❌ | "Only YouTube URLs are supported" |
| `not a url` | ❌ | "Please enter a valid YouTube URL" |
| `https://youtube.com/` | ❌ | "Please enter a complete video URL" |

---

### US-2.2: Import Available Captions

**As a** user  
**I want to** automatically import captions when available  
**So that** I get a transcript instantly without waiting for transcription

**Acceptance Criteria:**
- [ ] System checks for caption availability
- [ ] If captions exist: import automatically
- [ ] Job created with type `youtube_captions`
- [ ] Redirect to transcript view
- [ ] Source URL displayed in job details
- [ ] User can edit imported captions like any transcript

**Success Flow:**
```
1. User pastes URL → clicks "Get Transcript"
2. System: "Checking for captions..."
3. Captions found → "Importing captions..."
4. Job created → Redirect to transcript view
5. Toast: "Captions imported successfully!"
```

---

### US-2.3: Handle Missing Captions (Fallback)

**As a** user  
**I want to** see clear next steps when captions aren't available  
**So that** I can still get a transcript through alternative means

**Acceptance Criteria:**
- [ ] If no captions: show fallback message (not an error)
- [ ] Message explains why and offers alternatives
- [ ] Two clear options: Upload File or Paste Captions
- [ ] "Upload File" navigates to upload with context preserved
- [ ] "Paste Captions" opens manual caption entry modal

**Fallback UI:**
```
╔══════════════════════════════════════════════════════════╗
║  ℹ️ No Captions Available                                ║
║                                                          ║
║  This video doesn't have captions we can import.         ║
║                                                          ║
║  You can still get a transcript by:                      ║
║                                                          ║
║  [📁 Upload the Audio/Video File]                        ║
║  Download the file and upload it for transcription       ║
║                                                          ║
║  [📋 Paste Captions Manually]                            ║
║  If you have captions text from another source           ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

**Error Scenarios:**

| Scenario | Message | Options |
|----------|---------|---------|
| No captions | "This video doesn't have captions we can import." | Upload / Paste |
| Captions disabled | "The video owner has disabled captions." | Upload / Paste |
| Private video | "This video is private or unavailable." | Try Another URL |
| Age-restricted | "This video is age-restricted." | Upload / Paste |
| Region blocked | "This video isn't available in your region." | Upload / Paste |

---

### US-2.4: Paste Captions Manually

**As a** user  
**I want to** paste caption text I copied from elsewhere  
**So that** I can import captions even when automatic retrieval fails

**Acceptance Criteria:**
- [ ] Modal/page with large text area
- [ ] Accepts plain text or SRT/VTT formatted text
- [ ] System parses and normalizes to standard format
- [ ] Creates job with type `youtube_captions`
- [ ] Links to original YouTube URL if provided
- [ ] Validation: minimum 10 characters

**Accepted Input Formats:**
1. Plain text (no timestamps) → stored as single segment
2. SRT format → parsed into segments
3. VTT format → parsed into segments
4. YouTube auto-generated (with timestamps) → best-effort parse

---

## Epic 3: YouTube Auto Ingest Mode (v2.0)

### US-3.1: Enable Auto Ingest Mode

**As an** admin/power user  
**I want to** enable Auto Ingest Mode via configuration  
**So that** I can use the automatic download feature when needed

**Acceptance Criteria:**
- [ ] Feature disabled by default (`YOUTUBE_AUTO_INGEST=false`)
- [ ] When enabled: mode toggle appears in YouTube URL UI
- [ ] Toggle labeled "Auto Transcribe" with info icon
- [ ] Feature flag checked on both frontend and backend
- [ ] If disabled: endpoint returns 403 with explanation

**Configuration:**
```env
YOUTUBE_AUTO_INGEST=true    # Enable the feature
YOUTUBE_MAX_DURATION=120    # Max video length in minutes
YOUTUBE_RATE_LIMIT=5        # Max requests per hour
```

---

### US-3.2: Acknowledge Usage Warning

**As a** user  
**I want to** see a clear warning about Auto Ingest Mode  
**So that** I understand the implications before using it

**Acceptance Criteria:**
- [ ] Warning modal shown on first Auto Ingest attempt
- [ ] Warning explains ToS considerations
- [ ] User must click "I Understand" to proceed
- [ ] Acknowledgment stored in localStorage (per browser)
- [ ] Warning re-shown if localStorage cleared
- [ ] Cancel returns to Safe Link Mode

**Warning Content:**
```
⚠️ Auto Ingest Mode

This feature downloads audio from YouTube for local transcription.

Important:
• Only use for content you have rights to transcribe
• Downloading may violate YouTube's Terms of Service
• This tool is for personal/educational use only
• You are responsible for compliance with applicable laws

By continuing, you acknowledge these considerations.

[Cancel]  [I Understand, Continue]
```

---

### US-3.3: Download and Transcribe

**As a** user  
**I want to** paste a YouTube URL and get a full transcript automatically  
**So that** I can transcribe videos without manually downloading them

**Acceptance Criteria:**
- [ ] After warning acknowledgment: process starts
- [ ] Progress shows: "Downloading audio..." → "Transcribing..."
- [ ] Audio-only downloaded (no video)
- [ ] Duration limit enforced before download starts
- [ ] Job created with type `youtube_auto_ingest`
- [ ] Temp audio file cleaned up after transcription
- [ ] On success: redirect to transcript view

**Progress Flow:**
```
1. "Checking video..." (duration, availability)
2. "Downloading audio..." (with progress bar)
3. "Transcribing..." (with progress bar)
4. "Complete!" → View Transcript
```

**Error Scenarios:**

| Error | Message | UX |
|-------|---------|-----|
| Video too long | "Video is X hours. Max allowed: 2 hours." | Offer truncated option or decline |
| Download blocked | "Could not download this video. Try uploading the file." | Fallback to upload |
| Rate limited (ours) | "Please wait X minutes before another Auto Ingest." | Show countdown |
| Rate limited (YouTube) | "Too many requests. Please try again later." | Suggest retry time |
| Network error | "Download failed. Check your connection." | Retry button |

---

## Epic 4: Job Management

### US-4.1: View All Jobs

**As a** user  
**I want to** see a list of all my transcription jobs  
**So that** I can track and manage my work

**Acceptance Criteria:**
- [ ] Jobs page shows all jobs in table/list
- [ ] Columns: Status, Name/Source, Type, Created, Duration
- [ ] Type badges: 📁 Upload, 🔗 Captions, ⬇️ Auto
- [ ] Sortable by date, status, name
- [ ] Filterable by status
- [ ] Pagination for 20+ jobs
- [ ] Click row to open job detail

---

### US-4.2: Delete Job

**As a** user  
**I want to** delete a job and its associated files  
**So that** I can clean up storage and remove unwanted transcripts

**Acceptance Criteria:**
- [ ] Delete button on job detail page
- [ ] Confirmation dialog before deletion
- [ ] Deletes: job record, transcript files, uploaded file
- [ ] Cannot delete jobs in "running" state
- [ ] Success message after deletion
- [ ] Redirect to jobs list

**Confirmation Dialog:**
```
Delete this job?

This will permanently delete:
• The transcript and all edits
• The uploaded file
• Export history

This cannot be undone.

[Cancel]  [Delete]
```

---

### US-4.3: Retry Failed Job

**As a** user  
**I want to** retry a failed transcription job  
**So that** I can recover from temporary errors

**Acceptance Criteria:**
- [ ] Retry button visible on failed jobs
- [ ] Retry creates new job with same source file
- [ ] Original failed job preserved (for debugging)
- [ ] User can choose different model/language on retry
- [ ] Rate limit: max 3 retries per original job

---

## Epic 5: Settings & Configuration

### US-5.1: Select Transcription Model

**As a** user  
**I want to** choose the transcription model  
**So that** I can balance speed vs. accuracy

**Acceptance Criteria:**
- [ ] Model dropdown on upload form
- [ ] Options: Small (fast), Medium (balanced), Large (accurate)
- [ ] Default: Medium
- [ ] Model descriptions shown
- [ ] Setting persisted per session

**Model Options:**
| Model | Speed | Accuracy | Size |
|-------|-------|----------|------|
| Small | ⚡⚡⚡ | ⭐⭐ | ~500MB |
| Medium | ⚡⚡ | ⭐⭐⭐ | ~1.5GB |
| Large | ⚡ | ⭐⭐⭐⭐ | ~3GB |

---

### US-5.2: Set Language Hint

**As a** user  
**I want to** specify the audio language  
**So that** I can improve transcription accuracy for non-English content

**Acceptance Criteria:**
- [ ] Language dropdown on upload form
- [ ] Options: Auto-detect (default), English, Spanish, French, etc.
- [ ] Auto-detect works for most content
- [ ] Language hint improves accuracy for specified language
- [ ] Saved as job metadata

---

## Acceptance Criteria Checklist Summary

### MVP Must-Pass Tests

- [ ] Upload MP3 file → job created → transcript appears
- [ ] Upload MP4 file → audio extracted → transcript appears
- [ ] Job status updates in real-time (Queued → Running → Done)
- [ ] Edit transcript → save → changes persist on refresh
- [ ] Export SRT → valid subtitle file opens in VLC
- [ ] Export VTT → valid file plays in HTML5 video
- [ ] Export JSON → valid JSON with segments array
- [ ] Failed job shows error message
- [ ] `docker compose up` starts all services

### v1.5 Must-Pass Tests

- [ ] Paste valid YouTube URL → captions imported (if available)
- [ ] Paste URL without captions → fallback UI shown
- [ ] Invalid URL → validation error shown
- [ ] Non-YouTube URL → rejected with message
- [ ] Paste captions manually → job created

### v2.0 Must-Pass Tests

- [ ] Feature disabled by default
- [ ] Warning shown on first use
- [ ] Download + transcribe completes successfully
- [ ] Duration limit enforced
- [ ] Temp files cleaned up
- [ ] Rate limit enforced
