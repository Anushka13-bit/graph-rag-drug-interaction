import { useState } from 'react'

export default function QueryInput({ onAnalyze, onClear, loading }) {
  const [input, setInput] = useState('')
  const [topK, setTopK] = useState(5)

  const handleSubmit = () => {
    const drugs = input.split(',').map(d => d.trim()).filter(Boolean)
    if (drugs.length > 0) {
      onAnalyze(drugs, topK)
    }
  }

  const handleClear = () => {
    setInput('')
    setTopK(5)
    onClear()
  }

  return (
    <section className="card input-card">
      <div className="card-header">
        <h2>Query</h2>
      </div>
      <div className="card-body">
        <div className="form-row">
          <div className="form-field form-field--grow">
            <label htmlFor="drugInput">Drug Names</label>
            <input
              type="text"
              id="drugInput"
              placeholder="e.g. Warfarin, Aspirin, Metformin"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            />
            <span className="form-hint">Separate multiple drugs with commas</span>
          </div>
          <div className="form-field">
            <label htmlFor="topK">Top K</label>
            <input
              type="number"
              id="topK"
              min="1"
              max="20"
              value={topK}
              onChange={e => setTopK(Number(e.target.value))}
            />
          </div>
        </div>
        <div className="form-actions">
          <button className="btn btn--primary" onClick={handleSubmit} disabled={loading || !input.trim()}>
            <svg className="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
            </svg>
            <span className={loading ? "hidden" : ""}>Analyze Interactions</span>
            {loading && <span className="btn-spinner" aria-hidden="true"></span>}
          </button>
          <button className="btn btn--ghost" onClick={handleClear} disabled={loading}>
            Clear
          </button>
        </div>
      </div>
    </section>
  )
}
