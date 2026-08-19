import { DeepQLearningAgent } from '../ai/DeepQLearningAgent';
import type { Direction, Vehicle, VehicleType, TurnIntention, TrafficLight, LightState, Phase, SimulationStats, LogEntry } from './types';

export const DIRECTIONS = {
  EST: { spawn_x: -600, spawn_y: -35, heading: 0, lane_offset: -35, oncoming: "OUEST" as Direction },
  OUEST: { spawn_x: 600, spawn_y: 35, heading: 180, lane_offset: 35, oncoming: "EST" as Direction },
  NORD: { spawn_x: 35, spawn_y: -600, heading: 90, lane_offset: 35, oncoming: "SUD" as Direction },
  SUD: { spawn_x: -35, spawn_y: 600, heading: 270, lane_offset: -35, oncoming: "NORD" as Direction }
} as const;

export const STOP_POSITIONS = {
  EST: -135,
  OUEST: 135,
  NORD: -135,
  SUD: 135
} as const;

export const PHASES: Record<Phase, Record<Direction, LightState>> = {
  A: { NORD: "VERT", SUD: "VERT", EST: "ROUGE", OUEST: "ROUGE" },
  A_ORANGE: { NORD: "ORANGE", SUD: "ORANGE", EST: "ROUGE", OUEST: "ROUGE" },
  B: { NORD: "ROUGE", SUD: "ROUGE", EST: "VERT", OUEST: "VERT" },
  B_ORANGE: { NORD: "ROUGE", SUD: "ROUGE", EST: "ORANGE", OUEST: "ORANGE" }
};

export const PHASE_SEQUENCE: Phase[] = ["A", "A_ORANGE", "B", "B_ORANGE"];

export class SimulationEngine {
  public vehicles: Vehicle[] = [];
  public lights: Record<Direction, TrafficLight>;
  
  // Intersection state
  public currentPhase: Phase = "A";
  public phaseIndex = 0;
  public timer = 0;
  
  // Simulation control
  public isPaused = true;
  public isRunning = true;
  public nightMode = false;
  
  // Scenario & RL Agent
  public scenarioName = "SCENARIO_1"; // SCENARIO_1 to SCENARIO_5
  public rlAgent: DeepQLearningAgent;
  
  private nextVehicleId = 1;
  private spawnTimer = 0;
  private spawnInterval = 60; // frames between spawns
  private startTime: number;
  private totalPausedTime = 0;
  private pauseStart = 0;
  
  // RL state history for learning
  private lastStateKey: string | null = null;
  private lastStateVector: number[] | null = null;
  private lastAction: number | null = null;
  
  // Callbacks
  private onLog: (entry: LogEntry) => void;
  private onStats: (stats: SimulationStats) => void;
  private backendUrl: string;

  constructor(
    backendUrl = "http://localhost:8000",
    onLog: (entry: LogEntry) => void,
    onStats: (stats: SimulationStats) => void
  ) {
    this.backendUrl = backendUrl;
    this.onLog = onLog;
    this.onStats = onStats;
    this.startTime = Date.now();
    this.pauseStart = Date.now();
    
    // Initialize traffic lights
    this.lights = {
      EST: { id: "EST", state: "ROUGE", x: -100, y: -100 },
      OUEST: { id: "OUEST", state: "ROUGE", x: 100, y: 100 },
      NORD: { id: "NORD", state: "ROUGE", x: 100, y: -100 },
      SUD: { id: "SUD", state: "ROUGE", x: -100, y: 100 }
    };
    
    this.rlAgent = new DeepQLearningAgent([0, 1], backendUrl);
    this._applyPhase();
    
    // Synchronize weights on startup
    this.rlAgent.loadQTable();
    
    // Set up periodic sync for Q-table updates
    setInterval(() => {
      if (!this.isPaused && this.scenarioName === "SCENARIO_5") {
        this.rlAgent.syncPendingUpdates();
      }
    }, 10000);
  }

  private _applyPhase() {
    const phaseStates = PHASES[this.currentPhase];
    for (const dir in this.lights) {
      const d = dir as Direction;
      this.lights[d].state = phaseStates[d];
    }
  }

