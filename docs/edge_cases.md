# Edge Cases & Error Handling — Local Transcript App

**Version:** 1.0  
**Author:** Product Manager  
**Date:** Feb 2, 2026

---

## Overview

This document catalogs edge cases, failure modes, and their UX fallbacks. Use this as a reference during development and QA testing.

**Severity Levels:**
- 🔴 **Critical:** Blocks core functionality, must handle
- 🟠 **High:** Degrades UX significantly, should handle
- 🟡 **Medium:** Inconvenient but workarounds exist
- 🟢 **Low:** Rare or minor impact

---

## 1. File Upload Edge Cases

### 1.1 🔴 File Too Large

**Scenario:** User uploads file exceeding size limit (500MB default)

**Detection:** Check `Content-Length` header before accepting upload

**Response:**
```json
{
  "error": "file_too_large",
  "message": "File exceeds 500MB limit. Please use a smaller file or split into segments.",
  "limit_mb": 500,
  "file_size_mb": 723
}
```

**UX Fallback:**
- Reject upload before consuming bandwidth
- Show file size and limit clearly
- Suggest: "Try trimming the file or using a lower quality version"

---

### 1.2 🔴 Invalid File Type (Extension Spoofing)

**Scenario:** User renames `malware.exe` to `audio.mp3`

**Detection:** 
1. Check file extension (first pass)
2. Check MIME type from file header (magic bytes)
3. Validate with ffprobe on backend

**Response:**
```json
{
  "error": "invalid_file_type",
  "message": "This file doesn't appear to be a valid audio/video file.",
  "detected_type": "application/x-executable",
  "expected_types": ["audio/*", "video/*"]
}
```

**UX Fallback:**
- Reject file immediately
- Don't store the file
- Log for security monitoring

---

### 1.3 🟠 Corrupted File

**Scenario:** File downloads incomplete or has encoding errors

**Detection:** ffmpeg/ffprobe returns error during normalization

**Response:**
```json
{
  "error": "corrupt_file",
  "message": "This file appears to be corrupted or incomplete. Please try downloading it again.",
  "ffmpeg_error": "Invalid data found when processing input"
}
```

**UX Fallback:**
- Job marked as FAILED
- Error message shown in job detail
- Suggest re-downloading or trying a different source

---

### 1.4 🟠 Video Without Audio Track

**Scenario:** User uploads video file that has no audio

**Detection:** ffprobe shows no audio streams

**Response:**
```json
{
  "error": "no_audio_track",
  "message": "This video file has no audio track to transcribe.",
  "streams": ["video/h264"]
}
```

**UX Fallback:**
- Reject before creating job
- Explain the issue clearly
- Suggest checking the source file

---

### 1.5 🟡 Very Short Audio (< 1 second)

**Scenario:** File is too short for meaningful transcription

**Detection:** Duration check after ffprobe

**Response:**
```json
{
  "error": "audio_too_short",
  "message": "Audio is less than 1 second. Please upload a longer file.",
  "duration_seconds": 0.3
}
```

**UX Fallback:**
- Reject with clear explanation
- Don't waste processing resources

---

### 1.6 🟡 Extremely Long Audio (> 8 hours)

**Scenario:** User uploads a very long file (full audiobook, conference recording)

**Detection:** Duration check after ffprobe

**Response:**
- For MVP: Accept but warn about processing time
- Show estimated completion time
- Allow user to cancel

**Warning Message:**
```
⚠️ Long File Detected

This file is 8 hours 23 minutes long.
Estimated processing time: ~4 hours (CPU) / ~50 minutes (GPU)

The transcript will be split into manageable segments.

[Cancel] [Continue Anyway]
```

---

### 1.7 🟡 Upload Interrupted (Network Drop)

**Scenario:** Network fails mid-upload

**Detection:** Upload stream ends prematurely

**Response:**
- Frontend shows connection error
- No partial file stored on backend
- Offer retry button

