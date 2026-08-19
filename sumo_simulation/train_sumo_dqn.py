import os
import sys
import math
import random
import time
import collections
import json
import urllib.request
from datetime import datetime

# Import SUMO libraries
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci
import sumolib
import numpy as np

# Import TensorBoard SummaryWriter
try:
    from torch.utils.tensorboard import SummaryWriter
    TENSORBOARD_AVAILABLE = True
except ImportError:
    TENSORBOARD_AVAILABLE = False

BACKEND_URL = "http://localhost:8000"

# --- 1. Pure NumPy DQN Model & Backpropagation ---
class NumPyMLP:
    def __init__(self, state_dim, action_dim, lr=0.005):
        self.lr = lr
        # He (Kaiming) Initialization
        self.w1 = np.random.randn(24, state_dim) * np.sqrt(2.0 / state_dim)
        self.b1 = np.zeros((24, 1))
        self.w2 = np.random.randn(24, 24) * np.sqrt(2.0 / 24)
        self.b2 = np.zeros((24, 1))
        self.w3 = np.random.randn(action_dim, 24) * np.sqrt(2.0 / 24)
        self.b3 = np.zeros((action_dim, 1))
        
    def forward(self, state):
        s = np.array(state).reshape(-1, 1)
        h1 = np.maximum(0, np.dot(self.w1, s) + self.b1) # ReLU
        h2 = np.maximum(0, np.dot(self.w2, h1) + self.b2) # ReLU
        q = np.dot(self.w3, h2) + self.b3 # Linear output
        return q.flatten(), h1, h2
        
    def train_step(self, state, action, target):
        s = np.array(state).reshape(-1, 1)
        q, h1, h2 = self.forward(s)
        
        # Loss derivative w.r.t output
        delta_out = np.zeros((len(q), 1))
        delta_out[action, 0] = q[action] - target
        
        loss = 0.5 * (q[action] - target) ** 2
        
        # Layer 3 Gradients
        dw3 = np.dot(delta_out, h2.T)
        db3 = delta_out
        
        # Layer 2 Gradients (Backprop through ReLU)
        d2 = np.dot(self.w3.T, delta_out) * (h2 > 0)
        dw2 = np.dot(d2, h1.T)
        db2 = d2
        
        # Layer 1 Gradients (Backprop through ReLU)
        d1 = np.dot(self.w2.T, d2) * (h1 > 0)
        dw1 = np.dot(d1, s.T)
        db1 = d1
        
        # Gradient clipping to stabilize learning (between -1.0 and 1.0)
        for g in [dw3, db3, dw2, db2, dw1, db1]:
            np.clip(g, -1.0, 1.0, out=g)
            
        # Update weights and biases
        self.w3 -= self.lr * dw3
        self.b3 -= self.lr * db3
        self.w2 -= self.lr * dw2
        self.b2 -= self.lr * db2
        self.w1 -= self.lr * dw1
        self.b1 -= self.lr * db1
        
        return loss

class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = collections.deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)

