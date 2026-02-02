# Local Transcript Website — Project Spec

**Created:** Feb 2, 2026  
**Status:** Ready to Build (v1.5 with YouTube intake)

---

## 1) Goal

Build a local-only transcript website you can run on a laptop or home server that lets you:
- Upload audio/video files
- Generate transcripts locally (no cloud calls)
- View, edit, and export transcripts (TXT, SRT, VTT, JSON)
- Track transcription jobs (queued/running/done/failed)
- Paste a YouTube link and get a transcript via one of two modes (below)

---

## 1.5) YouTube Link Intake Modes (New)

### Mode A: Safe Link Mode (recommended for v1.5)

**What it does:**
- User pastes a YouTube URL
- App tries to retrieve captions only when available via approved/legit methods (user-provided captions text or compliant API flow)
- If captions unavailable, app guides user to either:
  - Upload a file (audio/video), or
  - Paste captions manually

**Why:**
- Avoids automatic downloading/extraction and reduces ToS/legal risk
- Still gives the "paste link" convenience for workflows

### Mode B: Auto Ingest Mode (optional v2)

**What it does:**
- User pastes a YouTube URL
- App automatically downloads/extracts audio, then transcribes locally

**Risk note:**
- This is the "one-click magic" experience, but can violate platform terms depending on implementation and usage
- If you build this, treat it as explicit opt-in module with clear warnings and strict limits

---

## 2) Success Criteria (Definition of Done)

The project is done when:
1. A user can upload an audio/video file through the browser.
2. A job is created and job status is visible (queued/running/done/failed).
3. A transcript is generated with timestamps.
4. The transcript is viewable and editable in the browser.
5. Exports work: TXT, SRT, VTT, JSON.
6. Everything runs locally via one command (Docker Compose preferred).
7. **(New)** A user can paste a YouTube link and:
   - **v1.5 Safe Link Mode:** obtain captions if available or be routed to upload/paste captions
   - **v2 Auto Ingest Mode:** optionally generate transcript from link end-to-end

---

## 3) System Architecture (High-Level)

### Components

1. **Frontend Web App (React + Vite)**
   - Upload UI
   - **YouTube link intake UI** (new)
   - Jobs list with status polling
   - Transcript viewer/editor
   - Export controls

2. **API Server (Python FastAPI)**
   - File upload + validation
   - **YouTube link intake endpoint(s)** (new)
   - Job creation + status
   - Transcript storage + retrieval
   - Edit-save endpoint
   - Export endpoints

3. **Worker Service**
   - Pulls queued jobs
   - Normalizes media to clean audio (ffmpeg)
   - Runs transcription engine
   - Writes transcript outputs + updates job status
   - **(New)** Optionally handles YouTube ingest jobs, depending on mode

4. **Storage**
   - Filesystem: ./data/uploads, ./data/outputs
   - SQLite DB: jobs + transcript metadata + edits

5. **Optional Queue**
   - MVP: simple background tasks
   - Next: Redis + Celery for reliability and concurrency

---

## 4) Tech Stack (Recommended Defaults)

- **Frontend:** React + Vite
- **Backend:** FastAPI (Python)
- **Worker/Transcription:** faster-whisper (GPU optional) or whisper.cpp (fast CPU)
- **Media handling:** ffmpeg
- **DB:** SQLite
- **Packaging:** Docker Compose

---

## 5) Agent Team (Roles, Responsibilities, Deliverables)

### Agent 1: Product Manager (PM)

**Responsibilities**
- Define MVP scope and priorities
- **Add YouTube intake modes and decide what ships in v1.5 vs v2** (new)
- Write user stories + acceptance criteria
- **Define explicit user messaging for Auto Ingest Mode risk** (new)
- Identify edge cases and success metrics

**Deliverables**
- docs/requirements.md
- MVP + v1.5 + v2 user stories + acceptance criteria
- Edge cases list

---

### Agent 2: Tech Lead / Architect

**Responsibilities**
- Decide repo structure and service boundaries
- Define API contract (request/response formats)
- Define DB schema and storage layout
- Establish coding standards and merge rules
- **(New)** Define "job types": file_upload, youtube_captions, youtube_auto_ingest

