export default function StatsBar({ drugsCount, interactionsCount, maxSeverity, confidence }) {
  return (
    <section className="stats-bar">
      <div className="stat">
        <span className="stat-value">{drugsCount}</span>
        <span className="stat-label">Drugs Analyzed</span>
      </div>
      <div className="stat">
        <span className="stat-value">{interactionsCount}</span>
        <span className="stat-label">Interactions</span>
      </div>
      <div className="stat">
        <span className="stat-value" style={{ 
          color: maxSeverity === 'Severe' ? 'var(--sev-severe)' : 
                 maxSeverity === 'Moderate' ? 'var(--sev-mod)' : 
                 maxSeverity === 'Mild' ? 'var(--sev-mild)' : 'inherit'
        }}>
          {maxSeverity}
        </span>
        <span className="stat-label">Max Severity</span>
      </div>
      <div className="stat">
        <span className="stat-value">{confidence}</span>
        <span className="stat-label">Confidence</span>
      </div>
    </section>
  )
}