# --- 2. Environment Wrapper ---
class SUMOTrafficEnv:
    def __init__(self, config_path, tls_id=None, use_gui=True):
        self.config_path = config_path
        self.use_gui = use_gui
        self.sumo_binary = sumolib.checkBinary('sumo-gui' if use_gui else 'sumo')
        self.tls_id = tls_id
        
        # State and Action dimensions
        self.state_dim = 7
        self.action_dim = 2
        
        self.lane_groups = {}
        self.green_phases = []
        self.yellow_phases = {}
        self.current_green_idx = 0
        self.timer = 0
        self.min_green_time = 50  # 5 seconds minimum green time
        
    def log_to_backend(self, type_action, action_msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "timestamp": timestamp,
            "type_action": type_action,
            "action": action_msg,
            "etat_feu": str(self.current_green_idx),
            "scenario": "DQN SUMO Thiès",
            "id_voiture": "N/A",
            "position_x": "N/A",
            "position_y": "N/A",
            "vitesse": "N/A"
        }
        try:
            req = urllib.request.Request(
                f"{BACKEND_URL}/api/logs", 
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=1) as response:
                pass
        except Exception:
            pass  # Fail silently if backend is offline

    def start_sumo(self):
        traci.start([self.sumo_binary, "-c", self.config_path, "--tripinfo-output", "tripinfo.xml", "--start", "--quit-on-end"])
        
        # Auto-detect Traffic Light ID if not provided
        if not self.tls_id:
            tls_ids = traci.trafficlight.getIDList()
            if not tls_ids:
                raise Exception("No traffic lights found in SUMO network!")
            self.tls_id = tls_ids[0]
            print(f"Auto-detected traffic light ID: {self.tls_id}")
            
        self.log_to_backend("TRAFFIC_LIGHT", f"Initialisation SUMO avec le feu {self.tls_id}")
        
        # Group controlled lanes by incoming angles
        tls_lanes = list(set(traci.trafficlight.getControlledLanes(self.tls_id)))
        junction_pos = traci.junction.getPosition(self.tls_id)
        
        self.lane_groups = {"NORD": [], "SUD": [], "EST": [], "OUEST": []}
        for lane_id in tls_lanes:
            shape = traci.lane.getShape(lane_id)
            start_pt = shape[0]
            dx = junction_pos[0] - start_pt[0]
            dy = junction_pos[1] - start_pt[1]
            
            angle = math.degrees(math.atan2(dy, dx))
            if angle < 0:
                angle += 360
                
            if 45 <= angle < 135:
                self.lane_groups["SUD"].append(lane_id) # coming from South (moving North)
            elif 135 <= angle < 225:
                self.lane_groups["EST"].append(lane_id) # coming from East (moving West)
            elif 225 <= angle < 315:
                self.lane_groups["NORD"].append(lane_id) # coming from North (moving South)
            else:
                self.lane_groups["OUEST"].append(lane_id) # coming from West (moving East)
                
        print("Lanes grouped by direction:")
        for k, v in self.lane_groups.items():
            print(f"  {k}: {len(v)} lanes")
            
        # Analyze phases of the traffic light
        self.green_phases = []
        program = traci.trafficlight.getAllProgramLogics(self.tls_id)[0]
        for i, phase in enumerate(program.phases):
            state = phase.state.lower()
            if 'y' in state:
                pass
            elif 'g' in state:
                self.green_phases.append(i)
                
        # Associate each green phase with its following yellow phase
        for idx, green_idx in enumerate(self.green_phases):
            next_idx = (green_idx + 1) % len(program.phases)
            if 'y' in program.phases[next_idx].state.lower():
                self.yellow_phases[green_idx] = next_idx
            else:
                self.yellow_phases[green_idx] = green_idx
                
        print(f"Green phases found: {self.green_phases}")
        print(f"Yellow transitions: {self.yellow_phases}")
        self.current_green_idx = 0
        traci.trafficlight.setPhase(self.tls_id, self.green_phases[self.current_green_idx])
        traci.trafficlight.setPhaseDuration(self.tls_id, 3600)  # Lock duration so SUMO doesn't switch automatically

    def get_state(self):
        # Get halting vehicles in each direction
        n_count = sum(traci.lane.getLastStepHaltingNumber(l) for l in self.lane_groups["NORD"])
        s_count = sum(traci.lane.getLastStepHaltingNumber(l) for l in self.lane_groups["SUD"])
        e_count = sum(traci.lane.getLastStepHaltingNumber(l) for l in self.lane_groups["EST"])
        o_count = sum(traci.lane.getLastStepHaltingNumber(l) for l in self.lane_groups["OUEST"])
        
        phase_a = 1.0 if self.current_green_idx == 0 else 0.0
        phase_b = 1.0 if self.current_green_idx == 1 else 0.0
        norm_time = min(self.timer / 100.0, 1.0)
        
        return [n_count, s_count, e_count, o_count, phase_a, phase_b, norm_time]

    def reset(self):
        try:
            traci.close()
        except Exception:
            pass
        self.start_sumo()
        self.timer = 0
        return self.get_state()

    def step(self, action):
        reward = 0
        done = False
        
        # 1. Handle actions
        if action == 1 and self.timer >= self.min_green_time:
            # SWITCH phase
            green_idx = self.green_phases[self.current_green_idx]
            yellow_idx = self.yellow_phases[green_idx]
            
            # Transition with Yellow phase
            traci.trafficlight.setPhase(self.tls_id, yellow_idx)
            traci.trafficlight.setPhaseDuration(self.tls_id, 3600)
            self.log_to_backend("TRAFFIC_LIGHT", f"Changement de Phase (Decision SWITCH) vers Jaune {yellow_idx}")
            
            # Advance SUMO during yellow phase (4 seconds = 40 steps)
            for _ in range(40):
                traci.simulationStep()
                
            # Switch to new green phase
            self.current_green_idx = (self.current_green_idx + 1) % len(self.green_phases)
            new_green_idx = self.green_phases[self.current_green_idx]
            traci.trafficlight.setPhase(self.tls_id, new_green_idx)
            traci.trafficlight.setPhaseDuration(self.tls_id, 3600)
            self.log_to_backend("TRAFFIC_LIGHT", f"Phase Verte active: {new_green_idx}")
            
            self.timer = 0
            reward -= 15.0 # switch penalty
        else:
            # STAY phase - Advance simulation by 1 second (10 steps)
            for _ in range(10):
                traci.simulationStep()
            self.timer += 10
            
        # 2. Get new state and calculate reward
        state_after = self.get_state()
        tot_queue_after = sum(state_after[:4])
        
        # Base reward is the negative size of queues
        reward -= tot_queue_after
        
        # Calculate average speed of vehicles on controlled lanes in km/h
        all_lanes = []
        for l_list in self.lane_groups.values():
            all_lanes.extend(l_list)
        speeds = [traci.lane.getLastStepMeanSpeed(l) for l in all_lanes]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
        avg_speed_kmh = avg_speed * 3.6
        
        self.log_to_backend("STEP_METRICS", f"Queues: N={state_after[0]}, S={state_after[1]}, E={state_after[2]}, O={state_after[3]}, AvgSpeed={avg_speed_kmh:.2f}")
        
        # Check if simulation is finished (no more vehicles or max steps reached)
        if traci.simulation.getMinExpectedNumber() == 0 or traci.simulation.getTime() > 1000:
            done = True
            
        return state_after, reward, done, tot_queue_after, avg_speed_kmh

    def close(self):
        traci.close()

