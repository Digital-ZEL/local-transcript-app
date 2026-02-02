import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getJob, getTranscript, saveTranscript, Job, Segment } from '../api/client'
import TranscriptEditor from '../components/TranscriptEditor'
import ExportButtons from '../components/ExportButtons'

const STATUS_CONFIG = {
  queued: { label: 'Queued', color: 'bg-gray-100 text-gray-700', icon: '⏳' },
  running: { label: 'Running', color: 'bg-blue-100 text-blue-700', icon: '⚙️' },
  done: { label: 'Done', color: 'bg-green-100 text-green-700', icon: '✅' },
  failed: { label: 'Failed', color: 'bg-red-100 text-red-700', icon: '❌' },
}

export default function Transcript() {
  const { id } = useParams<{ id: string }>()
  const [job, setJob] = useState<Job | null>(null)
  const [segments, setSegments] = useState<Segment[]>([])
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    if (!id) return

    try {
      const jobData = await getJob(id)
      setJob(jobData)

      if (jobData.status === 'done') {
        const transcriptData = await getTranscript(id)
        setSegments(transcriptData.segments)
        setText(transcriptData.text)
      }
      
      setError(null)
    } catch (err) {
      setError('Failed to load job')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()

    // Poll while job is running
    const interval = setInterval(() => {
      if (job?.status === 'queued' || job?.status === 'running') {
        fetchData()
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [id, job?.status])

  const handleSave = async (newText: string, newSegments: Segment[]) => {
    if (!id) return

    setSaving(true)
    try {
      await saveTranscript(id, newText, newSegments)
      setText(newText)
      setSegments(newSegments)
      setError(null)
    } catch (err) {
      setError('Failed to save transcript')
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin text-4xl mb-4">⚙️</div>
        <p className="text-gray-600">Loading transcript...</p>
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">⚠️</div>
        <p className="text-red-600">{error || 'Job not found'}</p>
        <Link
          to="/jobs"
          className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Back to Jobs
        </Link>
      </div>
    )
  }

  const statusConfig = STATUS_CONFIG[job.status]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link to="/jobs" className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block">
            ← Back to Jobs
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            {job.original_filename || job.source_url || `Job ${job.id.slice(0, 8)}`}
          </h1>
          <div className="flex items-center gap-3 mt-2">
            <span className={`inline-flex items-center gap-1 text-sm px-3 py-1 rounded-full ${statusConfig.color}`}>
              {statusConfig.icon} {statusConfig.label}
            </span>
            <span className="text-sm text-gray-500">
              Model: {job.model} • Language: {job.language}
            </span>
          </div>
        </div>
      </div>

      {/* Status-specific content */}
      {job.status === 'queued' && (
        <div className="bg-gray-50 border rounded-lg p-8 text-center">
          <div className="text-4xl mb-4">⏳</div>
          <h2 className="text-xl font-medium text-gray-900 mb-2">Waiting in Queue</h2>
          <p className="text-gray-600">
            Your transcription job is queued and will start processing soon.
          </p>
          <p className="text-sm text-gray-400 mt-4">Auto-refreshing...</p>
        </div>
      )}

      {job.status === 'running' && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">
          <div className="animate-spin text-4xl mb-4">⚙️</div>
          <h2 className="text-xl font-medium text-blue-900 mb-2">Processing</h2>
          <p className="text-blue-700">
            Your file is being transcribed. This may take a few minutes depending on the file length and model.
          </p>
          <p className="text-sm text-blue-500 mt-4">Auto-refreshing...</p>
        </div>
      )}

      {job.status === 'failed' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="text-3xl">❌</div>
            <div>
              <h2 className="text-lg font-medium text-red-900">Transcription Failed</h2>
              {job.error_message && (
                <p className="text-red-700 mt-2">{job.error_message}</p>
              )}
              <Link
                to="/"
                className="inline-block mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Try Again
              </Link>
            </div>
          </div>
        </div>
      )}

      {job.status === 'done' && (
        <>
          {/* Export buttons */}
          <div className="bg-white border rounded-lg p-4">
            <ExportButtons jobId={job.id} />
          </div>

          {/* Transcript editor */}
          <div className="bg-white border rounded-lg p-4">
            <TranscriptEditor
              segments={segments}
              text={text}
              onSave={handleSave}
              saving={saving}
            />
          </div>
        </>
      )}

      {/* Job metadata */}
      <div className="bg-gray-50 border rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Job Details</h3>
        <dl className="grid grid-cols-2 gap-2 text-sm">
          <dt className="text-gray-500">Job ID</dt>
          <dd className="text-gray-900 font-mono">{job.id}</dd>
          
          <dt className="text-gray-500">Type</dt>
          <dd className="text-gray-900">{job.job_type}</dd>
          
          <dt className="text-gray-500">Created</dt>
          <dd className="text-gray-900">{new Date(job.created_at).toLocaleString()}</dd>
          
          <dt className="text-gray-500">Updated</dt>
          <dd className="text-gray-900">{new Date(job.updated_at).toLocaleString()}</dd>
          
          {job.source_url && (
            <>
              <dt className="text-gray-500">Source URL</dt>
              <dd className="text-gray-900 truncate">
                <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                  {job.source_url}
                </a>
              </dd>
            </>
          )}
        </dl>
      </div>
    </div>
  )
}
