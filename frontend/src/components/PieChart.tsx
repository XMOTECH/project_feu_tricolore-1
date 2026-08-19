import React from 'react';

interface PieChartProps {
  stays: number;
  switches: number;
}

export const PieChart: React.FC<PieChartProps> = ({ stays, switches }) => {
  const total = stays + switches;
  if (total === 0) {
    return (
      <div className="panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '224px' }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Aucune donnée disponible</span>
      </div>
    );
  }

  const stayPercentage = (stays / total) * 100;
  const switchPercentage = (switches / total) * 100;

  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const stayStrokeDash = (stayPercentage / 100) * circumference;

  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'space-between', height: '224px' }}>
      <h4 className="panel-title" style={{ marginBottom: '8px' }}>Équilibre des Actions</h4>
      <div className="relative" style={{ width: '112px', height: '112px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width="100%" height="100%" viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
          {/* Base circle background */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="transparent"
            stroke="#1e293b"
            strokeWidth="10"
          />
          {/* Stay segment */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="transparent"
            stroke="var(--color-green)"
            strokeWidth="10"
            strokeDasharray={`${stayStrokeDash} ${circumference}`}
            strokeLinecap="round"
            style={{ transition: 'all 0.5s ease-out' }}
          />
          {/* Switch segment */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="transparent"
            stroke="var(--color-red)"
            strokeWidth="10"
            strokeDasharray={`${circumference - stayStrokeDash} ${circumference}`}
            strokeDashoffset={-stayStrokeDash}
            strokeLinecap="round"
            style={{ transition: 'all 0.5s ease-out' }}
          />
        </svg>
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
          <span style={{ fontSize: '24px', fontWeight: 900, color: 'white', lineHeight: 1 }}>{total}</span>
          <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: '4px' }}>ÉTATS</span>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '100%', marginTop: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="status-led online" style={{ height: '8px', width: '8px', boxShadow: 'none' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Rester (Stay)</span>
          </div>
          <span style={{ fontWeight: 600, color: 'var(--color-green)' }}>{stays} ({Math.round(stayPercentage)}%)</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="status-led error" style={{ height: '8px', width: '8px', boxShadow: 'none' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Changer (Switch)</span>
          </div>
          <span style={{ fontWeight: 600, color: 'var(--color-red)' }}>{switches} ({Math.round(switchPercentage)}%)</span>
        </div>
      </div>
    </div>
  );
};
