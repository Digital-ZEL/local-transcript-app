import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getJobs, Job } from '../api/client'

const STATUS_CONFIG = {
  queued: { label: 'Queued', color: 'bg-gray-100 text-gray-700', icon: '⏳' },
  running: { label: 'Running', color: 'bg-blue-100 text-blue-700', icon: '⚙️' },
  done: { label: 'Done', color: 'bg-green-100 text-green-700', icon: '✅' },
  failed: { label: 'Failed', color: 'bg-red-100 text-red-700', icon: '❌' },
}

const JOB_TYPE_LABELS = {
  file_upload: '📁 File Upload',
  youtube_captions: '📺 YouTube Captions',
  youtube_auto_ingest: '🎬 YouTube Auto',
}

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchJobs = async () => {
    try {
      const data = await getJobs()
      setJobs(data)
      setError(null)
    } catch (err) {
      setError('Failed to load jobs')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobs()

    // Poll every 2 seconds for status updates
    const interval = setInterval(fetchJobs, 2000)
    return () => clearInterval(interval)
  }, [])

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString()
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin text-4xl mb-4">⚙️</div>
        <p className="text-gray-600">Loading jobs...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">⚠️</div>
        <p className="text-red-600">{error}</p>
        <button
          onClick={() => {
            setLoading(true)
            fetchJobs()
          }}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transcription Jobs</h1>
          <p className="text-gray-600 mt-1">
            {jobs.length} job{jobs.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Link
          to="/"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
        >
          + New Transcript
        </Link>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <div className="text-4xl mb-4">📭</div>
          <p className="text-gray-600 mb-4">No transcription jobs yet</p>
          <Link
            to="/"
            className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create your first transcript
          </Link>
        </div>
      ) : (
        <div className="bg-white border rounded-lg divide-y">
          {jobs.map((job) => {
            const statusConfig = STATUS_CONFIG[job.status]
            const isClickable = job.status === 'done'
            
            const content = (
              <div className="flex items-center gap-4 p-4 hover:bg-gray-50">
                <div className="flex-shrink-0 text-2xl">
                  {statusConfig.icon}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-gray-900 truncate">
                      {job.original_filename || job.source_url || `Job ${job.id.slice(0, 8)}`}
                    </p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${statusConfig.color}`}>
                      {statusConfig.label}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                    <span>{JOB_TYPE_LABELS[job.job_type] || job.job_type}</span>
                    <span>•</span>
                    <span>{formatDate(job.created_at)}</span>
                    {job.model && (
                      <>
                        <span>•</span>
                        <span>Model: {job.model}</span>
                      </>
                    )}
                  </div>
                  {job.error_message && (
                    <p className="text-sm text-red-600 mt-1 truncate">
                      Error: {job.error_message}
                    </p>
                  )}
                </div>

                <div className="flex-shrink-0 text-gray-400">
                  {isClickable ? '→' : ''}
                </div>
              </div>
            )

            return isClickable ? (
              <Link key={job.id} to={`/jobs/${job.id}`} className="block">
                {content}
              </Link>
            ) : (
              <div key={job.id}>{content}</div>
            )
          })}
        </div>
      )}

      {/* Auto-refresh indicator */}
      <p className="text-center text-sm text-gray-400">
        Auto-refreshing every 2 seconds
      </p>
    </div>
  )
}
