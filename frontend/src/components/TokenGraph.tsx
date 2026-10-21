import { useStore } from '../stores/useStore';

function riskColor(score: number): string {
  if (score >= 0.8) return '#ef4444';
  if (score >= 0.6) return '#f97316';
  if (score >= 0.4) return '#eab308';
  return '#22c55e';
}

export function TokenGraph() {
  const { nodes } = useStore();

  return (
    <div className="graph-overlay">
      {nodes.map((n) => {
        const size = Math.max(28, Math.min(56, 20 + Math.log10(n.liquidity_usd + 1) * 6));
        const color = riskColor(n.risk_score);
        return (
          <div
            key={n.id}
            className="token-node"
            style={{
              left: `${(n.x / 800) * 100}%`,
              top: `${(n.y / 600) * 100}%`,
              width: size,
              height: size,
              borderColor: color,
              boxShadow: `0 0 12px ${color}55`,
            }}
            title={`${n.symbol}\n$${n.price}\n${n.change_24h > 0 ? '+' : ''}${n.change_24h}%\nRisk: ${n.risk_score}\n${n.explanation}`}
          >
            <span className="node-symbol">{n.symbol}</span>
            <span className="node-change" style={{ color: n.change_24h >= 0 ? '#22c55e' : '#ef4444' }}>
              {n.change_24h >= 0 ? '+' : ''}{n.change_24h.toFixed(1)}%
            </span>
          </div>
        );
      })}
      {nodes.length === 0 && (
        <div className="graph-empty">En attente de scan…</div>
      )}
    </div>
  );
}
