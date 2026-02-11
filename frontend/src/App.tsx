import { useState, useEffect } from 'react'
import './App.css'
import DocumentList from './components/DocumentList'
import FactsView from './components/FactsView'
import FactEntry from './components/FactEntry'
import UnifiedWorkflow from './components/UnifiedWorkflow'

function App() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...')
  const [activeTab, setActiveTab] = useState<'workflow' | 'documents' | 'facts'>('workflow')
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [showFactEntry, setShowFactEntry] = useState(false)

  useEffect(() => {
    // Check backend health on mount
    fetch('/api/v1/health')
      .then(res => res.json())
      .then(data => {
        setHealthStatus(data.status === 'healthy' ? '✅ Connected' : '❌ Unhealthy')
      })
      .catch(() => {
        setHealthStatus('❌ Backend not available')
      })
  }, [])

  const handleFactsAdded = () => {
    setShowFactEntry(false)
    setRefreshTrigger(prev => prev + 1)
    setActiveTab('facts')
  }

  const handleSkipFactEntry = () => {
    setShowFactEntry(false)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Paperwork Co-pilot</h1>
        <p className="status">Backend Status: {healthStatus}</p>
      </header>
      
      <nav className="app-nav">
        <button 
          className={activeTab === 'workflow' ? 'active' : ''}
          onClick={() => setActiveTab('workflow')}
        >
          Upload & Fill
        </button>
        <button 
          className={activeTab === 'documents' ? 'active' : ''}
          onClick={() => setActiveTab('documents')}
        >
          Documents
        </button>
        <button 
          className={activeTab === 'facts' ? 'active' : ''}
          onClick={() => setActiveTab('facts')}
        >
          Company Facts
        </button>
      </nav>

      <main className="app-main">
        {showFactEntry ? (
          <FactEntry 
            onFactsAdded={handleFactsAdded}
            onSkip={handleSkipFactEntry}
          />
        ) : (
          <>
            {activeTab === 'workflow' && (
              <UnifiedWorkflow />
            )}
            {activeTab === 'documents' && (
              <DocumentList key={refreshTrigger} />
            )}
            {activeTab === 'facts' && (
              <FactsView key={refreshTrigger} />
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App

