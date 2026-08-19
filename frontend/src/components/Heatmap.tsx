import React from 'react';

interface HeatmapProps {
  qTable: Record<string, [number, number]>;
}

export const Heatmap: React.FC<HeatmapProps> = ({ qTable }) => {
  const states = Object.entries(qTable);

  if (states.length === 0) {
    return (
      <div className="panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '280px' }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>En attente de données d'apprentissage...</span>
      </div>
    );
  }

  // Sort states by highest max Q-value
  const sortedStates = [...states]
    .sort((a, b) => Math.max(...b[1]) - Math.max(...a[1]))
    .slice(0, 12); // top 12 states

  const parseStateKey = (key: string) => {
    const parts = key.split('_');
    if (parts.length >= 6) {
      return {
        counts: `N:${parts[0]} S:${parts[1]} E:${parts[2]} O:${parts[3]}`,
        phase: parts[4],
        time: `T:${parts[5]}`
      };
    }
    return { counts: key, phase: '?', time: '?' };
  };

  return (
    <div className="panel heatmap-container">
      <div className="heatmap-header">
        <div>
          <h4 className="panel-title" style={{ fontSize: '12px' }}>Politique de Confiance</h4>
          <p className="heatmap-subtitle">Top 12 des états classés par valeur de récompense (Q-value)</p>
        </div>
        <div className="heatmap-legend">
          <div className="legend-item">
            <span className="legend-color stay" />
            <span style={{ color: 'var(--text-secondary)' }}>Rester (Stay)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color switch" />
            <span style={{ color: 'var(--text-secondary)' }}>Changer (Switch)</span>
          </div>
        </div>
      </div>

      <div className="heatmap-grid">
        {sortedStates.map(([key, values]) => {
          const info = parseStateKey(key);
          const diff = values[0] - values[1]; // Stay - Switch
          const isStay = diff > 0;
          const absDiff = Math.abs(diff);

          // Calculate color intensity based on the delta value (confidence)
          const intensity = Math.min(0.8, 0.2 + absDiff * 0.05);

          const bgColor = isStay 
            ? `rgba(16, 185, 129, ${intensity})` // Emerald alpha
            : `rgba(239, 68, 68, ${intensity})`; // Rose alpha

          const borderColor = isStay 
            ? `rgba(52, 211, 153, ${intensity + 0.1})` 
            : `rgba(248, 113, 113, ${intensity + 0.1})`;

          const glowColor = isStay ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)';
          const bestVal = Math.max(...values);

          return (
            <div
              key={key}
              style={{
                backgroundColor: bgColor,
                borderColor: borderColor,
                boxShadow: `0 0 10px ${glowColor}`
              }}
              className="heatmap-cell group"
            >
              {/* Custom CSS Hover Tooltip Card */}
              <div className="heatmap-tooltip">
                <div className="tooltip-title">Politique Q-Value</div>
                <div className="tooltip-state">{info.counts} • Phase {info.phase}</div>
                
                <div className="tooltip-metrics">
                  <div className="tooltip-row">
                    <span className="tooltip-dot stay"></span>
                    <span className="tooltip-label">Rester (Stay):</span>
                    <span className="tooltip-value">{values[0].toFixed(3)}</span>
                  </div>
                  <div className="tooltip-row">
                    <span className="tooltip-dot switch"></span>
                    <span className="tooltip-label">Changer (Switch):</span>
                    <span className="tooltip-value">{values[1].toFixed(3)}</span>
                  </div>
                </div>

                <div className="tooltip-diff">
                  <span>Delta (Confiance) :</span>
                  <strong>{absDiff.toFixed(2)}</strong>
                </div>
              </div>

              <div className="heatmap-cell-top">
                <span className="cell-counts">{info.counts}</span>
                <span className="cell-phase">{info.phase}</span>
              </div>
              
              <div className="heatmap-cell-bottom">
                <span className="cell-action">
                  {isStay ? 'RESTER' : 'CHANGER'}
                </span>
                <span className="cell-qvals">
                  Q: {bestVal.toFixed(2)} | Diff: {absDiff.toFixed(1)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
