import { useState } from 'react'
import './DocumentUpload.css'

interface DocumentUploadProps {
  onUploadSuccess: () => void
  onShowFactEntry?: () => void
}

export default function DocumentUpload({ onUploadSuccess, onShowFactEntry }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState<string>('')
  const [error, setError] = useState<string>('')

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError('')
      setMessage('')
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file')
      return
    }

    setUploading(true)
    setError('')
    setMessage('')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('description', 'Uploaded via web interface')

    try {
      const response = await fetch('/api/v1/documents/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data = await response.json()
      setMessage(`Document uploaded successfully! ID: ${data.document.id}`)
      setFile(null)
      
      // Reset file input
      const fileInput = document.getElementById('file-input') as HTMLInputElement
      if (fileInput) fileInput.value = ''
      
      // Check if we should prompt for missing facts
      // After first upload, show fact entry if needed
      if (onShowFactEntry) {
        // Small delay to show success message first
        setTimeout(() => {
          onShowFactEntry()
        }, 1500)
      }
      
      onUploadSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="document-upload">
      <h2>Upload Document</h2>
      <div className="upload-form">
        <div className="file-input-wrapper">
          <input
            id="file-input"
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            disabled={uploading}
          />
          {file && (
            <div className="file-info">
              <span>Selected: {file.name}</span>
              <span>Size: {(file.size / 1024).toFixed(2)} KB</span>
            </div>
          )}
        </div>
        
        <button 
          onClick={handleUpload} 
          disabled={!file || uploading}
          className="upload-button"
        >
          {uploading ? 'Uploading...' : 'Upload PDF'}
        </button>

        {message && <div className="message success">{message}</div>}
        {error && <div className="message error">{error}</div>}
      </div>
    </div>
  )
}

