import { useStore } from '../stores/useStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { Spider } from './Spider';
import { TokenGraph } from './TokenGraph';

export function Dashboard() {
  const { status, events, jev, paperStats, connected, spiderState } = useStore();
  const { sendControl } = useWebSocket();

  const mode = status?.trading_mode ?? 'paper';
  const emergency = status?.emergency_stop ?? false;

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <span className="logo-icon">SJ</span>
          <span>SPIDER JARVIS</span>
          <span className="version">v0.1</span>
        </div>
        <div className="badges">
          <span className={`badge ${mode === 'paper' ? 'badge-paper' : 'badge-live'}`}>
            {mode === 'paper' ? 'PAPER TRADING' : 'LIVE TRADING'}
          </span>
          {!status?.live_trading_enabled && (
            <span className="badge badge-disabled">LIVE DISABLED</span>
          )}
          <span className={`badge ${connected ? 'badge-ok' : 'badge-err'}`}>
            {connected ? 'WS CONNECTED' : 'WS OFFLINE'}
          </span>
          <span className={`badge ${status?.risk_engine_status === 'ACTIVE' ? 'badge-ok' : 'badge-err'}`}>
            RISK: {status?.risk_engine_status ?? '—'}
          </span>
          {emergency && <span className="badge badge-err pulse">EMERGENCY STOP</span>}
        </div>
      </header>

      <div className="main-grid">
        <section className="scene-panel">
          <div className="scene-canvas">
            <div className="grid-bg" />
            <TokenGraph />
            <Spider />
          </div>
          <div className="scene-footer">
            <span>Etat: <strong style={{ color: 'var(--accent)' }}>{spiderState}</strong></span>
            <span>Scans: {status?.scans_count ?? 0}</span>
            <span>Derniere action: {status?.last_action ?? '—'}</span>
          </div>
        </section>

        <aside className="side-panels">
          <div className="panel">
            <h3>Controles</h3>
            <div className="btn-row">
              <button onClick={() => sendControl('start')} className="btn btn-cyan">Start</button>
              <button onClick={() => sendControl('pause')} className="btn">Pause</button>
              <button onClick={() => sendControl('resume')} className="btn">Resume</button>
              <button onClick={() => sendControl('scan_now')} className="btn btn-cyan">Scan now</button>
            </div>
            <div className="btn-row">
              <button onClick={() => sendControl('reset_paper')} className="btn">Reset paper</button>
              <button onClick={() => sendControl('clear_graph')} className="btn">Clear graph</button>
              <button onClick={() => sendControl('emergency_stop')} className="btn btn-danger">
                EMERGENCY STOP
              </button>
              {emergency && (
                <button onClick={() => sendControl('clear_emergency')} className="btn btn-warn">
                  Clear emergency
                </button>
              )}
            </div>
          </div>

          <div className="panel">
            <h3>Paper Trading</h3>
            <div className="stats-grid">
              <div><span className="label">Solde</span><span className="value">${paperStats?.paper_balance?.toFixed(2) ?? '10000.00'}</span></div>
              <div><span className="label">PnL total</span><span className={`value ${(paperStats?.total_pnl ?? 0) >= 0 ? 'pos' : 'neg'}`}>${paperStats?.total_pnl?.toFixed(2) ?? '0.00'}</span></div>
              <div><span className="label">PnL jour</span><span className={`value ${(paperStats?.daily_pnl ?? 0) >= 0 ? 'pos' : 'neg'}`}>${paperStats?.daily_pnl?.toFixed(2) ?? '0.00'}</span></div>
              <div><span className="label">Positions</span><span className="value">{paperStats?.open_positions ?? 0}</span></div>
              <div><span className="label">Trades</span><span className="value">{paperStats?.trade_count ?? 0}</span></div>
              <div><span className="label">Win rate</span><span className="value">{((paperStats?.win_rate ?? 0) * 100).toFixed(0)}%</span></div>
              <div><span className="label">Exposition</span><span className="value">${paperStats?.exposure?.toFixed(0) ?? 0}</span></div>
              <div><span className="label">Frais sim.</span><span className="value">${paperStats?.total_fees?.toFixed(2) ?? '0.00'}</span></div>
            </div>
          </div>

          <div className="panel">
            <h3>JEV Decision</h3>
            {jev ? (
              <div className="jev-box">
                <div className="jev-decision" data-dec={jev.decision}>{jev.decision}</div>
                <div className="jev-meta">
                  <span>Confiance: {(jev.confidence * 100).toFixed(0)}%</span>
                  <span>Risque: {(jev.risk_score * 100).toFixed(0)}%</span>
                  <span>{jev.symbol}</span>
                </div>
                <p className="jev-summary">{jev.summary}</p>
                <div className="tags">
                  {jev.reason_codes?.map((code) => (
                    <span key={code} className="tag">{code}</span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="muted">Aucune decision encore</p>
            )}
          </div>

          <div className="panel panel-log">
            <h3>Journal temps reel</h3>
            <div className="log-list">
              {events.length === 0 && <p className="muted">En attente d evenements...</p>}
              {events.slice(0, 40).map((e) => (
                <div key={e.id} className={`log-line level-${e.level}`}>
                  <span className="log-time">{new Date(e.timestamp).toLocaleTimeString()}</span>
                  <span className="log-type">{e.event_type}</span>
                  <span className="log-msg">{e.message}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>

      <footer className="footer">
        <span>Mode: <strong>{mode.toUpperCase()}</strong></span>
        <span>Live trading: <strong>{status?.live_trading_enabled ? 'ENABLED' : 'DISABLED'}</strong></span>
        <span>Donnees: {status?.data_connection ?? '—'}</span>
        <span>Derniere sync: {status?.last_data_update ? new Date(status.last_data_update).toLocaleTimeString() : '—'}</span>
        <a href="http://localhost:8000/api/safety" target="_blank" rel="noreferrer">Safety Center</a>
      </footer>
    </div>
  );
}