**UX Fallback:**
```
Upload interrupted. Please check your connection and try again.

[Retry Upload]
```

---

### 1.8 🟢 Unusual Audio Format (Valid but Rare)

**Scenario:** User uploads .opus, .aac, or other less common formats

**Detection:** ffprobe identifies codec

**Response:**
- Accept if ffmpeg can process it
- Log for format support analytics
- If unsupported: suggest conversion

**Behavior:** Best-effort transcoding via ffmpeg

---

## 2. Transcription Edge Cases

### 2.1 🔴 Worker Crashes Mid-Transcription

**Scenario:** Worker process dies during transcription

**Detection:** 
- Job stuck in "running" state for too long
- Worker heartbeat stops
- Process exit detected

**Response:**
- Job marked as FAILED
- Cleanup partial output files
- Error message explains the failure

**UX Fallback:**
```json
{
  "error": "transcription_failed",
  "message": "Transcription was interrupted unexpectedly. Please retry.",
  "suggestion": "Try a smaller file or different model"
}
```

**Recovery:**
- Auto-retry once with backoff
- If fails again, require manual retry

---

### 2.2 🔴 Out of Memory (OOM)

**Scenario:** Large file + large model exhausts RAM

**Detection:** Process killed by OOM killer

**Response:**
- Job marked as FAILED
- Specific error message about memory

**UX Fallback:**
```
Transcription failed: Not enough memory.

Suggestions:
• Try the "small" model instead of "large"
• Use a shorter audio segment
• Close other applications

[Retry with Small Model]
```

---

### 2.3 🟠 Inaudible or Silent Audio

**Scenario:** File contains silence or unintelligible audio

**Detection:** Whisper returns empty or near-empty transcript

**Response:**
- Job completes as "done" (not failed)
- Transcript contains minimal text
- Warning shown to user

**UX Message:**
```
⚠️ Limited Transcript

The transcription engine couldn't detect much speech in this audio.
This might be because:
• The audio is mostly silent
• Speech is too quiet or distorted
• Language wasn't detected correctly

Transcript: "[inaudible]"
```

---

### 2.4 🟠 Wrong Language Detection

**Scenario:** Auto-detect picks wrong language

**Detection:** User reports incorrect transcript

**Response:**
- Allow retry with manual language selection
- Show detected language in job details
- Suggest language hint

**UX Fallback:**
```
Detected language: Spanish (auto)

If this is incorrect, you can retry with a specific language:
[Retry with English] [Retry with Other...]
```

---

### 2.5 🟡 Mixed Languages in Audio

**Scenario:** Audio switches between languages

**Detection:** Whisper handles but accuracy varies

**Response:**
- Transcript may have errors at language boundaries
- Note this limitation in docs
- Suggest manual editing

**Behavior:** Best-effort transcription; may need manual cleanup

---

### 2.6 🟡 Heavy Accents or Dialects

**Scenario:** Regional accent affects accuracy

**Detection:** Lower confidence scores (if available)

**Response:**
- Transcription completes normally
- User may need to edit more
- Suggest using larger model for better accuracy

---

## 3. YouTube Edge Cases (v1.5 + v2)

### 3.1 🔴 Invalid YouTube URL

**Scenario:** URL doesn't match expected patterns

**Detection:** Regex validation on frontend + backend

**Response:**
```json
{
  "error": "invalid_youtube_url",
  "message": "Please enter a valid YouTube URL",
  "examples": [
    "https://www.youtube.com/watch?v=XXXXXXXXXXX",
    "https://youtu.be/XXXXXXXXXXX"
  ]
}
```

**UX:** Inline validation, don't submit to backend

---

### 3.2 🔴 Non-YouTube URL Attempted

**Scenario:** User pastes Vimeo, TikTok, or other platform URL

**Detection:** URL doesn't match youtube.com or youtu.be

