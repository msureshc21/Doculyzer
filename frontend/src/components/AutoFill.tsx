import { useState } from 'react'
import './AutoFill.css'

interface FieldExplanation {
  field_name: string
  fact_key: string
  value: string
  confidence: number
  source_document_name?: string
  reason: string
  matched: boolean
}

interface AutoFillResult {
  filled_pdf_path?: string
  fields_detected: number
  fields_matched: number
  fields_filled: number
  explanations: FieldExplanation[]
  success: boolean
}

export default function AutoFill() {
  const [file, setFile] = useState<File | null>(null)
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<AutoFillResult | null>(null)
  const [error, setError] = useState<string>('')

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError('')
      setResult(null)
    }
  }

  const handleAutoFill = async () => {
    if (!file) {
      setError('Please select a PDF file')
      return
    }

    setProcessing(true)
    setError('')
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('generate_preview', 'true')

    try {
      const response = await fetch('/api/v1/autofill/autofill', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Auto-fill failed')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Auto-fill failed')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="autofill">
      <h2>Auto-Fill PDF Form</h2>
      <div className="autofill-form">
        <div className="file-input-wrapper">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            disabled={processing}
          />
          {file && (
            <div className="file-info">
              <span>Selected: {file.name}</span>
            </div>
          )}
        </div>
        
        <button 
          onClick={handleAutoFill} 
          disabled={!file || processing}
          className="autofill-button"
        >
          {processing ? 'Processing...' : 'Auto-Fill PDF'}
        </button>

        {error && <div className="message error">{error}</div>}

        {result && (
          <div className="autofill-result">
            <div className="result-summary">
              <h3>Results</h3>
              <div className="stats">
                <div className="stat">
                  <span className="stat-label">Fields Detected:</span>
                  <span className="stat-value">{result.fields_detected}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Fields Matched:</span>
                  <span className="stat-value">{result.fields_matched}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Fields Filled:</span>
                  <span className="stat-value">{result.fields_filled}</span>
                </div>
              </div>
            </div>

            {result.explanations.length > 0 && (
              <div className="explanations">
                <h3>Field Explanations</h3>
                {result.explanations.map((explanation, idx) => (
                  <div key={idx} className={`explanation ${explanation.matched ? 'matched' : 'unmatched'}`}>
                    <div className="explanation-header">
                      <span className="field-name">{explanation.field_name}</span>
                      {explanation.matched && (
                        <span className="match-badge">✓ Matched</span>
                      )}
                    </div>
                    {explanation.matched && explanation.value && (
                      <>
                        <div className="explanation-value">
                          Value: <strong>{explanation.value}</strong>
                        </div>
                        <div className="explanation-details">
                          <div className="explanation-reason">{explanation.reason}</div>
                          {explanation.source_document_name && (
                            <div className="explanation-source">
                              Source: {explanation.source_document_name}
                            </div>
                          )}
                        </div>
                      </>
                    )}
                    {!explanation.matched && (
                      <div className="explanation-reason">{explanation.reason}</div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {result.filled_pdf_path && (
              <div className="preview-link">
                <a 
                  href={`/api/v1/autofill/preview/${result.filled_pdf_path}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="download-button"
                >
                  Download Filled PDF
                </a>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

