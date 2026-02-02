import { useState, useEffect } from 'react'
import { Segment, formatTime } from '../api/client'

interface TranscriptEditorProps {
  segments: Segment[]
  text: string
  onSave: (text: string, segments: Segment[]) => void
  saving: boolean
}

export default function TranscriptEditor({ segments, text, onSave, saving }: TranscriptEditorProps) {
  const [editMode, setEditMode] = useState(false)
  const [editedSegments, setEditedSegments] = useState<Segment[]>(segments)
  const [editedText, setEditedText] = useState(text)
  const [hasChanges, setHasChanges] = useState(false)
  const [activeSegment, setActiveSegment] = useState<number | null>(null)

  useEffect(() => {
    setEditedSegments(segments)
    setEditedText(text)
    setHasChanges(false)
  }, [segments, text])

  const handleSegmentEdit = (index: number, newText: string) => {
    const updated = [...editedSegments]
    updated[index] = { ...updated[index], text: newText }
    setEditedSegments(updated)
    setEditedText(updated.map(s => s.text).join(' '))
    setHasChanges(true)
  }

  const handleFullTextEdit = (newText: string) => {
    setEditedText(newText)
    setHasChanges(true)
  }

  const handleSave = () => {
    onSave(editedText, editedSegments)
    setHasChanges(false)
    setEditMode(false)
  }

  const handleCancel = () => {
    setEditedSegments(segments)
    setEditedText(text)
    setHasChanges(false)
    setEditMode(false)
  }

  const scrollToTimestamp = (seconds: number) => {
    // This could be extended to control a video player
    console.log(`Jump to ${formatTime(seconds)}`)
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setEditMode(!editMode)}
            className={`px-4 py-2 rounded-lg font-medium ${
              editMode
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            ✏️ {editMode ? 'Viewing Segments' : 'Edit Mode'}
          </button>
          
          {hasChanges && (
            <span className="text-sm text-yellow-600">
              ⚠️ Unsaved changes
            </span>
          )}
        </div>

        {hasChanges && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleCancel}
              disabled={saving}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
            >
              {saving ? 'Saving...' : '💾 Save Changes'}
            </button>
          </div>
        )}
      </div>

      {/* Full text editor mode */}
      {editMode && (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Full Transcript (edit freely)
          </label>
          <textarea
            value={editedText}
            onChange={(e) => handleFullTextEdit(e.target.value)}
            className="w-full h-64 px-4 py-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Transcript text..."
          />
        </div>
      )}

      {/* Segment view */}
      {!editMode && (
        <div className="border rounded-lg divide-y max-h-[600px] overflow-y-auto">
          {editedSegments.map((segment, index) => (
            <div
              key={index}
              className={`flex gap-4 p-3 hover:bg-gray-50 ${
                activeSegment === index ? 'bg-blue-50' : ''
              }`}
              onClick={() => setActiveSegment(index)}
            >
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  scrollToTimestamp(segment.start)
                }}
                className="flex-shrink-0 text-xs font-mono text-blue-600 hover:text-blue-800 hover:underline"
              >
                {formatTime(segment.start)}
              </button>
              
              <div className="flex-1 min-w-0">
                {activeSegment === index ? (
                  <input
                    type="text"
                    value={segment.text}
                    onChange={(e) => handleSegmentEdit(index, e.target.value)}
                    className="w-full px-2 py-1 border border-blue-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    autoFocus
                    onBlur={() => setActiveSegment(null)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') setActiveSegment(null)
                      if (e.key === 'Escape') {
                        setEditedSegments(segments)
                        setActiveSegment(null)
                      }
                    }}
                  />
                ) : (
                  <p className="text-gray-800">{segment.text}</p>
                )}
              </div>
              
              <span className="flex-shrink-0 text-xs font-mono text-gray-400">
                → {formatTime(segment.end)}
              </span>
            </div>
          ))}
        </div>
      )}

      {editedSegments.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No transcript segments available yet.
        </div>
      )}
    </div>
  )
}