**Response:**
```json
{
  "error": "unsupported_platform",
  "message": "Only YouTube URLs are supported. For other platforms, please download and upload the file.",
  "supported": ["youtube.com", "youtu.be"]
}
```

**UX Fallback:**
- Clear message about scope
- Link to file upload option

---

### 3.3 🔴 Private Video

**Scenario:** Video is private or unlisted (and not accessible)

**Detection:** API/scrape returns private status

**Response:**
```json
{
  "error": "video_private",
  "message": "This video is private. If you have access, please download and upload the file.",
  "video_id": "dQw4w9WgXcQ"
}
```

**UX Fallback:** Guide to download option

---

### 3.4 🔴 Video Deleted/Unavailable

**Scenario:** Video no longer exists

**Detection:** 404 or unavailable response

**Response:**
```json
{
  "error": "video_unavailable",
  "message": "This video is no longer available on YouTube.",
  "video_id": "dQw4w9WgXcQ"
}
```

**UX:** Clear message, suggest trying a different video

---

### 3.5 🟠 No Captions Available (Safe Mode)

**Scenario:** Video exists but has no captions

**Detection:** Caption track not found

**Response:**
```json
{
  "error": "no_captions",
  "message": "This video doesn't have captions available.",
  "fallback_options": ["upload", "paste_manual"]
}
```

**UX Fallback:**
```
ℹ️ No Captions Available

This video doesn't have captions we can import.

Options:
[📁 Upload the Audio/Video File]
[📋 Paste Captions Manually]
```

**IMPORTANT:** This is NOT an error state — it's a valid outcome that requires user action.

---

### 3.6 🟠 Captions Disabled by Owner

**Scenario:** Creator has disabled caption access

**Detection:** Captions blocked response

**Response:** Same as 3.5 but with different message:

```
Captions are disabled for this video by the creator.
```

---

### 3.7 🟠 Age-Restricted Video

**Scenario:** Video requires age verification

**Detection:** Age gate detected

**Response:**
```json
{
  "error": "age_restricted",
  "message": "This video is age-restricted. Please download and upload the file instead."
}
```

---

### 3.8 🟠 Region-Blocked Video

**Scenario:** Video not available in server's region

**Detection:** Geographic restriction response

**Response:**
```json
{
  "error": "region_blocked",
  "message": "This video isn't available in your region. Try using a VPN to download it, then upload the file."
}
```

---

### 3.9 🟠 Video Too Long (Auto Ingest v2)

**Scenario:** Video exceeds duration limit

**Detection:** Duration check before download

**Response:**
```json
{
  "error": "video_too_long",
  "message": "This video is 3 hours 15 minutes. Maximum allowed is 2 hours.",
  "duration_minutes": 195,
  "limit_minutes": 120
}
```

**UX Fallback:**
```
Video too long for auto-download (3h 15m).
Maximum: 2 hours

Options:
• Download the file manually and upload it
• Try a shorter video
```

---

### 3.10 🟠 Rate Limited (Our Limit)

**Scenario:** User exceeds our rate limit for Auto Ingest

**Detection:** Request counter in Redis/memory

**Response:**
```json
{
  "error": "rate_limited",
  "message": "You've reached the Auto Ingest limit. Please wait 45 minutes.",
  "retry_after_seconds": 2700,
  "limit": "5 per hour"
}
```

**UX:** Countdown timer, suggest Safe Mode or manual upload

---

### 3.11 🟡 Rate Limited (YouTube Side)

**Scenario:** YouTube blocks requests

**Detection:** 429 or equivalent response

**Response:**
```json
{
  "error": "upstream_rate_limit",
  "message": "YouTube is limiting requests. Please try again in a few minutes."
}
```

**UX:** Exponential backoff, suggest retry later

---

### 3.12 🟡 Network Timeout During Download

**Scenario:** Download starts but times out

**Detection:** Download timeout exceeded

**Response:**
- Job marked as FAILED
- Partial download cleaned up
- Offer retry