**Deliverables**
- docs/architecture.md
- docs/api_contract.md
- docs/db_schema.md
- docs/repo_structure.md

---

### Agent 3: Backend Engineer (FastAPI)

**Responsibilities**
- Implement REST API endpoints
- Validate uploads and enforce safe limits
- Store job + transcript metadata in SQLite
- Implement export endpoints (TXT/SRT/VTT/JSON)
- **(New)** Implement YouTube endpoints:
  - Create job from YouTube URL
  - Expose job status and transcript retrieval
- Add basic tests

**Deliverables**
- apps/api/ implementation
- Unit tests for key endpoints
- Logging and error handling

---

### Agent 4: Worker/ML Engineer (Transcription Pipeline)

**Responsibilities**
- Implement transcription pipeline (ffmpeg normalize -> whisper)
- Output timestamped segments
- Update job state and store outputs
- Add failure recovery and logs
- **(New)** YouTube job handling by mode:
  - Safe Link Mode: accept captions text payload and convert to internal transcript format
  - Auto Ingest Mode: optional URL ingest pipeline (opt-in module)

**Deliverables**
- apps/worker/ implementation
- Transcription outputs:
  - segments.json
  - transcript.txt
  - transcript.srt
  - transcript.vtt

---

### Agent 5: Frontend Engineer (React UI)

**Responsibilities**
- Build Upload page (progress + validation)
- Build Jobs list (poll job status)
- Build Transcript viewer/editor
- Add export buttons and download handling
- **(New)** Build YouTube intake UI:
  - URL input
  - Mode selection (Safe Link vs Auto Ingest if enabled)
  - Clear warnings and fallback instructions

**Deliverables**
- apps/web/ implementation
- UI for upload, youtube intake, jobs, transcript, export

---

### Agent 6: DevOps Engineer

**Responsibilities**
- Docker Compose for local runtime
- Local volumes for data persistence
- Makefile scripts and environment config
- Ensure single-command startup
- **(New)** Feature flags:
  - YOUTUBE_SAFE_MODE=true
  - YOUTUBE_AUTO_INGEST=false (default)

**Deliverables**
- docker-compose.yml
- Makefile
- .env.example
- docs/local_dev.md

---

### Agent 7: QA + Security Engineer

**Responsibilities**
- Define smoke tests and regression checklist
- Validate upload limits and file safety
- Validate path sanitization and storage rules
- Verify failure modes (worker crash, bad formats)
- **(New)** YouTube-specific safety:
  - Strict allowlist of domains: youtube.com, youtu.be
  - Duration and size caps
  - Rate limiting and retries
  - Clear warnings for Auto Ingest Mode
  - Ensure no arbitrary URL fetch beyond allowlist

**Deliverables**
- docs/test_plan.md
- docs/security_checklist.md
- Smoke test checklist

---

### Agent 8: Docs Engineer

**Responsibilities**
- Write README for setup and usage
- Troubleshooting guide (ffmpeg, model downloads, permissions)
- Privacy statement: everything stays local
- CPU vs GPU performance guidance
- **(New)** YouTube feature documentation:
  - Safe Link Mode behavior and limitations
  - Auto Ingest Mode warnings and how to enable/disable

**Deliverables**
- README.md
- docs/troubleshooting.md
- docs/performance.md
- docs/youtube_modes.md

---

## 6) Execution Phases (Milestones)

### Phase 0: Kickoff (Scope + Contracts)

**Owners:** PM + Architect

**Deliverables**
- MVP requirements
- API contract draft
- DB schema and repo structure
- Definition of Done checklist
- **(New)** YouTube mode decisions:
  - Ship Safe Link Mode in v1.5
  - Gate Auto Ingest Mode behind a feature flag for v2

**Exit Criteria**
- Everyone can build against the same contract without guessing.

---

### Phase 1: Bootable Skeleton

**Owners:** DevOps + Backend + Frontend

**Deliverables**
- Docker Compose starts services
- Frontend loads
- Backend has /health
- Upload endpoint stub wired end-to-end
- **(New)** YouTube URL intake page stub and endpoint stub

