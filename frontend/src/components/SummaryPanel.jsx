export default function SummaryPanel({ summary, severity }) {
  if (!summary) return null;

  const lines = summary.split('\n').map(l => l.replace(/^[-•]\s*/, '')).filter(Boolean)
  const sevClass = severity ? severity.toLowerCase() : 'unknown'

  return (
    <div className={`summary-hero severity-${sevClass}`}>
      <div className="summary-hero-icon">
        {sevClass === 'severe' ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4m0 4h.01"/></svg>
        ) : sevClass === 'moderate' ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg>
        )}
      </div>
      <div className="summary-hero-content">
        <h2 className="summary-hero-title">AI Interaction Analysis</h2>
        <div className="summary-hero-text">
          {lines.map((line, idx) => (
            <p key={idx} className="summary-hero-line">{line}</p>
          ))}
        </div>
      </div>
    </div>
  )
}
