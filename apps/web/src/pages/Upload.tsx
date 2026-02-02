import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FileUpload from '../components/FileUpload'
import YouTubeInput from '../components/YouTubeInput'
import { uploadFile, submitYouTube } from '../api/client'

type Tab = 'file' | 'youtube'

export default function Upload() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('file')
  
  // File upload state
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [model, setModel] = useState('small')
  const [language, setLanguage] = useState('auto')
  
  // YouTube state
  const [youtubeSubmitting, setYoutubeSubmitting] = useState(false)
  const [fallbackMessage, setFallbackMessage] = useState<string | null>(null)
  
  // General state
  const [error, setError] = useState<string | null>(null)

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    setError(null)
  }

  const handleFileUpload = async () => {
    if (!selectedFile) return

    setUploading(true)
    setProgress(0)
    setError(null)

    try {
      const result = await uploadFile(
        selectedFile,
        { model, language },
        (percent) => setProgress(percent)
      )
      navigate(`/jobs/${result.job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setUploading(false)
    }
  }

  const handleYouTubeSubmit = async (url: string, mode: 'safe' | 'auto') => {
    setYoutubeSubmitting(true)
    setFallbackMessage(null)
    setError(null)

    try {
      const result = await submitYouTube(url, mode)
      
      if (result.fallback_message) {
        // Captions not available
        setFallbackMessage(result.fallback_message)
        setYoutubeSubmitting(false)
      } else if (result.job_id) {
        // Success - navigate to job
        navigate(`/jobs/${result.job_id}`)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process YouTube URL')
      setYoutubeSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Create Transcript</h1>
        <p className="text-gray-600 mt-1">
          Upload a file or paste a YouTube link to generate a transcript
        </p>
      </div>

      {/* Tab buttons */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('file')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'file'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📁 Upload File
          </button>
          <button
            onClick={() => setActiveTab('youtube')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'youtube'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📺 YouTube Link
          </button>
        </nav>
      </div>

      {/* File upload tab */}
      {activeTab === 'file' && (
        <div className="space-y-6">
          <FileUpload
            onFileSelect={handleFileSelect}
            uploading={uploading}
            progress={progress}
          />

          {selectedFile && !uploading && (
            <div className="bg-white border rounded-lg p-4 space-y-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl">📄</span>
                <div>
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Model
                  </label>
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="tiny">Tiny (fastest)</option>
                    <option value="base">Base</option>
                    <option value="small">Small (recommended)</option>
                    <option value="medium">Medium</option>
                    <option value="large">Large (best quality)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Language
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="auto">Auto-detect</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="it">Italian</option>
                    <option value="pt">Portuguese</option>
                    <option value="ja">Japanese</option>
                    <option value="zh">Chinese</option>
                    <option value="ko">Korean</option>
                  </select>
                </div>
              </div>

              <button
                onClick={handleFileUpload}
                className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                🚀 Start Transcription
              </button>
            </div>
          )}
        </div>
      )}

      {/* YouTube tab */}
      {activeTab === 'youtube' && (
        <YouTubeInput
          onSubmit={handleYouTubeSubmit}
          submitting={youtubeSubmitting}
          autoModeEnabled={false} // Enable when YOUTUBE_AUTO_INGEST feature flag is true
          fallbackMessage={fallbackMessage}
        />
      )}

      {/* Error display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}
    </div>
  )
}
