import React from 'react';

interface LineChartProps {
  history: number[];
  title?: string;
  subtitle?: string;
  unit?: string;
  color?: string;
}

export const LineChart: React.FC<LineChartProps> = ({ 
  history,
  title = "Progression Cognitive",
  subtitle = "Découverte d'états au fil du temps",
  unit = "États",
  color = "#3b82f6"
}) => {
  if (history.length < 2) {
    return (
      <div className="panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '224px' }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Collecte des données...</span>
      </div>
    );
  }

  const width = 300;
  const height = 130;
  const paddingLeft = 35;
  const paddingBottom = 20;
  const paddingTop = 10;
  const paddingRight = 10;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  let maxVal = Math.max(...history);
  let minVal = Math.min(...history);
  
  // Add some padding to bounds
  if (maxVal === minVal) {
    maxVal += 1;
    minVal -= 1;
  } else {
    const margin = (maxVal - minVal) * 0.1;
    maxVal += margin;
    minVal -= margin;
  }
  
  const valRange = maxVal - minVal;

  // Generate points
  const points = history.map((val, index) => {
    const x = paddingLeft + (index / (history.length - 1)) * chartWidth;
    const y = paddingTop + chartHeight - ((val - minVal) / valRange) * chartHeight;
    return { x, y, val };
  });

  // SVG Line path
  const linePath = points.reduce((path, pt, index) => {
    return index === 0 ? `M ${pt.x} ${pt.y}` : `${path} L ${pt.x} ${pt.y}`;
  }, '');

  // SVG Area path for fill
  const areaPath = points.length > 0 
    ? `${linePath} L ${points[points.length - 1].x} ${paddingTop + chartHeight} L ${points[0].x} ${paddingTop + chartHeight} Z`
    : '';

  const gradientId = `chartGradient-${title.replace(/\s+/g, '-')}`;

  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '224px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <h4 className="panel-title">{title}</h4>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '11px',
          color: color,
          backgroundColor: `${color}1a`, // 10% opacity
          border: `1px solid ${color}33`, // 20% opacity
          padding: '2px 6px',
          borderRadius: '4px'
        }}>
          {Number(history[history.length - 1].toFixed(1))} {unit}
        </span>
      </div>
      <div className="relative" style={{ width: '100%', flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.4" />
              <stop offset="100%" stopColor={color} stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line x1={paddingLeft} y1={paddingTop} x2={width - paddingRight} y2={paddingTop} stroke="#1e293b" strokeDasharray="3 3" />
          <line x1={paddingLeft} y1={paddingTop + chartHeight / 2} x2={width - paddingRight} y2={paddingTop + chartHeight / 2} stroke="#1e293b" strokeDasharray="3 3" />
          <line x1={paddingLeft} y1={paddingTop + chartHeight} x2={width - paddingRight} y2={paddingTop + chartHeight} stroke="#334155" />

          {/* Y Axis Labels */}
          <text x={paddingLeft - 8} y={paddingTop + 4} fill="#64748b" fontSize="8" textAnchor="end" fontFamily="monospace">{Math.round(maxVal)}</text>
          <text x={paddingLeft - 8} y={paddingTop + chartHeight / 2 + 3} fill="#64748b" fontSize="8" textAnchor="end" fontFamily="monospace">{Math.round((maxVal + minVal) / 2)}</text>
          <text x={paddingLeft - 8} y={paddingTop + chartHeight + 3} fill="#64748b" fontSize="8" textAnchor="end" fontFamily="monospace">{Math.round(minVal)}</text>

          {/* Fill Area */}
          {areaPath && <path d={areaPath} fill={`url(#${gradientId})`} />}

          {/* Line */}
          {linePath && (
            <path
              d={linePath}
              fill="none"
              stroke={color}
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Endpoint Glow Dot */}
          {points.length > 0 && (
            <circle
              cx={points[points.length - 1].x}
              cy={points[points.length - 1].y}
              r="4"
              fill={color}
              stroke="#ffffff"
              strokeWidth="1.5"
              style={{ filter: `drop-shadow(0px 0px 4px ${color})` }}
            />
          )}
        </svg>
      </div>
      <div style={{ fontSize: '9px', color: 'var(--text-muted)', textAlign: 'center', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '4px' }}>
        {subtitle}
      </div>
    </div>
  );
};
