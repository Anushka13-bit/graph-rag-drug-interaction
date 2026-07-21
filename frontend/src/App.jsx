import { useState, useCallback } from 'react'
import './App.css'
import Header from './components/Header'
import QueryInput from './components/QueryInput'
import StatsBar from './components/StatsBar'
import InteractionCards from './components/InteractionCards'
import NetworkGraph from './components/NetworkGraph'
import SeverityChart from './components/SeverityChart'
import SummaryPanel from './components/SummaryPanel'
import JsonPanel from './components/JsonPanel'

export default function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAnalyze = useCallback(async (drugs, topK) => {
    setLoading(true)
    setError(null)
    setData(null)

    try {
      const question = `Check interactions between: ${drugs.join(', ')}`
      const res = await fetch('/query/interact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          top_k: topK,
          include_graph_paths: true,
          stream: false,
        }),
      })

      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const json = await res.json()
      setData(json)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleClear = useCallback(() => {
    setData(null)
    setError(null)
  }, [])

  const interactions = data?.interactions || []
  const severityCounts = { mild: 0, moderate: 0, severe: 0 }
  interactions.forEach(i => { severityCounts[i.severity]++ })

  const maxSeverity = interactions.length > 0
    ? (severityCounts.severe > 0 ? 'Severe' : severityCounts.moderate > 0 ? 'Moderate' : 'Mild')
    : '—'

  return (
    <>
      <Header />

      <main className="main">
        <QueryInput
          onAnalyze={handleAnalyze}
          onClear={handleClear}
          loading={loading}
        />

        {error && (
          <div className="alert alert--error">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="alert-icon">
              <circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/>
            </svg>
            <span>{error}</span>
          </div>
        )}

        <StatsBar
          drugsCount={data?.drugs_queried?.length || 0}
          interactionsCount={data?.total_interactions || 0}
          maxSeverity={maxSeverity}
          confidence={data ? (interactions.length > 0 ? 'Available' : 'Low') : '—'}
        />

        <SummaryPanel summary={data?.summary} severity={maxSeverity} />

        <div className="results-grid">
          <InteractionCards interactions={interactions} />
          <NetworkGraph graphData={data?.graph_data} />
        </div>

        <div className="charts-row">
          <SeverityChart counts={severityCounts} hasData={interactions.length > 0} />
          {/* SummaryPanel moved up */}
        </div>

        <JsonPanel data={data} />
      </main>

      <footer className="footer">
        <p>&copy; 2024 Drug Interaction Analyzer &mdash; For informational purposes only. Always consult healthcare professionals.</p>
      </footer>
    </>
  )
}
