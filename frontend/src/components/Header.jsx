export default function Header() {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="header-brand">
          <svg className="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
          <div>
            <h1>Drug Interaction Analyzer</h1>
            <p className="header-subtitle">Clinical Decision Support System</p>
          </div>
        </div>
        <div className="header-status">
          <span className="status-dot"></span>
          <span>System Ready</span>
        </div>
      </div>
    </header>
  )
}
