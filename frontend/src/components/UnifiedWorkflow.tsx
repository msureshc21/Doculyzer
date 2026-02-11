import { useState } from 'react'
import './UnifiedWorkflow.css'

interface FieldContext {
  field_name: string
  field_type: string
  label?: string
  context: string
  category: string
  is_required: boolean
}

interface FieldMatch {
  field_name: string
  field_context: FieldContext
  suggested_fact_key?: string
  suggested_value?: string
  confidence: number
  match_quality: string
  requires_confirmation: boolean
  reason: string
}

interface DocumentAnalysis {
  document_type: string
  document_purpose: string
  summary: string
  fields: FieldContext[]
  total_fields: number
  required_fields: number
  can_autofill: boolean
  warnings: string[]
}

interface DocumentFillPreview {
  document_analysis: DocumentAnalysis
  field_matches: FieldMatch[]
  fields_requiring_input: FieldContext[]
  can_proceed: boolean
}

export default function UnifiedWorkflow() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [preview, setPreview] = useState<DocumentFillPreview | null>(null)
  const [error, setError] = useState<string>('')
  const [confirmedFields, setConfirmedFields] = useState<Set<string>>(new Set())
  const [userValues, setUserValues] = useState<Record<string, string>>({})
  const [filling, setFilling] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError('')
      setPreview(null)
      setConfirmedFields(new Set())
      setUserValues({})
    }
  }

  const handleUploadAndAnalyze = async () => {
    if (!file) {
      setError('Please select a PDF file')
      return
    }

    setUploading(true)
    setError('')
    setPreview(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/v1/workflow/upload-and-analyze', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Analysis failed')
      }

      const data = await response.json()
      setPreview(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setUploading(false)
    }
  }

  const handleConfirmField = (fieldName: string) => {
    setConfirmedFields(prev => {
      const newSet = new Set(prev)
      if (newSet.has(fieldName)) {
        newSet.delete(fieldName)
      } else {
        newSet.add(fieldName)
      }
      return newSet
    })
  }

  const handleUserValueChange = (fieldName: string, value: string) => {
    setUserValues(prev => ({ ...prev, [fieldName]: value }))
  }

  const handleFillDocument = async () => {
    if (!preview) return

    setFilling(true)
    setError('')

    // TODO: Implement actual fill endpoint
    // For now, just show success message
    setTimeout(() => {
      setFilling(false)
      alert('Document filling will be implemented in the next step')
    }, 1000)
  }

  return (
    <div className="unified-workflow">
      <h2>Upload & Auto-Fill Document</h2>
      
      <div className="workflow-step">
        <h3>Step 1: Upload PDF</h3>
        <div className="upload-section">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            disabled={uploading}
          />
          {file && (
            <div className="file-info">
              <span>Selected: {file.name}</span>
            </div>
          )}
          <button
            onClick={handleUploadAndAnalyze}
            disabled={!file || uploading}
            className="analyze-button"
          >
            {uploading ? 'Analyzing...' : 'Upload & Analyze Document'}
          </button>
        </div>
      </div>

      {error && <div className="message error">{error}</div>}

      {preview && (
        <>
          <div className="workflow-step">
            <h3>Step 2: Document Analysis</h3>
            <div className="analysis-summary">
              <h4>Document Summary</h4>
              <p><strong>Type:</strong> {preview.document_analysis.document_type.replace(/_/g, ' ')}</p>
              <p><strong>Purpose:</strong> {preview.document_analysis.document_purpose}</p>
              <p><strong>Summary:</strong> {preview.document_analysis.summary}</p>
              <p><strong>Total Fields:</strong> {preview.document_analysis.total_fields} ({preview.document_analysis.required_fields} required)</p>
            </div>
          </div>

          <div className="workflow-step">
            <h3>Step 3: Review Auto-Fill Suggestions</h3>
            {preview.field_matches.length > 0 ? (
              <div className="field-matches">
                <h4>Fields That Can Be Auto-Filled</h4>
                {preview.field_matches.map((match, idx) => (
                  <div key={idx} className="field-match-card">
                    <div className="field-match-header">
                      <input
                        type="checkbox"
                        checked={confirmedFields.has(match.field_name)}
                        onChange={() => handleConfirmField(match.field_name)}
                        disabled={!match.suggested_value}
                      />
                      <label>
                        <strong>{match.field_context.label || match.field_name}</strong>
                        {match.field_context.is_required && <span className="required">*</span>}
                      </label>
                    </div>
                    <div className="field-context">{match.field_context.context}</div>
                    {match.suggested_value && (
                      <div className="suggested-value">
                        <strong>Suggested Value:</strong> {match.suggested_value}
                        <span className="confidence">({(match.confidence * 100).toFixed(0)}% confidence)</span>
                      </div>
                    )}
                    <div className="match-reason">{match.reason}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p>No fields can be auto-filled from your Memory Graph.</p>
            )}
          </div>

          <div className="workflow-step">
            <h3>Step 4: Enter Missing Information</h3>
            {preview.fields_requiring_input.length > 0 ? (
              <div className="user-input-fields">
                {preview.fields_requiring_input.map((field, idx) => (
                  <div key={idx} className="user-input-field">
                    <label>
                      {field.label || field.field_name}
                      {field.is_required && <span className="required">*</span>}
                    </label>
                    <div className="field-context-small">{field.context}</div>
                    <input
                      type="text"
                      value={userValues[field.field_name] || ''}
                      onChange={(e) => handleUserValueChange(field.field_name, e.target.value)}
                      placeholder={`Enter ${field.label || field.field_name}`}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <p>All fields can be auto-filled or are optional.</p>
            )}
          </div>

          <div className="workflow-step">
            <h3>Step 5: Fill Document</h3>
            <button
              onClick={handleFillDocument}
              disabled={filling}
              className="fill-button"
            >
              {filling ? 'Filling...' : 'Fill Document & Download'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}

