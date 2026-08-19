import { useState, useEffect, useMemo } from 'react';
import { SimulationEngine } from './simulation/SimulationEngine';
import { TrafficCanvas } from './components/TrafficCanvas';
import { PieChart } from './components/PieChart';
import { LineChart } from './components/LineChart';
import { Heatmap } from './components/Heatmap';
import type { SimulationStats, LogEntry } from './simulation/types';

const BACKEND_URL = "http://localhost:8000";

const Icons = {
  lightning: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  ),
  chart: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  ),
  play: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style={{ flexShrink: 0 }}>
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  ),
  pause: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style={{ flexShrink: 0 }}>
      <rect x="6" y="4" width="4" height="16" />
      <rect x="14" y="4" width="4" height="16" />
    </svg>
  ),
  reset: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
    </svg>
  ),
  road: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <rect x="4" y="2" width="16" height="20" rx="2" />
      <line x1="12" y1="2" x2="12" y2="22" strokeDasharray="4 4" />
    </svg>
  ),
  clock: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  moon: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  ),
  sliders: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <line x1="4" y1="21" x2="4" y2="14" />
      <line x1="4" y1="10" x2="4" y2="3" />
      <line x1="12" y1="21" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12" y2="3" />
      <line x1="20" y1="21" x2="20" y2="16" />
      <line x1="20" y1="12" x2="20" y2="3" />
      <line x1="1" y1="14" x2="7" y2="14" />
      <line x1="9" y1="8" x2="15" y2="8" />
      <line x1="17" y1="16" x2="23" y2="16" />
    </svg>
  ),
  cpu: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <rect x="9" y="9" width="6" height="6" />
      <line x1="9" y1="1" x2="9" y2="4" />
      <line x1="15" y1="1" x2="15" y2="4" />
      <line x1="9" y1="20" x2="9" y2="23" />
      <line x1="15" y1="20" x2="15" y2="23" />
      <line x1="20" y1="9" x2="23" y2="9" />
      <line x1="20" y1="15" x2="23" y2="15" />
      <line x1="1" y1="9" x2="4" y2="9" />
      <line x1="1" y1="15" x2="4" y2="15" />
    </svg>
  ),
  car: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2" />
      <circle cx="7" cy="17" r="2" />
      <circle cx="17" cy="17" r="2" />
    </svg>
  ),
  fluidity: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <path d="M12 2a10 10 0 0 1 8 16" />
      <path d="M12 2a10 10 0 0 0-8 16" />
      <circle cx="12" cy="12" r="3" />
      <line x1="12" y1="12" x2="16" y2="8" />
    </svg>
  ),
  trafficLight: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <rect x="8" y="2" width="8" height="20" rx="2" />
      <circle cx="12" cy="6" r="2" />
      <circle cx="12" cy="12" r="2" />
      <circle cx="12" cy="18" r="2" />
    </svg>
  ),
  alert: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  )
};

