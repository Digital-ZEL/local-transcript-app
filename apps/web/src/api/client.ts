// API Client for Local Transcript App

const API_BASE = '/api'

export interface Job {
  id: string
  job_type: 'file_upload' | 'youtube_captions' | 'youtube_auto_ingest'
  source_url: string | null
  original_filename: string | null
  status: 'queued' | 'running' | 'done' | 'failed'
  created_at: string
  updated_at: string
  model: string
  language: string
  error_message: string | null
}

export interface Segment {
  start: number
  end: number
  text: string
}

export interface TranscriptData {
  text: string
  segments: Segment[]
}

// Upload a file for transcription
export async function uploadFile(
  file: File,
  options?: { model?: string; language?: string },
  onProgress?: (percent: number) => void
): Promise<{ job_id: string }> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()
    formData.append('file', file)
    if (options?.model) formData.append('model', options.model)
    if (options?.language) formData.append('language', options.language)

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText))
      } else {
        reject(new Error(xhr.responseText || 'Upload failed'))
      }
    })

    xhr.addEventListener('error', () => reject(new Error('Network error')))
    xhr.open('POST', `${API_BASE}/upload`)
    xhr.send(formData)
  })
}

// Submit a YouTube URL
export async function submitYouTube(
  url: string,
  mode: 'safe' | 'auto' = 'safe'
): Promise<{ job_id: string; captions_available?: boolean; fallback_message?: string }> {
  const response = await fetch(`${API_BASE}/youtube`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, mode })
  })
  if (!response.ok) {
    const error = await response.text()
    throw new Error(error || 'Failed to submit YouTube URL')
  }
  return response.json()
}

// Get list of all jobs
export async function getJobs(): Promise<Job[]> {
  const response = await fetch(`${API_BASE}/jobs`)
  if (!response.ok) throw new Error('Failed to fetch jobs')
  return response.json()
}

// Get a single job by ID
export async function getJob(id: string): Promise<Job> {
  const response = await fetch(`${API_BASE}/jobs/${id}`)
  if (!response.ok) throw new Error('Failed to fetch job')
  return response.json()
}

// Get transcript for a job
export async function getTranscript(jobId: string): Promise<TranscriptData> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/transcript`)
  if (!response.ok) throw new Error('Failed to fetch transcript')
  return response.json()
}

// Save edited transcript
export async function saveTranscript(
  jobId: string,
  text: string,
  segments?: Segment[]
): Promise<{ ok: boolean }> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/transcript`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, segments })
  })
  if (!response.ok) throw new Error('Failed to save transcript')
  return response.json()
}

// Get export URL
export function getExportUrl(jobId: string, format: 'txt' | 'srt' | 'vtt' | 'json'): string {
  return `${API_BASE}/jobs/${jobId}/export?fmt=${format}`
}

// Download export file
export async function downloadExport(
  jobId: string,
  format: 'txt' | 'srt' | 'vtt' | 'json'
): Promise<void> {
  const url = getExportUrl(jobId, format)
  const response = await fetch(url)
  if (!response.ok) throw new Error('Export failed')
  
  const blob = await response.blob()
  const downloadUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = downloadUrl
  a.download = `transcript.${format}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(downloadUrl)
}

// Format time in seconds to HH:MM:SS.mmm
export function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 1000)
  
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m}:${s.toString().padStart(2, '0')}`
}
