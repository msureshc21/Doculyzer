import { useState, useEffect } from 'react'
import './DocumentList.css'

interface Document {
  id: number
  filename: string
  file_type: string
  file_size: number
  upload_date: string
  processed: string
}

export default function DocumentList() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  const fetchDocuments = async () => {
    try {
      const response = await fetch('/api/v1/documents')
      if (!response.ok) throw new Error('Failed to fetch documents')
      const data = await response.json()
      setDocuments(data.documents || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  if (loading) return <div className="loading">Loading documents...</div>
  if (error) return <div className="error-message">{error}</div>

  return (
    <div className="document-list">
      <div className="list-header">
        <h2>Documents ({documents.length})</h2>
        <button onClick={fetchDocuments} className="refresh-button">Refresh</button>
      </div>
      
      {documents.length === 0 ? (
        <div className="empty-state">No documents uploaded yet</div>
      ) : (
        <div className="documents-grid">
          {documents.map((doc) => (
            <div key={doc.id} className="document-card">
              <div className="document-name">{doc.filename}</div>
              <div className="document-details">
                <span>Type: {doc.file_type}</span>
                <span>Size: {(doc.file_size / 1024).toFixed(2)} KB</span>
                <span>Status: {doc.processed}</span>
              </div>
              <div className="document-date">
                Uploaded: {new Date(doc.upload_date).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