function ChronometerDial({ timeStr }: { timeStr: string }) {
  const [, secondsStr] = timeStr.split(':');
  const seconds = parseInt(secondsStr, 10) || 0;
  
  const circumference = 2 * Math.PI * 40; // 251.3
  const strokeDashoffset = circumference - (seconds / 60) * circumference;
  const needleRotation = seconds * 6; // 360 / 60 = 6 degrees per second

  return (
    <div className="chronometer-widget">
      <div className="chronometer-dial">
        <svg width="76" height="76" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle cx="50" cy="50" r="46" fill="var(--bg-input)" stroke="var(--border-color)" strokeWidth="1.5" />
          
          {/* 12 major ticks */}
          <circle 
            cx="50" 
            cy="50" 
            r="40" 
            fill="none" 
            stroke="var(--text-muted)" 
            strokeWidth="2" 
            strokeDasharray="1.5 19.44" 
            transform="rotate(-90 50 50)"
          />
          
          {/* Seconds Progress Ring */}
          <circle 
            cx="50" 
            cy="50" 
            r="40" 
            fill="none" 
            stroke="var(--color-blue)" 
            strokeWidth="3" 
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            transform="rotate(-90 50 50)"
            style={{ transition: 'stroke-dashoffset 0.5s ease' }}
          />

          {/* Sweeping Pointer (Outer segment) */}
          <line 
            x1="50" 
            y1="25" 
            x2="50" 
            y2="15" 
            stroke="var(--color-orange)" 
            strokeWidth="3" 
            strokeLinecap="round"
            transform={`rotate(${needleRotation} 50 50)`}
            style={{ 
              transition: 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
              transformOrigin: '50px 50px'
            }}
          />

          {/* Central Digital Time */}
          <text 
            x="50" 
            y="54" 
            textAnchor="middle" 
            fill="var(--text-primary)" 
            fontSize="14" 
            fontWeight="800" 
            fontFamily="var(--font-mono)"
          >
            {timeStr}
          </text>

          {/* Label below the time */}
          <text 
            x="50" 
            y="70" 
            textAnchor="middle" 
            fill="var(--text-muted)" 
            fontSize="8" 
            fontWeight="700" 
            letterSpacing="0.05em"
          >
            TEMPS
          </text>
        </svg>
      </div>
      <div className="chronometer-info">
        <span className="stats-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--text-secondary)' }}>
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          Temps Écoulé
        </span>
        <span className="chronometer-digital">{timeStr}</span>
      </div>
    </div>
  );
}