**Exit Criteria**
- One command boots the app locally.

---

### Phase 2: Transcription Core

**Owners:** Worker/ML + Backend

**Deliverables**
- Worker processes jobs reliably
- Transcript stored and retrievable
- Job status lifecycle works: queued -> running -> done/failed
- Logs and error states are visible

**Exit Criteria**
- Upload file -> transcript appears in UI.

---

### Phase 3: YouTube Safe Link Mode (v1.5)

**Owners:** Frontend + Backend + Worker/ML

**Deliverables**
- POST /api/youtube creates a job from URL
- Captions flow:
  - If captions available through compliant means, ingest them
  - Else show "Upload file" or "Paste captions" fallback
- UI shows a clear path forward

**Exit Criteria**
- Paste YouTube link -> either transcript is created from captions or user is routed to a safe fallback.

---

### Phase 4: Editing + Export

**Owners:** Frontend + Backend

**Deliverables**
- Transcript viewer with timestamps
- Edit transcript and save
- Export formats: TXT, SRT, VTT, JSON

**Exit Criteria**
- User can edit and export usable transcript files.

---

### Phase 5: Auto Ingest Mode (Optional v2, behind feature flag)

**Owners:** Worker/ML + Backend + QA/Security

**Deliverables**
- URL ingest pipeline (opt-in)
- Strict allowlist + caps + warnings
- Clear enable/disable config and docs

**Exit Criteria**
- If enabled: paste link -> transcript created end-to-end.
- If disabled: feature is hidden or blocked cleanly.

---

### Phase 6: Quality + Packaging

**Owners:** QA + Docs + DevOps

**Deliverables**
- Test plan executed (smoke + negative tests)
- Security checklist satisfied (safe paths, size limits, allowlists)
- README is sufficient for fresh install

**Exit Criteria**
- Another person can run it locally using only the README.

---

## 7) Minimal Data Model (SQLite)

### jobs
- id (uuid or int)
- **job_type (file_upload | youtube_captions | youtube_auto_ingest)** ← new
- **source_url (nullable, for YouTube jobs)** ← new
- original_filename (nullable)
- stored_filename (nullable)
- status (queued | running | done | failed)
- created_at
- updated_at
- model (small | medium | large)
- language (auto | en | etc)
- error_message (nullable)

### transcripts
- job_id
- segments_json_path
- plain_text_path
- srt_path
- vtt_path
- edited_text_path (nullable)
- last_edited_at (nullable)

---

## 8) Minimal API Contract

### Core Endpoints

**POST /api/upload**
- **Request:** multipart file upload + optional params (model, language)
- **Response:** `{ "job_id": "..." }`

**GET /api/jobs**
- **Response:** list of jobs (id, status, created_at, filename)

**GET /api/jobs/{id}**
- **Response:** job details + status + error if any

**GET /api/jobs/{id}/transcript**
- **Response:** transcript text + segments array

**POST /api/jobs/{id}/transcript**
- **Request:** updated transcript text (and optionally segments edits)
- **Response:** `{ "ok": true }`

**GET /api/jobs/{id}/export?fmt=txt|srt|vtt|json**
- **Response:** file download stream

### YouTube Endpoints (New)

**POST /api/youtube**
- **Request:** `{ "url": "...", "mode": "safe" | "auto" }`
- **Response:** `{ "job_id": "..." }`
- **Behavior:**
  - `safe`: captions ingestion or fallback instructions
  - `auto`: only if feature flag enabled

---

## 9) Operational Rules (Must-Haves)

- Enforce file type allowlist and max upload size
- Sanitize filenames and store under ./data/ only
- Never accept arbitrary filesystem paths from user input
- Log worker output per job
- Offline-by-default for normal operation
- **(New)** YouTube allowlist and caps:
  - Only accept youtube.com and youtu.be URLs
  - Duration limit (configurable)
  - Rate limiting and retries
  - Auto Ingest Mode disabled by default

---

## 10) Roadmap (After v2)

- Speaker diarization (speaker labels)
- Chunking for long files
- Search within transcript
- Local auth for LAN deployments
- "Paste captions" helper that formats messy text into clean segments
