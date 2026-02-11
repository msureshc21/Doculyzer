import { useState, useEffect } from 'react'
import './FactEntry.css'

interface FieldDefinition {
  fact_key: string
  description: string
  type: string
  examples: string[]
}

interface MissingFacts {
  missing_facts: string[]
  suggested_fields: FieldDefinition[]
}

interface FactEntryProps {
  onFactsAdded: () => void
  onSkip: () => void
}

export default function FactEntry({ onFactsAdded, onSkip }: FactEntryProps) {
  const [missingFacts, setMissingFacts] = useState<MissingFacts | null>(null)
  const [loading, setLoading] = useState(true)
  const [factValues, setFactValues] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    fetchMissingFacts()
  }, [])

  const fetchMissingFacts = async () => {
    try {
      const response = await fetch('/api/v1/facts/missing')
      if (!response.ok) throw new Error('Failed to fetch missing facts')
      const data = await response.json()
      setMissingFacts(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load missing facts')
    } finally {
      setLoading(false)
    }
  }

  const handleValueChange = (factKey: string, value: string) => {
    setFactValues(prev => ({ ...prev, [factKey]: value }))
  }

  const handleSave = async () => {
    setSaving(true)
    setError('')
    setSuccess(false)

    try {
      // Create all facts that have values
      const factsToCreate = Object.entries(factValues)
        .filter(([_, value]) => value.trim() !== '')
        .map(([factKey, value]) => ({
          fact_key: factKey,
          fact_value: value.trim()
        }))

      if (factsToCreate.length === 0) {
        setError('Please enter at least one fact')
        setSaving(false)
        return
      }

      // Create facts one by one
      const promises = factsToCreate.map(async fact => {
        const res = await fetch('/api/v1/facts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(fact)
        })
        
        if (!res.ok) {
          const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }))
          throw new Error(errorData.detail || `Failed to create ${fact.fact_key}`)
        }
        
        return res.json()
      })

      await Promise.all(promises)
      setSuccess(true)
      setTimeout(() => {
        onFactsAdded()
      }, 1000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save facts')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="fact-entry loading">Loading...</div>
  }

  if (!missingFacts || missingFacts.suggested_fields.length === 0) {
    return (
      <div className="fact-entry">
        <div className="all-facts-present">
          <h3>✓ All Information Complete</h3>
          <p>You have all the essential company information in your Memory Graph.</p>
          <button onClick={onSkip} className="continue-button">Continue</button>
        </div>
      </div>
    )
  }

  return (
    <div className="fact-entry">
      <div className="fact-entry-header">
        <h2>Enter Company Information</h2>
        <p>Please provide the following information to populate your Memory Graph. This will be used to auto-fill future documents.</p>
      </div>

      <div className="facts-form">
        {missingFacts.suggested_fields.map((field) => (
          <div key={field.fact_key} className="fact-input-group">
            <label htmlFor={field.fact_key}>
              {field.fact_key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              <span className="field-description">{field.description}</span>
            </label>
            <input
              id={field.fact_key}
              type="text"
              value={factValues[field.fact_key] || ''}
              onChange={(e) => handleValueChange(field.fact_key, e.target.value)}
              placeholder={field.examples.length > 0 ? `e.g., ${field.examples[0]}` : 'Enter value'}
              className="fact-input"
            />
            {field.examples.length > 0 && (
              <div className="field-examples">
                Examples: {field.examples.slice(0, 2).join(', ')}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="fact-entry-actions">
        <button onClick={onSkip} className="skip-button" disabled={saving}>
          Skip for Now
        </button>
        <button 
          onClick={handleSave} 
          className="save-button"
          disabled={saving || Object.values(factValues).every(v => !v.trim())}
        >
          {saving ? 'Saving...' : 'Save Information'}
        </button>
      </div>

      {error && <div className="message error">{error}</div>}
      {success && <div className="message success">Information saved successfully!</div>}
    </div>
  )
}

