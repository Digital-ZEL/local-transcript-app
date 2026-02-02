import { useState, useRef, DragEvent } from 'react'

interface FileUploadProps {
  onFileSelect: (file: File) => void
  uploading: boolean
  progress: number
}

const ACCEPTED_TYPES = [
  'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac', 'audio/m4a', 'audio/webm',
  'video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska'
]

const ACCEPTED_EXTENSIONS = '.mp3,.wav,.ogg,.flac,.m4a,.webm,.mp4,.mov,.avi,.mkv'

export default function FileUpload({ onFileSelect, uploading, progress }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): boolean => {
    // Check file type
    const ext = file.name.split('.').pop()?.toLowerCase()
    const validExts = ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'webm', 'mp4', 'mov', 'avi', 'mkv']
    if (!ext || !validExts.includes(ext)) {
      setError(`Invalid file type: .${ext}. Accepted: ${validExts.join(', ')}`)
      return false
    }
    
    // Check file size (max 500MB)
    const maxSize = 500 * 1024 * 1024
    if (file.size > maxSize) {
      setError('File too large. Maximum size is 500MB.')
      return false
    }
    
    setError(null)
    return true
  }

  const handleFile = (file: File) => {
    if (validateFile(file)) {
      onFileSelect(file)
    }
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleClick = () => {
    inputRef.current?.click()
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  return (
    <div className="space-y-4">
      <div
        onClick={handleClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
          ${isDragging 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }
          ${uploading ? 'pointer-events-none opacity-60' : ''}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          onChange={handleInputChange}
          className="hidden"
          disabled={uploading}
        />
        
        <div className="text-4xl mb-4">🎵</div>
        
        {uploading ? (
          <div className="space-y-3">
            <p className="text-gray-600">Uploading...</p>
            <div className="w-full max-w-xs mx-auto bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-sm text-gray-500">{progress}%</p>
          </div>
        ) : (
          <>
            <p className="text-gray-600 font-medium">
              Drop audio/video file here or click to browse
            </p>
            <p className="text-sm text-gray-400 mt-2">
              MP3, WAV, OGG, FLAC, M4A, MP4, MOV, MKV (max 500MB)
            </p>
          </>
        )}
      </div>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}
    </div>
  )
}
