export default function InteractionCards({ interactions }) {
  return (
    <section className="card">
      <div className="card-header">
        <h2>Interactions</h2>
        <span className="badge">{interactions.length}</span>
      </div>
      <div className="card-body">
        {interactions.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M9 12h6m-3-3v6m-7.5 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15A2.25 2.25 0 002.25 6.75v10.5A2.25 2.25 0 004.5 19.5z"/>
            </svg>
            <p>Enter drugs above and click <strong>Analyze</strong></p>
          </div>
        ) : (
          <div className="interactions-list">
            {interactions.map((ix, idx) => (
              <div key={idx} className={`interaction-item ${ix.severity || 'moderate'}`}>
                <div className="ix-header">
                  <span className="ix-drugs">{ix.drug_a} &amp; {ix.drug_b}</span>
                  <span className={`severity-badge ${ix.severity || 'moderate'}`}>{ix.severity || 'Moderate'}</span>
                </div>
                <div className="ix-type">Type: {ix.interaction_type}</div>
                <div className="ix-desc">{ix.description}</div>
                <div className="ix-meta">
                  <span><strong>Evidence:</strong> {ix.evidence_count} source(s)</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
