import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface HealthStatus {
  status: string
  version: string
  features: {
    youtube_safe_mode: boolean
    youtube_auto_ingest: boolean
    whisper_model: string
    max_upload_mb: number
  }
}

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then(res => res.json())
      .then(setHealth)
      .catch(e => setError(e.message))
  }, [])

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '1rem', color: '#fff' }}>
        🎙️ Local Transcript
      </h1>
      
      <div style={{ 
        background: '#1a1a1a', 
        padding: '1.5rem', 
        borderRadius: '8px',
        marginBottom: '1.5rem'
      }}>
        <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>System Status</h2>
        
        {error && (
          <p style={{ color: '#ff6b6b' }}>⚠️ API Error: {error}</p>
        )}
        
        {health && (
          <div>
            <p>✅ API: {health.status} (v{health.version})</p>
            <p>🤖 Model: {health.features.whisper_model}</p>
            <p>📁 Max Upload: {health.features.max_upload_mb}MB</p>
            <p>🔒 YouTube Safe Mode: {health.features.youtube_safe_mode ? 'On' : 'Off'}</p>
            <p>⚡ YouTube Auto-Ingest: {health.features.youtube_auto_ingest ? 'On' : 'Off'}</p>
          </div>
        )}
        
        {!health && !error && <p>Loading...</p>}
      </div>

      <div style={{ 
        background: '#1a1a1a', 
        padding: '1.5rem', 
        borderRadius: '8px',
        marginBottom: '1.5rem'
      }}>
        <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>Upload File</h2>
        <p style={{ color: '#888' }}>Upload component coming soon...</p>
      </div>

      <div style={{ 
        background: '#1a1a1a', 
        padding: '1.5rem', 
        borderRadius: '8px',
        marginBottom: '1.5rem'
      }}>
        <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>YouTube Link</h2>
        <p style={{ color: '#888' }}>YouTube intake component coming soon...</p>
      </div>

      <div style={{ 
        background: '#1a1a1a', 
        padding: '1.5rem', 
        borderRadius: '8px'
      }}>
        <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>Recent Jobs</h2>
        <p style={{ color: '#888' }}>Jobs list component coming soon...</p>
      </div>
    </div>
  )
}

export default App
