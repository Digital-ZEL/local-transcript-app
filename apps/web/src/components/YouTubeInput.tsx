import { useState } from 'react'

interface YouTubeInputProps {
  onSubmit: (url: string, mode: 'safe' | 'auto') => void
  submitting: boolean
  autoModeEnabled?: boolean
  fallbackMessage?: string | null
}

const YOUTUBE_REGEX = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/

export default function YouTubeInput({ 
  onSubmit, 
  submitting, 
  autoModeEnabled = false,
  fallbackMessage 
}: YouTubeInputProps) {
  const [url, setUrl] = useState('')
  const [mode, setMode] = useState<'safe' | 'auto'>('safe')
  const [error, setError] = useState<string | null>(null)

  const validateUrl = (input: string): boolean => {
    if (!input.trim()) {
      setError('Please enter a YouTube URL')
      return false
    }
    if (!YOUTUBE_REGEX.test(input)) {
      setError('Please enter a valid YouTube URL (youtube.com or youtu.be)')
      return false
    }
    setError(null)
    return true
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validateUrl(url)) {
      onSubmit(url, mode)
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            YouTube URL
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://youtube.com/watch?v=... or https://youtu.be/..."
              disabled={submitting}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            />
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {submitting ? 'Processing...' : '📺 Get Transcript'}
            </button>
          </div>
        </div>

        {autoModeEnabled && (
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-gray-700">Mode:</label>
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="mode"
                value="safe"
                checked={mode === 'safe'}
                onChange={() => setMode('safe')}
                className="text-blue-600"
              />
              <span className="text-sm">Safe (captions only)</span>
            </label>
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="mode"
                value="auto"
                checked={mode === 'auto'}
                onChange={() => setMode('auto')}
                className="text-blue-600"
              />
              <span className="text-sm">Auto Ingest</span>
              <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                ⚠️ ToS Risk
              </span>
            </label>
          </div>
        )}
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {fallbackMessage && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-4 rounded-lg">
          <p className="font-medium mb-2">⚠️ Captions Not Available</p>
          <p className="text-sm">{fallbackMessage}</p>
          <p className="text-sm mt-2">
            <strong>Options:</strong>
          </p>
          <ul className="text-sm list-disc list-inside mt-1 space-y-1">
            <li>Upload the video/audio file directly</li>
            <li>Download the video manually and upload it here</li>
            <li>Check if the video has captions enabled</li>
          </ul>
        </div>
      )}

      <div className="text-sm text-gray-500 bg-gray-50 p-4 rounded-lg">
        <p className="font-medium text-gray-700 mb-1">ℹ️ How it works:</p>
        <p>
          <strong>Safe Mode:</strong> Retrieves available captions from YouTube. If captions 
          aren't available, you'll be prompted to upload the file instead.
        </p>
        {autoModeEnabled && (
          <p className="mt-2">
            <strong>Auto Ingest:</strong> Downloads and transcribes the audio locally. 
            Use responsibly — may violate platform terms.
          </p>
        )}
      </div>
    </div>
  )
}
