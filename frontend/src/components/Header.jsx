export default function Header({ isConnected }) {
  return (
    <header className="app-header">
      <div className="header-inner">
        <a href="/" className="logo">
          <span className="emoji">🍳</span>
          <span className="gradient-text">Smart Chef</span>
        </a>
        <div className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`}>
          <span className="status-dot"></span>
          {isConnected ? 'Live' : 'Offline'}
        </div>
      </div>
    </header>
  );
}