function TrafficPhaseVisualizer({ phase }: { phase: string }) {
  const getLightStatesFromPhase = (p: string) => {
    switch (p) {
      case 'A':
        return { NORD: 'VERT', SUD: 'VERT', EST: 'ROUGE', OUEST: 'ROUGE' };
      case 'A_ORANGE':
        return { NORD: 'ORANGE', SUD: 'ORANGE', EST: 'ROUGE', OUEST: 'ROUGE' };
      case 'B':
        return { NORD: 'ROUGE', SUD: 'ROUGE', EST: 'VERT', OUEST: 'VERT' };
      case 'B_ORANGE':
        return { NORD: 'ROUGE', SUD: 'ROUGE', EST: 'ORANGE', OUEST: 'ORANGE' };
      default:
        return { NORD: 'ORANGE', SUD: 'ORANGE', EST: 'ORANGE', OUEST: 'ORANGE' }; // Mode nuit clignotant
    }
  };

  const lightStates = getLightStatesFromPhase(phase);

  return (
    <div className="stats-card" style={{ gridColumn: 'span 2' }}>
      <span className="stats-label" style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
        {Icons.trafficLight}
        <span>Phase Active : {phase}</span>
      </span>
      <div className="phase-visualizer-grid">
        {(['NORD', 'SUD', 'EST', 'OUEST'] as const).map(dir => {
          const state = lightStates[dir];
          const ledClass = state === 'VERT' ? 'online' : state === 'ROUGE' ? 'error' : 'connecting';
          const labelColor = state === 'VERT' ? 'var(--color-green)' : state === 'ROUGE' ? 'var(--color-red)' : 'var(--color-orange)';
          
          return (
            <div key={dir} className="phase-visualizer-cell">
              <span className="phase-cell-dir">{dir}</span>
              <span className={`status-led ${ledClass}`} style={{ width: '8px', height: '8px', boxShadow: 'none' }} />
              <span className="phase-cell-state" style={{ color: labelColor }}>
                {state}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'live' | 'analyst'>('live');
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeScenario, setActiveScenario] = useState('SCENARIO_1');
  const [systemStatus, setSystemStatus] = useState('CONNECTING');
  
  // Real-time stats
  const [stats, setStats] = useState<SimulationStats>({
    vehicles: 0,
    timeStr: '00:00',
    fluidity: 100,
    phase: 'A',
    scenario: 'Normal',
    qTableSize: 0
  });

  // Logs list
  const [logs, setLogs] = useState<LogEntry[]>([]);
  
  // Q-table state
  const [qTable, setQTable] = useState<Record<string, [number, number]>>({});
  
  // History for LineChart
  const [history, setHistory] = useState<number[]>([]);

  // Time clock
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  // Segmented control and SUMO metrics state
  const [dataSource, setDataSource] = useState<'local' | 'sumo'>('local');
  const [sumoMetrics, setSumoMetrics] = useState({
    episodeRewards: [] as number[],
    episodeLosses: [] as number[],
    episodeEpsilons: [] as number[],
    stepQueues: [] as number[],
    stepAvgSpeeds: [] as number[],
    totalSwitches: 0,
    totalStays: 0,
    latestEpisode: 0,
    latestReward: 0,
    latestEpsilon: 1.0,
    latestAvgSpeed: 0,
    activeTLS: 'Non détecté',
    totalActions: 0
  });

  const fetchSumoMetrics = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/logs?limit=1000`);
      if (response.ok) {
        const dbLogs = await response.json();
        const chronLogs = [...dbLogs].reverse();
        
        let epRewards: number[] = [];
        let epEpsilons: number[] = [];
        let stQueues: number[] = [];
        let stSpeeds: number[] = [];
        
        let switches = 0;
        let stays = 0;
        let lastEp = 0;
        let lastRew = 0;
        let lastEps = 1.0;
        let lastSpeed = 0;
        let tlsId = 'Non détecté';

        chronLogs.forEach((log: any) => {
          if (log.scenario !== 'DQN SUMO Thiès') return;

          if (log.type_action === 'TRAFFIC_LIGHT') {
            if (log.action.includes('Initialisation SUMO avec le feu')) {
              const tlsMatch = log.action.match(/le feu\s+([a-zA-Z0-9_#.-]+)/);
              if (tlsMatch) tlsId = tlsMatch[1];
            }
            if (log.action.includes('Decision SWITCH')) {
              switches++;
            }
            if (log.action.includes('Decision STAY')) {
              stays++;
            }
          }
          
          if (log.type_action === 'EPISODE_METRICS') {
            const match = log.action.match(/Episode:\s*(\d+),\s*Reward:\s*(-?[\d.]+),\s*Epsilon:\s*([\d.]+)/);
            if (match) {
              const ep = parseInt(match[1]);
              const rew = parseFloat(match[2]);
              const eps = parseFloat(match[3]);
              epRewards.push(rew);
              epEpsilons.push(eps);
              lastEp = ep;
              lastRew = rew;
              lastEps = eps;
            }
          }

          if (log.type_action === 'STEP_METRICS') {
            const match = log.action.match(/Queues:\s*N=(\d+),\s*S=(\d+),\s*E=(\d+),\s*O=(\d+),\s*AvgSpeed=([\d.]+)/);
            if (match) {
              const n = parseInt(match[1]);
              const s = parseInt(match[2]);
              const e = parseInt(match[3]);
              const o = parseInt(match[4]);
              const speed = parseFloat(match[5]);
              stQueues.push(n + s + e + o);
              stSpeeds.push(speed);
              lastSpeed = speed;
            }
          }
        });

        const totalStepsCount = chronLogs.filter((l: any) => l.scenario === 'DQN SUMO Thiès' && l.type_action === 'STEP_METRICS').length;
        if (stays === 0 && totalStepsCount > 0) {
          stays = Math.max(0, totalStepsCount - switches);
        }

        setSumoMetrics({
          episodeRewards: epRewards,
          episodeLosses: [],
          episodeEpsilons: epEpsilons,
          stepQueues: stQueues.slice(-50),
          stepAvgSpeeds: stSpeeds.slice(-50),
          totalSwitches: switches,
          totalStays: stays,
          latestEpisode: lastEp,
          latestReward: lastRew,
          latestEpsilon: lastEps,
          latestAvgSpeed: lastSpeed,
          activeTLS: tlsId,
          totalActions: totalStepsCount
        });
      }
    } catch (e) {
      console.error("Error fetching SUMO metrics:", e);
    }
  };

  // Instantiate simulation engine
  const engine = useMemo(() => {
    return new SimulationEngine(
      BACKEND_URL,
      (newLog) => {
        setLogs(prev => [newLog, ...prev].slice(0, 150)); // Limit to latest 150 logs in state
      },
      (newStats) => {
        setStats(newStats);
      }
    );
  }, []);

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Periodic Q-table updates and history tracking
  useEffect(() => {
    // Check backend connection status
    const checkConnection = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/logs?limit=1`);
        if (response.ok) {
          setSystemStatus('ONLINE');
        } else {
          setSystemStatus('ERROR');
        }
      } catch (e) {
        setSystemStatus('OFFLINE');
      }
    };

    checkConnection();
    const connInterval = setInterval(checkConnection, 5000);

    const updateInterval = setInterval(() => {
      if (!engine.isPaused) {
        // Recalculate Q-values using the latest neural network weights
        engine.rlAgent.refreshQTableCache();
        
        // Sync local Q-table state
        setQTable({ ...engine.rlAgent.qTable });
        
        // Append history entry
        const size = Object.keys(engine.rlAgent.qTable).length;
        setHistory(prev => {
          const next = [...prev, size];
          return next.slice(-40); // keep last 40 entries
        });
      }
    }, 2000);

    return () => {
      clearInterval(connInterval);
      clearInterval(updateInterval);
    };
  }, [engine]);

  // Load initial Q-Table once
  useEffect(() => {
    const loadInit = async () => {
      await engine.rlAgent.loadQTable();
      setQTable({ ...engine.rlAgent.qTable });
      const size = Object.keys(engine.rlAgent.qTable).length;
      setHistory([size]);
    };
    loadInit();
  }, [engine]);

  // Fetch SUMO metrics periodically
  useEffect(() => {
    fetchSumoMetrics();
    const interval = setInterval(fetchSumoMetrics, 3000);
    return () => clearInterval(interval);
  }, [systemStatus]);

  // Controls handlers
  const handlePlayPause = () => {
    const nextState = !isPlaying;
    setIsPlaying(nextState);
    engine.setPlay(nextState);
  };

  const handleReset = () => {
    engine.reset();
    setIsPlaying(false);
    setActiveScenario('SCENARIO_1');
    setLogs([]);
    setHistory([0]);
    setQTable({});
  };

  const handleScenarioChange = (scenarioCode: string) => {
    setActiveScenario(scenarioCode);
    engine.setScenario(scenarioCode);
  };

  const handleManualSwitch = () => {
    if (activeScenario === 'SCENARIO_4') {
      engine.manualChange();
    }
  };

  const handleClearQTable = async () => {
    if (window.confirm("Êtes-vous sûr de vouloir réinitialiser l'apprentissage (Q-Table) ?")) {
      await engine.rlAgent.clearQTable();
      setQTable({});
      setHistory([0]);
    }
  };

  const handleClearLogs = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/logs/clear`, {
        method: 'DELETE'
      });
      if (response.ok) {
        setLogs([]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Compute stats for Q-table distribution
  const qTableStats = useMemo(() => {
    let stays = 0;
    let switches = 0;
    Object.values(qTable).forEach(([stay, sw]) => {
      if (stay >= sw) stays++;
      else switches++;
    });
    return { stays, switches };
  }, [qTable]);

  // Determine density for each axis based on vehicle count
  const vehicleCounts = useMemo(() => {
    const counts = { NORD: 0, SUD: 0, EST: 0, OUEST: 0 };
    engine.vehicles.forEach(v => {
      if (v.isActive && !v.hasTurned) {
        counts[v.origin]++;
      }
    });
    return counts;
  }, [engine.vehicles, stats.vehicles]); // Re-compute when vehicles array updates

  const getStatusLedClass = () => {
    if (systemStatus === 'ONLINE') return 'online';
    if (systemStatus === 'ERROR' || systemStatus === 'OFFLINE') return 'error';
    return 'connecting';
  };

  return (
    <div className="app-container">
      {/* Top Header Panel */}
      <header className="app-header">
        <div className="system-status">
          <span className={`status-led ${getStatusLedClass()}`} />
          <span className="status-text">
            SYSTEM STATUS: {systemStatus}
          </span>
        </div>
        <h1 className="app-title">
          Quantum AI Traffic Hub V3.0
        </h1>
        <div className="app-clock">
          {currentTime}
        </div>
      </header>

      {/* Tabs Navigation */}
      <nav className="nav-tabs">
        <button
          onClick={() => setActiveTab('live')}
          className={`tab-button ${activeTab === 'live' ? 'active' : ''}`}
        >
          {Icons.lightning}
          <span>Télémétrie Live</span>
        </button>
        <button
          onClick={() => setActiveTab('analyst')}
          className={`tab-button ${activeTab === 'analyst' ? 'active' : ''}`}
        >
          {Icons.chart}
          <span>Centre d'Analyse</span>
        </button>
      </nav>

      {/* Main Layout Area */}
      <main className={`main-content ${activeTab === 'analyst' ? 'analyst-active' : ''}`}>
        
        {/* Left Control Sidebar */}
        <section className="panel sidebar">
          <div>
            <h3 className="panel-title" style={{ marginBottom: '12px' }}>Contrôles</h3>
            <div className="control-grid">
              <button
                onClick={handlePlayPause}
                className={`btn ${isPlaying ? 'btn-pause' : 'btn-simulate'}`}
              >
                {isPlaying ? Icons.pause : Icons.play}
                <span>{isPlaying ? 'PAUSE' : 'SIMULER'}</span>
              </button>
              <button
                onClick={handleReset}
                className="btn btn-reset"
              >
                {Icons.reset}
                <span>RESET</span>
              </button>
            </div>
          </div>

          <div>
            <h3 className="panel-title" style={{ marginBottom: '12px' }}>Scénarios de Trafic</h3>
            <div className="scenario-list">
              {[
                { code: 'SCENARIO_1', label: 'Trafic Normal', desc: 'Cycles de feux standard', icon: Icons.road },
                { code: 'SCENARIO_2', label: 'Heures de Pointe', desc: 'Cycles longs optimisés', icon: Icons.clock },
                { code: 'SCENARIO_3', label: 'Mode Nuit', desc: 'Feux orange clignotants', icon: Icons.moon },
                { code: 'SCENARIO_4', label: 'Mode Manuel', desc: 'Changement de phase manuel', icon: Icons.sliders },
                { code: 'SCENARIO_5', label: 'IA Optimisé (RL)', desc: 'Régulation intelligente par Q-learning', icon: Icons.cpu },
              ].map(sc => (
                <button
                  key={sc.code}
                  onClick={() => handleScenarioChange(sc.code)}
                  className={`scenario-btn ${activeScenario === sc.code ? 'active' : ''}`}
                >
                  <div className="scenario-btn-label" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {sc.icon}
                    <span>{sc.label}</span>
                  </div>
                  <div className="scenario-btn-desc">{sc.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {activeScenario === 'SCENARIO_4' && (
            <div className="animate-fadeIn">
              <h3 className="panel-title" style={{ marginBottom: '12px' }}>Actions Manuelles</h3>
              <button
                onClick={handleManualSwitch}
                className="btn btn-action"
              >
                {Icons.lightning}
                <span>CHANGER LA PHASE</span>
              </button>
            </div>
          )}
        </section>

        {/* Dynamic Tabs Content */}
        {activeTab === 'live' ? (
          <>
            {/* Center Area: Simulation Canvas */}
            <div className="sim-container">
              <TrafficCanvas engine={engine} />
              
              {/* Density Gauges */}
              <div className="gauge-panel">
                <span className="gauge-title">File d'attente :</span>
                {(Object.keys(vehicleCounts) as Array<keyof typeof vehicleCounts>).map(dir => (
                  <div key={dir} className="gauge-wrapper">
                    <span className="gauge-label">{dir}</span>
                    <div className="gauge-track">
                      <div
                        style={{ 
                          height: `${Math.min(100, vehicleCounts[dir] * 20)}%`,
                          backgroundColor: vehicleCounts[dir] === 0 
                            ? 'var(--color-green)' 
                            : vehicleCounts[dir] <= 2 
                              ? 'var(--color-orange)' 
                              : 'var(--color-red)',
                          boxShadow: vehicleCounts[dir] === 0 
                            ? '0 0 8px var(--color-green)' 
                            : vehicleCounts[dir] <= 2 
                              ? '0 0 8px var(--color-orange)' 
                              : '0 0 8px var(--color-red)'
                        }}
                        className="gauge-bar"
                      />
                    </div>
                    <span className="gauge-val">{vehicleCounts[dir]}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Column: Telemetry Dashboard & Logs */}
            <div className="stats-column">
              {/* Stats Card */}
              <div className="panel stats-grid">
                <div style={{ gridColumn: 'span 2', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '4px' }}>
                  <h3 className="panel-title">Tableau de Bord</h3>
                </div>
                
                {/* Rotating needle gauge chronometer */}
                <ChronometerDial timeStr={stats.timeStr} />

                <div className="stats-card">
                  <span className="stats-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {Icons.car}
                    <span>Véhicules Actifs</span>
                  </span>
                  <span className="stats-value">{stats.vehicles}</span>
                </div>
                <div className="stats-card">
                  <span className="stats-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {Icons.fluidity}
                    <span>Fluidité Trafic</span>
                  </span>
                  <span className="stats-value fluidity">{stats.fluidity}%</span>
                </div>

                {/* Custom active phase visualizer */}
                <TrafficPhaseVisualizer phase={stats.phase} />
              </div>

              {/* Real-time Logs Console */}
              <div className="panel logs-panel">
                <div className="panel-header">
                  <h3 className="panel-title">Console d'événements</h3>
                  <button
                    onClick={handleClearLogs}
                    className="btn-link"
                  >
                    Effacer DB
                  </button>
                </div>
                <div className="logs-console">
                  {logs.length === 0 ? (
                    <div className="console-empty">Simulation en attente...</div>
                  ) : (
                    logs.map((log, index) => {
                      let badgeClass = 'log-badge-system';
                      if (log.type_action === 'VEHICLE') badgeClass = 'log-badge-vehicle';
                      else if (log.type_action.includes('LIGHT') || log.type_action === 'TRAFFIC_LIGHT') badgeClass = 'log-badge-light';
                      else if (log.type_action === 'SCENARIO') badgeClass = 'log-badge-scenario';
                      else if (log.type_action === 'USER_INPUT') badgeClass = 'log-badge-user';

                      return (
                        <div key={index} className="log-entry">
                          <div className="log-meta">
                            <span className={`log-badge ${badgeClass}`}>{log.type_action}</span>
                            <span className="log-timestamp">{log.timestamp.split(' ')[1] || log.timestamp}</span>
                          </div>
                          <span className="log-text">{log.action}</span>
                          {log.id_voiture !== "N/A" && (
                            <span className="log-details">
                              Auto #{log.id_voiture} • Vitesse: {log.vitesse} px/f • Pos: ({log.position_x}, {log.position_y})
                            </span>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </div>
          </>
        ) : (
          /* Tab 2 (CENTRE D'ANALYSE) takes remaining 3 columns out of 4 */
          <div className="analyst-content">
            {/* Toggler Bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', paddingBottom: '12px', borderBottom: '1px solid var(--border-color)' }}>
              <div>
                <h4 className="panel-title" style={{ margin: 0, fontSize: '15px' }}>Centre d'Analyse Cognitive</h4>
                <p style={{ fontSize: '10px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>Analyse des performances de l'IA de régulation du trafic</p>
              </div>
              <div style={{ display: 'flex', backgroundColor: 'var(--bg-input)', padding: '2px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                <button 
                  onClick={() => setDataSource('local')}
                  style={{
                    border: 'none',
                    padding: '6px 12px',
                    fontSize: '11px',
                    fontWeight: 600,
                    borderRadius: '4px',
                    cursor: 'pointer',
                    backgroundColor: dataSource === 'local' ? 'var(--color-blue)' : 'transparent',
                    color: dataSource === 'local' ? 'white' : 'var(--text-secondary)',
                    transition: 'all 0.2s ease'
                  }}
                >
                  Simulateur Canvas
                </button>
                <button 
                  onClick={() => setDataSource('sumo')}
                  style={{
                    border: 'none',
                    padding: '6px 12px',
                    fontSize: '11px',
                    fontWeight: 600,
                    borderRadius: '4px',
                    cursor: 'pointer',
                    backgroundColor: dataSource === 'sumo' ? 'var(--color-blue)' : 'transparent',
                    color: dataSource === 'sumo' ? 'white' : 'var(--text-secondary)',
                    transition: 'all 0.2s ease'
                  }}
                >
                  Eclipse SUMO (Thiès)
                </button>
              </div>
            </div>

            {dataSource === 'local' ? (
              <>
                <div className="charts-grid">
                  <PieChart stays={qTableStats.stays} switches={qTableStats.switches} />
                  <LineChart history={history} />
                </div>

                {/* DQN Neural Network Training Telemetry */}
                <div className="panel dqn-telemetry-panel" style={{ marginBottom: '16px', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                  <div className="stats-card">
                    <span className="stats-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {Icons.lightning}
                      <span>Taux d'Exploration (Epsilon)</span>
                    </span>
                    <span className="stats-value" style={{ fontSize: '20px', fontFamily: 'var(--font-mono)' }}>
                      {(engine.rlAgent.epsilon * 100).toFixed(1)}%
                    </span>
                    <p className="admin-desc" style={{ margin: '4px 0 0 0', fontSize: '10px' }}>Décroissance de l'exploration aléatoire</p>
                  </div>

                  <div className="stats-card">
                    <span className="stats-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {Icons.cpu}
                      <span>Erreur Réseau (DQN Loss)</span>
                    </span>
                    <span className="stats-value" style={{ fontSize: '20px', fontFamily: 'var(--font-mono)', color: 'var(--color-orange)' }}>
                      {engine.rlAgent.lastLoss.toFixed(5)}
                    </span>
                    <p className="admin-desc" style={{ margin: '4px 0 0 0', fontSize: '10px' }}>Indicateur de convergence (MSE)</p>
                  </div>

                  <div className="stats-card">
                    <span className="stats-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {Icons.road}
                      <span>Buffer d'Expérience</span>
                    </span>
                    <span className="stats-value" style={{ fontSize: '20px', fontFamily: 'var(--font-mono)' }}>
                      {engine.rlAgent.getBufferSize()} / 2000
                    </span>
                    <p className="admin-desc" style={{ margin: '4px 0 0 0', fontSize: '10px' }}>Transitions collectées en mémoire</p>
                  </div>
                </div>

                <Heatmap qTable={qTable} />

                {/* DQN Model Administration Panel */}
                <div className="admin-panel">
                  <div>
                    <h4 className="admin-title">Base de Connaissance DQN</h4>
                    <p className="admin-desc">Gérez les poids du réseau de neurones persistés sur le serveur PostgreSQL.</p>
                  </div>
                  <div>
                    <button
                      onClick={handleClearQTable}
                      className="btn-danger"
                      style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                    >
                      {Icons.alert}
                      <span>RÉINITIALISER LES POIDS DQN</span>
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <>
                {/* SUMO TELEMETRY CARDS */}
                <div className="panel dqn-telemetry-panel" style={{ marginBottom: '16px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                  <div className="stats-card">
                    <span className="stats-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {Icons.cpu}
                      <span>Carrefour Cible SUMO</span>
                    </span>
                    <span className="stats-value" style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', wordBreak: 'break-all', display: 'block', marginTop: '6px', color: 'var(--color-blue)' }}>
                      {sumoMetrics.activeTLS.length > 25 ? `${sumoMetrics.activeTLS.substring(0, 22)}...` : sumoMetrics.activeTLS}
                    </span>
                    <p className="admin-desc" style={{ margin: '4px 0 0 0', fontSize: '10px' }}>ID de l'intersection à Thiès</p>
                  </div>

                  <div className="stats-card">
                    <span className="stats-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {Icons.clock}
                      <span>Dernier Épisode</span>
                    </span>
                    <span className="stats-value" style={{ fontSize: '20px', fontFamily: 'var(--font-mono)' }}>
                      {sumoMetrics.latestEpisode} / 10
                    </span>
                    <p className="admin-desc" style={{ margin: '4px 0 0 0', fontSize: '10px' }}>Épisodes de co-simulation complétés</p>
                  </div>

                  <div className="stats-card">
                    <span className="stats-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {Icons.lightning}
                      <span>Dernière Récompense</span>
                    </span>
                    <span className="stats-value" style={{ fontSize: '20px', fontFamily: 'var(--font-mono)', color: sumoMetrics.latestReward < -400 ? 'var(--color-red)' : 'var(--color-green)' }}>
                      {sumoMetrics.latestReward.toFixed(1)}
                    </span>
                    <p className="admin-desc" style={{ margin: '4px 0 0 0', fontSize: '10px' }}>Performance cumulée du DQN</p>
                  </div>

                  <div className="stats-card">
                    <span className="stats-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {Icons.car}
                      <span>Vitesse Moyenne</span>
                    </span>
                    <span className="stats-value" style={{ fontSize: '20px', fontFamily: 'var(--font-mono)', color: 'var(--color-orange)' }}>
                      {sumoMetrics.latestAvgSpeed.toFixed(1)} km/h
                    </span>
                    <p className="admin-desc" style={{ margin: '4px 0 0 0', fontSize: '10px' }}>Véhicules sur les voies contrôlées</p>
                  </div>
                </div>

                {/* SUMO CHARTS GRID */}
                <div className="charts-grid" style={{ marginBottom: '16px' }}>
                  <PieChart stays={sumoMetrics.totalStays} switches={sumoMetrics.totalSwitches} />
                  <LineChart 
                    history={sumoMetrics.episodeRewards.length > 1 ? sumoMetrics.episodeRewards : [0, 0]} 
                    title="Convergence DQN (SUMO)" 
                    subtitle="Évolution des récompenses par épisode" 
                    unit="Score" 
                    color="#10b981" 
                  />
                </div>

                <div className="charts-grid" style={{ marginBottom: '16px' }}>
                  <LineChart 
                    history={sumoMetrics.stepQueues.length > 1 ? sumoMetrics.stepQueues : [0, 0]} 
                    title="Densité des Files d'Attente SUMO" 
                    subtitle="Nombre cumulé de véhicules arrêtés" 
                    unit="Véhs" 
                    color="#ef4444" 
                  />
                  <LineChart 
                    history={sumoMetrics.stepAvgSpeeds.length > 1 ? sumoMetrics.stepAvgSpeeds : [0, 0]} 
                    title="Vélocité du Trafic (SUMO)" 
                    subtitle="Vitesse moyenne sur les voies d'entrée" 
                    unit="km/h" 
                    color="#f59e0b" 
                  />
                </div>

                {/* SUMO EVENT FEED */}
                <div className="panel logs-panel" style={{ height: '300px' }}>
                  <h3 className="panel-title" style={{ marginBottom: '10px' }}>Flux d'Événements Eclipse SUMO (Thiès, Sénégal)</h3>
                  <div className="logs-console" style={{ height: '240px' }}>
                    {logs.filter(l => l.scenario === "DQN SUMO Thiès").length === 0 ? (
                      <div className="console-empty">Aucun événement de simulation SUMO détecté. Lancez le script d'entraînement en arrière-plan.</div>
                    ) : (
                      logs.filter(l => l.scenario === "DQN SUMO Thiès").slice(0, 50).map((log, index) => {
                        let badgeClass = 'log-badge-light';
                        if (log.type_action === 'EPISODE_METRICS') badgeClass = 'log-badge-scenario';
                        else if (log.type_action === 'STEP_METRICS') badgeClass = 'log-badge-vehicle';

                        return (
                          <div key={index} className="log-entry">
                            <div className="log-meta">
                              <span className={`log-badge ${badgeClass}`}>{log.type_action}</span>
                              <span className="log-timestamp">{log.timestamp.split(' ')[1] || log.timestamp}</span>
                            </div>
                            <span className="log-text" style={{ color: 'white' }}>{log.action}</span>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