  public setScenario(scenarioCode: string) {
    this.scenarioName = scenarioCode;
    const oldNight = this.nightMode;
    this.nightMode = (scenarioCode === "SCENARIO_3");
    
    if (this.nightMode !== oldNight) {
      // Toggle night mode on active vehicles
      this.vehicles.forEach(v => v.nightMode = this.nightMode);
    }
    
    if (scenarioCode !== "SCENARIO_5") {
      this.lastStateKey = null;
      this.lastStateVector = null;
      this.lastAction = null;
    }
    
    // Reset timer when changing scenario
    this.timer = 0;
    
    if (scenarioCode === "SCENARIO_3") {
      // Night mode starts with Orange
      for (const dir in this.lights) {
        this.lights[dir as Direction].state = "ORANGE";
      }
    } else {
      this._applyPhase();
    }
    
    this.logEvent("SCENARIO", `Changement vers ${this.getScenarioName()}`);
  }

  public getScenarioName(): string {
    switch (this.scenarioName) {
      case "SCENARIO_1": return "Normal";
      case "SCENARIO_2": return "Heure de Pointe";
      case "SCENARIO_3": return "Mode Nuit";
      case "SCENARIO_4": return "Manuel";
      case "SCENARIO_5": return "RL Optimisé";
      default: return "Inconnu";
    }
  }

