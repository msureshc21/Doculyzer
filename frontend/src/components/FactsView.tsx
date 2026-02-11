import { useState, useEffect } from 'react'
import './FactsView.css'

interface Fact {
  id: number
  fact_key: string
  fact_value: string
  confidence: number
  edit_count: number
  updated_at: string
}

export default function FactsView() {
  const [facts, setFacts] = useState<Fact[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  const fetchFacts = async () => {
    try {
      const response = await fetch('/api/v1/facts')
      if (!response.ok) throw new Error('Failed to fetch facts')
      const data = await response.json()
      setFacts(data.facts || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load facts')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFacts()
  }, [])

  if (loading) return <div className="loading">Loading facts...</div>
  if (error) return <div className="error-message">{error}</div>

  return (
    <div className="facts-view">
      <div className="list-header">
        <h2>Company Facts ({facts.length})</h2>
        <button onClick={fetchFacts} className="refresh-button">Refresh</button>
      </div>
      
      {facts.length === 0 ? (
        <div className="empty-state">No facts in Memory Graph yet. Upload documents to extract facts.</div>
      ) : (
        <div className="facts-grid">
          {facts.map((fact) => (
            <div key={fact.id} className="fact-card">
              <div className="fact-key">{fact.fact_key.replace(/_/g, ' ')}</div>
              <div className="fact-value">{fact.fact_value}</div>
              <div className="fact-meta">
                <span className="confidence">Confidence: {(fact.confidence * 100).toFixed(0)}%</span>
                {fact.edit_count > 0 && (
                  <span className="user-edited">✓ User-verified ({fact.edit_count} edit{fact.edit_count > 1 ? 's' : ''})</span>
                )}
              </div>
              <div className="fact-updated">
                Updated: {new Date(fact.updated_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

