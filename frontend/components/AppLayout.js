export default function AppLayout({ children }) {
  return (
    <div className="platform-shell">
      <aside className="platform-aside">
        <h2>LICEU</h2>
        <div className="platform-nav">
          <div className="platform-nav-item">Command Center</div>
          <div className="platform-nav-item">Obras</div>
          <div className="platform-nav-item">Investimentos</div>
          <div className="platform-nav-item">P&D</div>
          <div className="platform-nav-item">CRM</div>
          <div className="platform-nav-item">Econotech</div>
        </div>
      </aside>

      <main className="platform-main">{children}</main>
    </div>
  );
}