  public logEvent(typeAction: string, action: string, vehicle?: Vehicle) {
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    
    const entry: LogEntry = {
      timestamp,
      type_action: typeAction,
      action: `${action} (timer: ${this.timer})`,
      etat_feu: this.currentPhase,
      scenario: this.getScenarioName(),
      id_voiture: vehicle ? String(vehicle.id) : "N/A",
      position_x: vehicle ? vehicle.x.toFixed(1) : "N/A",
      position_y: vehicle ? vehicle.y.toFixed(1) : "N/A",
      vitesse: vehicle ? vehicle.currentSpeed.toFixed(1) : "N/A"
    };

    // Trigger local callback for live dashboard log display
    this.onLog(entry);

    // Send asynchronously to backend
    fetch(`${this.backendUrl}/api/logs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(entry)
    }).catch(err => console.error("Error logging to backend:", err));
  }

  public setPlay(play: boolean) {
    if (play && this.isPaused) {
      this.isPaused = false;
      this.totalPausedTime += (Date.now() - this.pauseStart);
      this.logEvent("USER_INPUT", "Clic sur PLAY");
    } else if (!play && !this.isPaused) {
      this.isPaused = true;
      this.pauseStart = Date.now();
      this.logEvent("USER_INPUT", "Clic sur PAUSE");
    }
  }

  public reset() {
    this.vehicles = [];
    this.nextVehicleId = 1;
    this.currentPhase = "A";
    this.phaseIndex = 0;
    this.timer = 0;
    this._applyPhase();
    this.scenarioName = "SCENARIO_1";
    this.nightMode = false;
    this.isPaused = true;
    this.startTime = Date.now();
    this.totalPausedTime = 0;
    this.pauseStart = Date.now();
    this.lastStateKey = null;
    this.lastStateVector = null;
    this.lastAction = null;
    
    this.logEvent("SYSTEM", "Réinitialisation");
    this.triggerStatsUpdate();
  }

  public manualChange() {
    if (this.scenarioName === "SCENARIO_4") {
      this.timer = 0;
      this.phaseIndex = (this.phaseIndex + 1) % PHASE_SEQUENCE.length;
      this.currentPhase = PHASE_SEQUENCE[this.phaseIndex];
      this._applyPhase();
      this.logEvent("TRAFFIC_LIGHT", `Changement Manuel vers ${this.currentPhase}`);
    }
  }

  public spawnVehicle(direction?: Direction) {
    const dir = direction || (Object.keys(DIRECTIONS) as Direction[])[Math.floor(Math.random() * 4)];
    const config = DIRECTIONS[dir];
    
    const typeRoll = Math.random();
    let type: VehicleType = 'CAR';
    let lengthOffset = 22;
    let backOffset = 18;
    let maxSpeed = 4;
    let color = '';

    if (typeRoll < 0.7) {
      type = 'CAR';
      color = [
        "#e74c3c", "#3498db", "#2ecc71", "#ffffff", "#2c3e50", 
        "#95a5a6", "#9b59b6", "#e67e22", "#1abc9c", "#f1c40f"
      ][Math.floor(Math.random() * 10)];
    } else if (typeRoll < 0.8) {
      type = 'TAXI';
      color = "#fbc02d";
    } else {
      type = 'MINIBUS';
      maxSpeed = 3.5;
      lengthOffset = 30;
      backOffset = 28;
      color = [
        "#f57c00", "#7b1fa2", "#00796b", "#455a64", "#5d4037", 
        "#d32f2f", "#1976d2", "#388e3c"
      ][Math.floor(Math.random() * 8)];
    }

    const r = Math.random();
    let turnIntention: TurnIntention = 'STRAIGHT';
    if (r < 0.6) turnIntention = 'STRAIGHT';
    else if (r < 0.8) turnIntention = 'RIGHT';
    else turnIntention = 'LEFT';

    const newVehicle: Vehicle = {
      id: this.nextVehicleId++,
      origin: dir,
      currentDirection: dir,
      type,
      x: config.spawn_x,
      y: config.spawn_y,
      heading: config.heading,
      color,
      maxSpeed,
      currentSpeed: maxSpeed,
      isActive: true,
      hasTurned: false,
      isTurning: false,
      targetHeading: config.heading,
      turnIntention,
      isBraking: false,
      blinkState: false,
      blinkTimer: 0,
      blinkInterval: 12,
      nightMode: this.nightMode,
      width: 16,
      length: lengthOffset * 2,
      frontOffset: lengthOffset,
      backOffset: backOffset
    };

    this.vehicles.push(newVehicle);
    this.logEvent("VEHICLE", `Entrée véhicule ${newVehicle.id}`, newVehicle);
  }

  private autoSpawn() {
    this.spawnTimer++;
    if (this.spawnTimer >= this.spawnInterval) {
      this.spawnTimer = 0;
      this.spawnVehicle();
    }
  }

  private cleanupInactive() {
    this.vehicles = this.vehicles.filter(v => v.isActive);
  }

  public tick() {
    if (this.isPaused) return;

    this.autoSpawn();
    this.updateIntersection();
    this.updateVehicles();
    this.cleanupInactive();
    this.triggerStatsUpdate();
  }

  private updateIntersection() {
    if (this.scenarioName === "SCENARIO_5") {
      this.updateRLScenario();
    } else if (this.scenarioName === "SCENARIO_3") {
      // Night mode blinking
      this.timer++;
      if (this.timer >= 30) {
        this.timer = 0;
        for (const dir in this.lights) {
          const d = dir as Direction;
          this.lights[d].state = this.lights[d].state === "ORANGE" ? "ETEINT" : "ORANGE";
        }
      }
    } else {
      // Predefined static durations
      this.timer++;
      let limit = 100; // Normal
      if (this.scenarioName === "SCENARIO_2") {
        // Rush hour durations
        limit = (this.currentPhase === "A" || this.currentPhase === "B") ? 200 : 30;
      } else {
        // Normal durations
        limit = (this.currentPhase === "A" || this.currentPhase === "B") ? 100 : 40;
      }

      if (this.timer >= limit) {
        this.logEvent("TRAFFIC_LIGHT", `Changement Phase Statique vers ${PHASE_SEQUENCE[(this.phaseIndex + 1) % PHASE_SEQUENCE.length]}`);
        this.timer = 0;
        this.phaseIndex = (this.phaseIndex + 1) % PHASE_SEQUENCE.length;
        this.currentPhase = PHASE_SEQUENCE[this.phaseIndex];
        this._applyPhase();
      }
    }
  }

  private updateRLScenario() {
    // Phase orange : cycle automatique
    if (this.currentPhase.includes("_ORANGE")) {
      this.timer++;
      const limit = 40; // orange duration
      if (this.timer >= limit) {
        this.logEvent("TRAFFIC_LIGHT", `Changement Phase RL (Orange Fini) vers ${PHASE_SEQUENCE[(this.phaseIndex + 1) % PHASE_SEQUENCE.length]}`);
        this.timer = 0;
        this.phaseIndex = (this.phaseIndex + 1) % PHASE_SEQUENCE.length;
        this.currentPhase = PHASE_SEQUENCE[this.phaseIndex];
        this._applyPhase();
      }
      return;
    }

    // Get vehicle counts in queue
    const counts = this.getVehicleCounts();
    const stateVector = this.rlAgent.getStateVector(
      counts.NORD, counts.SUD, counts.EST, counts.OUEST,
      this.currentPhase, this.timer
    );
    const stateKey = this.rlAgent.getStateKey(
      counts.NORD, counts.SUD, counts.EST, counts.OUEST,
      this.currentPhase, this.timer
    );

    // Apply Deep Q-Learning step (Learn)
    if (this.lastStateVector !== null && this.lastAction !== null) {
      const vCount = this.vehicles.length;
      let reward = 5.0;
      if (vCount > 0) {
        const avgSpeedRatio = this.vehicles.reduce((sum, v) => sum + (v.currentSpeed / v.maxSpeed), 0) / vCount;
        const waitingPenalty = this.vehicles.filter(v => v.currentSpeed === 0).length;
        reward = (avgSpeedRatio * 10) - (waitingPenalty * 2);
      }
      // Apply penalty for switching phase to prevent rapid light toggling and stabilize queues
      if (this.lastAction === 1) {
        reward -= 15.0;
      }
      this.rlAgent.learn(this.lastStateVector, this.lastAction, reward, stateVector, this.lastStateKey || undefined);
    }

    // Decide Action
    const MIN_GREEN_TIME = 300; // 5 seconds minimum green time to stabilize traffic flow
    const MAX_GREEN_TIME = 600; // 10 seconds maximum green time
    let action = 0;
    if (this.timer < MIN_GREEN_TIME) {
      action = 0; // Force stay
    } else if (this.timer >= MAX_GREEN_TIME) {
      action = 1; // Force switch
    } else {
      action = this.rlAgent.chooseAction(stateVector);
    }

    this.lastStateVector = stateVector;
    this.lastStateKey = stateKey;
    this.lastAction = action;

    if (action === 1) {
      this.logEvent("TRAFFIC_LIGHT", `Changement Phase RL (Decision SWITCH) vers ${PHASE_SEQUENCE[(this.phaseIndex + 1) % PHASE_SEQUENCE.length]}`);
      this.timer = 0;
      this.phaseIndex = (this.phaseIndex + 1) % PHASE_SEQUENCE.length;
      this.currentPhase = PHASE_SEQUENCE[this.phaseIndex];
      this._applyPhase();
    } else {
      this.timer++;
    }
  }

  private getVehicleCounts() {
    const counts = { NORD: 0, SUD: 0, EST: 0, OUEST: 0 };
    for (const v of this.vehicles) {
      if (!v.isActive || v.hasTurned) continue;

      let dist = 999;
      if (v.origin === "EST") dist = STOP_POSITIONS.EST - v.x;
      else if (v.origin === "OUEST") dist = v.x - STOP_POSITIONS.OUEST;
      else if (v.origin === "NORD") dist = STOP_POSITIONS.NORD - v.y;
      else if (v.origin === "SUD") dist = v.y - STOP_POSITIONS.SUD;

      if (dist > -20 && dist < 200) {
        counts[v.origin]++;
      }
    }
    return counts;
  }

  private updateVehicles() {
    for (const v of this.vehicles) {
      if (!v.isActive) continue;

      const wasStopped = v.currentSpeed === 0;
      
      // Default movement behavior
      v.currentSpeed = v.maxSpeed;

      // Slow down inside intersection
      if (Math.abs(v.x) < 140 && Math.abs(v.y) < 140) {
        v.currentSpeed = v.maxSpeed * 0.6;
      }

      let stopCause: string | null = null;

      // Check Traffic Light
      if (!v.hasTurned) {
        const lightState = this.lights[v.origin].state;
        const lightPos = STOP_POSITIONS[v.origin];
        
        let stopMargin = 15;
        let dist = 9999;
        
        if (v.origin === "EST") dist = lightPos - (v.x + v.frontOffset);
        else if (v.origin === "OUEST") dist = (v.x - v.frontOffset) - lightPos;
        else if (v.origin === "NORD") dist = lightPos - (v.y + v.frontOffset);
        else if (v.origin === "SUD") dist = (v.y - v.frontOffset) - lightPos;

        if (dist >= -15) {
          if ((lightState === "ROUGE" || lightState === "ORANGE") && dist > 0 && dist < stopMargin) {
            v.currentSpeed = 0;
            stopCause = `Feu ${lightState}`;
          }
        }
      }

      // Check Yield / Left-turn priorities
      if (v.currentSpeed > 0) {
        const priorityCause = this.checkVehiclePriority(v);
        if (priorityCause) {
          v.currentSpeed = 0;
          stopCause = priorityCause;
        }
      }

      // Check Collision with Vehicle Ahead
      if (v.currentSpeed > 0) {
        const aheadCause = this.checkVehicleAhead(v);
        if (aheadCause) {
          v.currentSpeed = 0;
          stopCause = aheadCause;
        }
      }

      // Log movement change
      const isStopped = v.currentSpeed === 0;
      if (isStopped && !wasStopped) {
        this.logEvent("VEHICLE", `Véhicule ${v.id} Arrêté (${stopCause || "Obstacle/Priority"})`, v);
      } else if (wasStopped && !isStopped) {
        this.logEvent("VEHICLE", `Véhicule ${v.id} Redémarrage`, v);
      }

      // Move Vehicle
      this.moveVehicle(v);
    }
  }

  private checkVehiclePriority(v: Vehicle): string | null {
    if (!v.isActive || v.hasTurned || v.currentSpeed === 0) return null;

    if (v.turnIntention === "LEFT") {
      const oncomingDir = DIRECTIONS[v.origin].oncoming;
      
      for (const other of this.vehicles) {
        if (!other.isActive || other.id === v.id) continue;
        
        if (other.origin === oncomingDir) {
          if (other.turnIntention === "LEFT") continue;

          // Check if oncoming vehicle has already cleared intersection
          let passed = false;
          if (other.origin === "EST" && other.x > 30) passed = true;
          else if (other.origin === "OUEST" && other.x < -30) passed = true;
          else if (other.origin === "NORD" && other.y > 30) passed = true;
          else if (other.origin === "SUD" && other.y < -30) passed = true;
          if (passed) continue;

          // Check if oncoming light is RED or ORANGE (if so, they will stop)
          const oncomingLight = this.lights[other.origin].state;
          if (oncomingLight === "ROUGE" || oncomingLight === "ORANGE") {
            continue;
          }

          // Check if oncoming vehicle is stopped and has not entered the intersection yet
          let otherEntered = false;
          if (other.origin === "EST" && other.x > -120) otherEntered = true;
          else if (other.origin === "OUEST" && other.x < 120) otherEntered = true;
          else if (other.origin === "NORD" && other.y > -120) otherEntered = true;
          else if (other.origin === "SUD" && other.y < 120) otherEntered = true;

          if (other.currentSpeed === 0 && !otherEntered) {
            continue;
          }

          const otherDistSq = other.x * other.x + other.y * other.y;
          const myDistSq = v.x * v.x + v.y * v.y;

          // If we are already deep in the box, clear it (anti-blocking)
          if (myDistSq < 70 * 70) return null;

          // Wait if oncoming traffic is near the intersection
          if (otherDistSq < 250 * 250 && myDistSq < 160 * 160) {
            return `Priorité gauche (Véhicule ${other.id})`;
          }
        }
      }
    }
    return null;
  }

  private checkVehicleAhead(v: Vehicle): string | null {
    if (!v.isActive || v.currentSpeed === 0) return null;

    const radHeading = (v.heading * Math.PI) / 180;
    const sensorX = v.x + Math.cos(radHeading) * 30;
    const sensorY = v.y + Math.sin(radHeading) * 30;
    const safetyRadius = 22;

    for (const other of this.vehicles) {
      if (other.id === v.id || !other.isActive) continue;

      const dx = other.x - v.x;
      const dy = other.y - v.y;
      const dot = dx * Math.cos(radHeading) + dy * Math.sin(radHeading);
      
      // If behind us, ignore
      if (dot < 0) continue;

      // Close proximity sensor check
      const sensorDistSq = (other.x - sensorX) ** 2 + (other.y - sensorY) ** 2;
      if (sensorDistSq < safetyRadius * safetyRadius) {
        // Deadlock tie-breaker: if both vehicles are inside the intersection, the one with the higher ID proceeds
        const inBox = (x: number, y: number) => (x * x + y * y) < 110 * 110;
        if (inBox(v.x, v.y) && inBox(other.x, other.y)) {
          if (v.id > other.id) {
            continue; // Skip stopping, let this vehicle clear the box
          }
        }

        // If in center ("clear the box"), be more aggressive
        if (v.x * v.x + v.y * v.y < 80 * 80) {
          const latDist = Math.abs(-dx * Math.sin(radHeading) + dy * Math.cos(radHeading));
          if (latDist < 15) {
            return `Collisions proche Centre (Véhicule ${other.id})`;
          }
        } else {
          return `Collisions proche (Véhicule ${other.id})`;
        }
      }

      // Standard Queue alignment on same lane
      const minGap = 10;
      const stopDist = v.frontOffset + other.backOffset + minGap;
      const slowDist = stopDist + 30;

      if (other.currentDirection === v.currentDirection && dot < slowDist) {
        const latDist = Math.abs(-dx * Math.sin(radHeading) + dy * Math.cos(radHeading));
        if (latDist < 20) {
          v.currentSpeed = Math.min(v.currentSpeed, other.currentSpeed);
          if (dot < stopDist) {
            return `Suivi file (Véhicule ${other.id})`;
          }
        }
      }
    }
    return null;
  }

  private moveVehicle(v: Vehicle) {
    // Handle brake lights
    const currentlyStopping = v.currentSpeed === 0;
    if (currentlyStopping !== v.isBraking) {
      v.isBraking = currentlyStopping;
    }

    // Handle blinkers
    if (!v.hasTurned && v.turnIntention !== 'STRAIGHT') {
      v.blinkTimer++;
      if (v.blinkTimer >= v.blinkInterval) {
        v.blinkTimer = 0;
        v.blinkState = !v.blinkState;
      }
    } else {
      v.blinkState = false;
      v.blinkTimer = 0;
    }

    if (v.currentSpeed === 0) return;

    // Gradual Turn Logic
    if (!v.hasTurned && v.turnIntention !== 'STRAIGHT') {
      if (!v.isTurning) {
        let startTurn = false;
        
        if (v.origin === "EST") {
          if (v.turnIntention === "LEFT" && v.x >= -3) {
            startTurn = true; v.targetHeading = 90; v.currentDirection = "NORD";
          } else if (v.turnIntention === "RIGHT" && v.x >= -73) {
            startTurn = true; v.targetHeading = 270; v.currentDirection = "SUD";
          }
        } else if (v.origin === "OUEST") {
          if (v.turnIntention === "LEFT" && v.x <= 3) {
            startTurn = true; v.targetHeading = 270; v.currentDirection = "SUD";
          } else if (v.turnIntention === "RIGHT" && v.x <= 73) {
            startTurn = true; v.targetHeading = 90; v.currentDirection = "NORD";
          }
        } else if (v.origin === "NORD") {
          if (v.turnIntention === "LEFT" && v.y >= -3) {
            startTurn = true; v.targetHeading = 180; v.currentDirection = "OUEST";
          } else if (v.turnIntention === "RIGHT" && v.y >= -73) {
            startTurn = true; v.targetHeading = 0; v.currentDirection = "EST";
          }
        } else if (v.origin === "SUD") {
          if (v.turnIntention === "LEFT" && v.y <= 3) {
            startTurn = true; v.targetHeading = 0; v.currentDirection = "EST";
          } else if (v.turnIntention === "RIGHT" && v.y <= 73) {
            startTurn = true; v.targetHeading = 180; v.currentDirection = "OUEST";
          }
        }

        if (startTurn) {
          v.isTurning = true;
        }
      }

      if (v.isTurning) {
        const turnStep = 6 * (v.currentSpeed / v.maxSpeed);
        const diff = ((v.targetHeading - v.heading + 180) % 360 + 360) % 360 - 180;
        
        if (Math.abs(diff) <= turnStep) {
          v.heading = v.targetHeading;
          v.isTurning = false;
          v.hasTurned = true;
          // Align to center lane
          const offset = DIRECTIONS[v.currentDirection].lane_offset;
          if (v.currentDirection === "EST" || v.currentDirection === "OUEST") {
            v.y = offset;
          } else {
            v.x = offset;
          }
        } else {
          v.heading += diff > 0 ? turnStep : -turnStep;
        }
      }
    }

    // Apply movement vector
    const rad = (v.heading * Math.PI) / 180;
    v.x += Math.cos(rad) * v.currentSpeed;
    v.y += Math.sin(rad) * v.currentSpeed;

    // Mark as inactive if out of bounds
    if (Math.abs(v.x) > 650 || Math.abs(v.y) > 650) {
      v.isActive = false;
      this.logEvent("VEHICLE", `Sortie véhicule ${v.id}`, v);
    }
  }

  private triggerStatsUpdate() {
    let elapsed = 0;
    if (!this.isPaused) {
      elapsed = Date.now() - this.startTime - this.totalPausedTime;
    } else {
      elapsed = this.pauseStart - this.startTime - this.totalPausedTime;
    }

    const minutes = Math.floor(elapsed / 60000);
    const seconds = Math.floor((elapsed % 60000) / 1000);
    const timeStr = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

    const vCount = this.vehicles.length;
    let fluidity = 100;
    if (vCount > 0) {
      const sumRatio = this.vehicles.reduce((sum, v) => sum + (v.currentSpeed / v.maxSpeed), 0);
      fluidity = Math.round((sumRatio / vCount) * 100);
    }

    this.onStats({
      vehicles: vCount,
      timeStr,
      fluidity,
      phase: this.currentPhase,
      scenario: this.getScenarioName(),
      qTableSize: Object.keys(this.rlAgent.qTable).length
    });
  }
}
