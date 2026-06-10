export default function SummaryPanel({ summary }) {
  if (!summary) {
    return (
      <div className="summary-text">
        <p className="text-muted">Analysis summary will appear here after querying.</p>
      </div>
    )
  }

  const lines = summary.split('\n').map(l => l.replace(/^[-•]\s*/, '')).filter(Boolean)

  return (
    <div className="summary-text">
      {lines.map((line, idx) => (
        <div key={idx} className="bullet-line">
          • {line}
        </div>
      ))}
    </div>
  )
}