# --- 3. Training Loop ---
def train():
    # Find sumocfg file
    sim_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(sim_dir, "map.sumocfg")
    
    if not os.path.exists(config_path):
        print(f"Error: Could not find map.sumocfg in {sim_dir}!")
        print("Please run osmWebWizard.py, export Thiès, and copy files to this directory.")
        return
        
    runs_dir = os.path.join(sim_dir, "runs")
    writer = SummaryWriter(log_dir=runs_dir) if TENSORBOARD_AVAILABLE else None
    if writer:
        print(f"📈 TensorBoard Logging activé dans : {runs_dir}")
        
    env = SUMOTrafficEnv(config_path, use_gui=True)
    
    # Initialize NumPy DQN
    state_dim = env.state_dim
    action_dim = env.action_dim
    
    policy_net = NumPyMLP(state_dim, action_dim)
    target_net = NumPyMLP(state_dim, action_dim)
    
    memory = ReplayBuffer(2000)
    
    epsilon = 1.0
    epsilon_min = 0.05
    epsilon_decay = 0.99
    gamma = 0.95
    batch_size = 32
    tau = 0.05  # soft update factor
    
    num_episodes = 20
    
    for episode in range(num_episodes):
        state = env.reset()
        episode_reward = 0
        queues = []
        speeds = []
        losses = []
        
        print(f"\n--- Starting Episode {episode+1} ---")
        
        while True:
            # Epsilon-greedy action selection
            if random.random() < epsilon:
                action = random.randint(0, action_dim - 1)
            else:
                q_vals, _, _ = policy_net.forward(state)
                action = np.argmax(q_vals)
                    
            next_state, reward, done, queue_val, speed_val = env.step(action)
            episode_reward += reward
            queues.append(queue_val)
            speeds.append(speed_val)
            
            memory.push(state, action, reward, next_state, done)
            state = next_state
            
            # Optimization step
            if len(memory) >= batch_size:
                batch = memory.sample(batch_size)
                batch_loss = 0
                for s_b, a_b, r_b, ns_b, d_b in batch:
                    if d_b:
                        target = r_b
                    else:
                        target_q, _, _ = target_net.forward(ns_b)
                        target = r_b + gamma * np.max(target_q)
                    
                    loss_step = policy_net.train_step(s_b, a_b, target)
                    batch_loss += loss_step
                losses.append(batch_loss / batch_size)
                
                # Soft update target network weights
                target_net.w1 = tau * policy_net.w1 + (1 - tau) * target_net.w1
                target_net.b1 = tau * policy_net.b1 + (1 - tau) * target_net.b1
                target_net.w2 = tau * policy_net.w2 + (1 - tau) * target_net.w2
                target_net.b2 = tau * policy_net.b2 + (1 - tau) * target_net.b2
                target_net.w3 = tau * policy_net.w3 + (1 - tau) * target_net.w3
                target_net.b3 = tau * policy_net.b3 + (1 - tau) * target_net.b3
            
            if done:
                break
                
        epsilon = max(epsilon_min, epsilon * epsilon_decay)
        avg_queue = np.mean(queues) if queues else 0
        avg_speed = np.mean(speeds) if speeds else 0
        avg_loss = np.mean(losses) if losses else 0
        
        print(f"Episode {episode+1} Finished. Reward: {episode_reward:.2f}, Epsilon: {epsilon:.3f}, Speed: {avg_speed:.1f} km/h, Queue: {avg_queue:.1f}")
        env.log_to_backend("EPISODE_METRICS", f"Episode: {episode+1}, Reward: {episode_reward:.2f}, Epsilon: {epsilon:.3f}")
        
        if writer:
            writer.add_scalar("Performance/Reward", episode_reward, episode + 1)
            writer.add_scalar("Performance/Vitesse_Moyenne_kmh", avg_speed, episode + 1)
            writer.add_scalar("Performance/File_Moyenne", avg_queue, episode + 1)
            writer.add_scalar("DQN/Epsilon", epsilon, episode + 1)
            writer.add_scalar("DQN/Loss", avg_loss, episode + 1)
            writer.flush()
        
    if writer:
        writer.close()
    env.close()

if __name__ == "__main__":
    train()