**UX:**
```
Download timed out. This could be due to:
• Slow internet connection
• YouTube server issues

[Retry Download]
```

---

### 3.13 🟢 Caption Language Mismatch

**Scenario:** Captions exist but not in expected language

**Detection:** Caption language metadata

**Response:**
- Import available language
- Note the language in job details
- Suggest checking if correct

**UX:**
```
Imported captions in Spanish.
If you expected English, the video may not have English captions available.
```

---

### 3.14 🟢 Auto-Generated vs Manual Captions

**Scenario:** Only auto-generated captions available (lower quality)

**Detection:** Caption metadata indicates auto-generated

**Response:**
- Import anyway but warn about quality
- Suggest editing may be needed

**UX:**
```
ℹ️ Auto-Generated Captions

These captions were auto-generated by YouTube and may contain errors.
We recommend reviewing and editing the transcript.

[View Transcript] [Try Auto Ingest Instead]
```

---

## 4. Export Edge Cases

### 4.1 🟠 Empty Transcript Export

**Scenario:** User exports transcript with no content

**Detection:** Transcript text is empty or whitespace

**Response:**
- Block export with message
- Suggest adding content first

**UX:**
```
Cannot export: Transcript is empty.
Please add some content or wait for transcription to complete.
```

---

### 4.2 🟡 Very Large Transcript (Export Timeout)

**Scenario:** Extremely long transcript takes too long to generate

**Detection:** Export generation exceeds timeout

**Response:**
- Stream the response instead of buffering
- Or generate async and notify when ready

---

### 4.3 🟡 Invalid Characters for SRT/VTT

**Scenario:** Transcript contains characters that break subtitle format

**Detection:** Validation during export generation

**Response:**
- Sanitize automatically
- Log what was changed
- Don't fail the export

---

## 5. System Edge Cases

### 5.1 🔴 Database Locked (SQLite)

**Scenario:** Concurrent writes cause lock contention

**Detection:** SQLite busy/locked error

**Response:**
- Retry with exponential backoff (up to 3 times)
- If persistent, show error

**Mitigation:** Use WAL mode, connection pooling

---

### 5.2 🔴 Disk Full

**Scenario:** Storage exhausted

**Detection:** Write fails with ENOSPC

**Response:**
```json
{
  "error": "storage_full",
  "message": "Server storage is full. Please delete old jobs or contact admin."
}
```

**Mitigation:** 
- Monitor disk usage
- Auto-cleanup old temp files
- Alert before critical threshold

---

### 5.3 🟠 Service Unavailable (Worker Down)

**Scenario:** Worker service not running

**Detection:** Job stuck in queued state

**Response:**
- Health check detects worker is down
- Frontend shows degraded status
- Jobs queue but don't process

**UX:**
```
⚠️ Transcription Service Unavailable

New jobs are being queued but won't process until the service is restored.
Please check docker-compose logs or restart the worker.
```

---

### 5.4 🟠 Model Not Downloaded

**Scenario:** Whisper model not present on first run

**Detection:** Model file missing

**Response:**
- Auto-download on first job (if online)
- Or fail with clear instructions

**UX:**
```
Downloading transcription model (whisper-medium, ~1.5GB)...
This only happens once.

[████████░░░░░░░░] 52% — 2:30 remaining
```

---

### 5.5 🟡 Time Sync Issues

**Scenario:** System clock is wrong, causing weird timestamps

**Detection:** Created timestamps in far past/future

**Response:**
- Log warning
- Use relative times where possible

---

## 6. Security Edge Cases

### 6.1 🔴 Path Traversal Attack

**Scenario:** Filename like `../../../etc/passwd`

**Detection:** Path validation rejects `..`, absolute paths

**Response:**
- Reject immediately
- Log for security audit
- Don't store anything

**Mitigation:**
```python
# Always use basename, never trust user paths
safe_name = os.path.basename(user_filename)
safe_name = re.sub(r'[^\w\-_\. ]', '_', safe_name)
```

