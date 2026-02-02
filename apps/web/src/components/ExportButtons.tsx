import { useState } from 'react'
import { downloadExport } from '../api/client'

interface ExportButtonsProps {
  jobId: string
  disabled?: boolean
}

const FORMATS = [
  { id: 'txt', label: 'TXT', icon: '📄', description: 'Plain text' },
  { id: 'srt', label: 'SRT', icon: '🎬', description: 'SubRip subtitles' },
  { id: 'vtt', label: 'VTT', icon: '🌐', description: 'WebVTT subtitles' },
  { id: 'json', label: 'JSON', icon: '📊', description: 'Structured data' },
] as const

export default function ExportButtons({ jobId, disabled }: ExportButtonsProps) {
  const [downloading, setDownloading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleDownload = async (format: 'txt' | 'srt' | 'vtt' | 'json') => {
    setDownloading(format)
    setError(null)
    try {
      await downloadExport(jobId, format)
    } catch (err) {
      setError(`Failed to download ${format.toUpperCase()}`)
      console.error(err)
    } finally {
      setDownloading(null)
    }
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-gray-700">Export Transcript</h3>
      
      <div className="flex flex-wrap gap-2">
        {FORMATS.map(({ id, label, icon, description }) => (
          <button
            key={id}
            onClick={() => handleDownload(id)}
            disabled={disabled || downloading !== null}
            title={description}
            className={`
              inline-flex items-center gap-2 px-4 py-2 rounded-lg border font-medium transition-colors
              ${downloading === id
                ? 'bg-blue-50 border-blue-300 text-blue-700'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            <span>{icon}</span>
            <span>{downloading === id ? 'Downloading...' : label}</span>
          </button>
        ))}
      </div>

      {error && (
        <div className="text-sm text-red-600">
          {error}
        </div>
      )}
    </div>
  )
}
