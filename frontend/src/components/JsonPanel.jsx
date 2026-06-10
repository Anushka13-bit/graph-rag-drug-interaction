import { useState } from 'react'

export default function JsonPanel({ data }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    if (!data) return
    navigator.clipboard.writeText(JSON.stringify(data, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <section className="card" id="jsonCard">
      <div className="card-header">
        <h2>API Response</h2>
        <button className="btn btn--small btn--ghost" title="Copy JSON" onClick={handleCopy} disabled={!data}>
          {copied ? (
            <span className="copy-toast">Copied!</span>
          ) : (
            <>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="btn-icon">
                <rect x="9" y="9" width="13" height="13" rx="2"/>
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
              </svg>
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="card-body">
        <pre className="json-display">
          <code>{data ? JSON.stringify(data, null, 2) : '{}'}</code>
        </pre>
      </div>
    </section>
  )
}
