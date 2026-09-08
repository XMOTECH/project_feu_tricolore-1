"""Script de diagnostic approfondi pour comparer le comportement de Fixe, DQN et MP sur 3600s.

Mesure pour chaque contrôleur sur la graine 7 (3600s) :
1. Nombre total de changements de phase (switches)
2. Temps total passé dans chaque phase verte (0, 1, 2, 3)
3. Nombre de véhicules insérés, terminés et restés bloqués
4. Métriques tripinfo (timeLoss, waitingTime, duration, vitesse)
"""

import os
import sys
import xml.etree.ElementTree as ET
import numpy as np
import traci

from . import config as C
from .adaptivity import phase_topology, grouped_queues, queue_per_phase
from .dqn import DQNAgent
from .env import SumoEnv
from .evaluate import parse_tripinfo
from .max_pressure import select_max_pressure_action, get_link_level_topology


def run_diagnose_dqn(model_path, seed=7, episode_len=3600):
    tri = os.path.join(C.OUTPUT_DIR, f"tripinfo_diag_dqn_{seed}.xml")
    env = SumoEnv(episode_len=episode_len, tripinfo_path=tri, label=f"diag_dqn_{seed}")
    state = env.reset(seed=seed)
    agent = DQNAgent(env.state_dim, env.num_actions)
    agent.load(model_path)
    
    phase_times = [0.0] * env.num_actions
    switches = 0
    prev_phase = env.signal.cur
    done = False
    
    while not done:
        action = agent.act(state, env.action_mask(), greedy=True)
        cur_p = env.signal.cur
        phase_times[cur_p] += C.DELTA_TIME
        if action != prev_phase and env.signal.can_switch():
            switches += 1
            prev_phase = action
        state, _, done, _ = env.step(action)
        
    env.close()
    info = parse_tripinfo(tri)
    return {
        "ctrl": "dqn",
        "switches": switches,
        "phase_times": phase_times,
        "tripinfo": info,
    }


def run_diagnose_mp(seed=7, episode_len=3600, delta=2.0, mode="hybrid"):
    tri = os.path.join(C.OUTPUT_DIR, f"tripinfo_diag_mp_{seed}.xml")
    env = SumoEnv(episode_len=episode_len, tripinfo_path=tri, label=f"diag_mp_{seed}")
    env.reset(seed=seed)
    
    green_states, controlled_links = get_link_level_topology(env.signal.id)
    phase_times = [0.0] * len(green_states)
    switches = 0
    prev_phase = env.signal.cur
    done = False
    
    while not done:
        valid = env.signal.valid_actions()
        action = select_max_pressure_action(env.signal, green_states, controlled_links, valid, delta=delta, mode=mode)
        cur_p = env.signal.cur
        phase_times[cur_p] += C.DELTA_TIME
        if action != prev_phase and env.signal.can_switch():
            switches += 1
            prev_phase = action
        state, _, done, _ = env.step(action)
        
    env.close()
    info = parse_tripinfo(tri)
    return {
        "ctrl": "mp",
        "switches": switches,
        "phase_times": phase_times,
        "tripinfo": info,
        "green_states": green_states,
    }


def run_diagnose_fixe(seed=7, episode_len=3600):
    import sumolib
    tri = os.path.join(C.OUTPUT_DIR, f"tripinfo_diag_fixe_{seed}.xml")
    env = SumoEnv(episode_len=episode_len, tripinfo_path=tri, label=f"diag_fixe_{seed}")
    env._write_demand(seed)
    
    cmd = [
        sumolib.checkBinary("sumo"), "-c", C.CONFIG_PATH,
        "--step-length", str(C.STEP_LENGTH), "--seed", str(seed),
        "--no-warnings", "true", "--no-step-log", "true",
        "--time-to-teleport", "-1", "--tripinfo-output", tri,
    ]
    traci.start(cmd, label=f"diag_fixe_{seed}")
    tls = C.TLS_ID or traci.trafficlight.getIDList()[0]
    logic = traci.trafficlight.getAllProgramLogics(tls)[0]
    green_states = [
        p.state for p in logic.phases
        if "y" not in p.state.lower() and "g" in p.state.lower()
    ]
    index_of = {st: i for i, st in enumerate(green_states)}
    
    phase_times = [0.0] * len(green_states)
    switches = 0
    cur = None
    t = 0.0
    
    while t < episode_len and traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        t += C.STEP_LENGTH
        state = traci.trafficlight.getRedYellowGreenState(tls)
        idx = index_of.get(state)
        if idx is not None:
            phase_times[idx] += C.STEP_LENGTH
            if cur is not None and idx != cur:
                switches += 1
            cur = idx
            
    traci.close()
    info = parse_tripinfo(tri)
    return {
        "ctrl": "fixe",
        "switches": switches,
        "phase_times": phase_times,
        "tripinfo": info,
    }


def main():
    seed = 7
    ep_len = 3600
    model_path = os.path.join(C.MODELS_DIR if hasattr(C, "MODELS_DIR") else "models", "dqn_150ep_eval.pt")
    if not os.path.exists(model_path):
        model_path = os.path.join(C.OUTPUT_DIR, "dqn_best.pt")
        
    print(f"\n=======================================================")
    print(f"  DIAGNOSTIC COMPLET (Graine {seed}, Durée {ep_len}s)")
    print(f"=======================================================\n")
    
    print("1. Analyse du contrôleur FIXE...")
    res_fixe = run_diagnose_fixe(seed, ep_len)
    
    print("2. Analyse du contrôleur DQN...")
    res_dqn = run_diagnose_dqn(model_path, seed, ep_len)
    
    print("3. Analyse du contrôleur MAX-PRESSURE (actuel)...")
    res_mp = run_diagnose_mp(seed, ep_len, delta=2.0, mode="hybrid")
    
    results = [res_fixe, res_dqn, res_mp]
    
    print("\n" + "=" * 80)
    print(f"{'Contrôleur':<12}{'Switches':<10}{'Véhicules (n)':<15}{'timeLoss (s)':<15}{'waiting (s)':<15}")
    print("-" * 80)
    for r in results:
        info = r["tripinfo"]
        print(f"{r['ctrl']:<12}{r['switches']:<10}{info['n']:<15}{info['timeLoss']:<15.1f}{info['waitingTime']:<15.1f}")
        
    print("\n" + "=" * 80)
    print("RÉPARTITION DU TEMPS PAR PHASE VERTE (en secondes et %) :")
    print("-" * 80)
    for r in results:
        pt = r["phase_times"]
        tot = max(1.0, sum(pt))
        pt_str = " | ".join([f"Ph{i}: {t:5.0f}s ({t/tot*100:4.1f}%)" for i, t in enumerate(pt)])
        print(f"{r['ctrl']:<8} -> {pt_str}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