---

### 6.2 🔴 Arbitrary URL Fetch (SSRF)

**Scenario:** Auto Ingest attempts to fetch internal URLs

**Detection:** URL validation against allowlist

**Response:**
- Reject any non-YouTube URL
- Never follow redirects to internal IPs
- Log attempt

**Mitigation:**
```python
ALLOWED_HOSTS = ['youtube.com', 'www.youtube.com', 'youtu.be']
# Validate hostname AFTER following redirects
```

---

### 6.3 🟠 Malicious Audio Payload

**Scenario:** Crafted file exploits ffmpeg vulnerability

**Detection:** Keep ffmpeg updated; sandbox if possible

**Mitigation:**
- Run ffmpeg with minimal privileges
- Use containerization
- Limit ffmpeg resource usage

---

## Top 3 Edge Cases to Watch ⚠️

Based on likelihood and impact, these are the most critical edge cases:

### 🥇 #1: No Captions Available (YouTube Safe Mode)

**Why it matters:** This is the *most common* outcome for Safe Link Mode. Many YouTube videos don't have captions. If we don't handle this gracefully, users will think the feature is broken.

**Must get right:**
- Clear, friendly messaging (not an error!)
- Obvious next steps (upload or paste)
- One-click path to alternatives
- Don't make users feel like they did something wrong

**Test cases:**
- Video with no captions
- Video with disabled captions
- Video with only foreign language captions

---

### 🥈 #2: Worker Crash / OOM During Transcription

**Why it matters:** Transcription is resource-intensive. Large files + large models can crash the worker. Users will lose progress and get frustrated.

**Must get right:**
- Detect crash quickly (don't leave jobs stuck)
- Clean up partial files
- Clear error message with actionable suggestion
- One-click retry with smaller model option

**Test cases:**
- Kill worker mid-job
- Upload large file with large model on low-memory system
- Multiple concurrent large jobs

---

### 🥉 #3: Invalid/Spoofed File Types

**Why it matters:** Security issue. Users might upload malicious files disguised as audio. This is both a security risk and a confusing UX if we process garbage.

**Must get right:**
- Validate file type beyond extension
- Use magic bytes / MIME detection
- Validate with ffprobe before accepting
- Never execute or store unvalidated files

**Test cases:**
- Rename .exe to .mp3
- Truncated file (partial download)
- File with wrong extension (mp4 named as mp3)
- Zero-byte file

---

## Edge Case Testing Checklist

### Before MVP Launch
- [ ] File too large rejected gracefully
- [ ] Invalid file type detected and rejected
- [ ] Corrupt file fails with clear message
- [ ] Worker crash doesn't leave zombie jobs
- [ ] Empty transcript blocks export
- [ ] Path traversal blocked

### Before v1.5 Launch
- [ ] Invalid YouTube URL rejected
- [ ] Non-YouTube URL rejected with message
- [ ] Private video handled
- [ ] No captions → fallback UI works
- [ ] Caption import creates valid transcript

### Before v2.0 Launch
- [ ] Feature flag respected (default off)
- [ ] Warning shown and acknowledged
- [ ] Duration limit enforced
- [ ] Rate limit enforced
- [ ] Download failure recovers gracefully
- [ ] Temp files cleaned up

---

## Error Message Guidelines

### Do ✅
- Be specific about what went wrong
- Suggest what to do next
- Use plain language
- Show relevant data (file size, duration, etc.)

### Don't ❌
- Show stack traces to users
- Use technical jargon
- Leave users without next steps
- Blame the user

### Example Transformation

**Bad:**
```
Error: ENOENT: no such file or directory, open '/data/uploads/abc123.mp3'
```

**Good:**
```
The uploaded file could not be found. This might happen if:
• The upload was interrupted
• The file was cleaned up automatically

Please try uploading again.

[Upload File]
```
