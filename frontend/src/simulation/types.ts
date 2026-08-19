export type Direction = 'EST' | 'OUEST' | 'NORD' | 'SUD';

export type VehicleType = 'CAR' | 'TAXI' | 'MINIBUS';

export type TurnIntention = 'STRAIGHT' | 'LEFT' | 'RIGHT';

export type LightState = 'ROUGE' | 'ORANGE' | 'VERT' | 'ETEINT';

export type Phase = 'A' | 'A_ORANGE' | 'B' | 'B_ORANGE';

export interface Vehicle {
  id: number;
  origin: Direction;
  currentDirection: Direction;
  type: VehicleType;
  x: number;
  y: number;
  heading: number;
  color: string;
  maxSpeed: number;
  currentSpeed: number;
  isActive: boolean;
  hasTurned: boolean;
  isTurning: boolean;
  targetHeading: number;
  turnIntention: TurnIntention;
  isBraking: boolean;
  blinkState: boolean;
  blinkTimer: number;
  blinkInterval: number;
  nightMode: boolean;
  width: number;
  length: number;
  frontOffset: number;
  backOffset: number;
}

export interface TrafficLight {
  id: Direction;
  state: LightState;
  x: number;
  y: number;
}

export interface SimulationStats {
  vehicles: number;
  timeStr: string;
  fluidity: number;
  phase: Phase;
  scenario: string;
  qTableSize: number;
}

export interface LogEntry {
  id?: number;
  timestamp: string;
  type_action: string;
  action: string;
  etat_feu: string;
  scenario: string;
  id_voiture: string;
  position_x: string;
  position_y: string;
  vitesse: string;
}
