"""Démonstration visuelle : SUMO-GUI piloté par le régulateur DQN.

Ouvre sumo-gui et laisse l'agent entraîné commander le carrefour en temps réel,
avec une télémétrie imprimée en console. Le même script permet de rejouer le
contrôleur fixe ou actionné pour comparer à l'œil.

    py -3.14 -m rl.demo                      # DQN, graine 7
    py -3.14 -m rl.demo --controller fixe    # baseline statique
    py -3.14 -m rl.demo --controller actue   # baseline actionnée
    py -3.14 -m rl.demo --seed 42 --delay 150

Contrôles utiles dans la fenêtre SUMO :
    Play/Pause (barre d'outils), curseur "Delay (ms)" pour ralentir,
    clic droit sur le carrefour > "Show Phase" pour suivre les phases.
"""

import argparse
import os
import time

import traci

from . import config as C
from .dqn import DQNAgent
from .env import SumoEnv


def run_dqn(args):
    """Le DQN prend la main sur le feu, phase par phase."""
    env = SumoEnv(
        use_gui=True, episode_len=args.episode_len,
        label="demo", demand_scale=args.scale,
    )
    state = env.reset(seed=args.seed)

    agent = DQNAgent(env.state_dim, env.num_actions)
    agent.load(args.model)
    print(f"Modèle chargé : {args.model}")
    print(f"feu {env.signal.id} — {env.signal.num_green} phases vertes\n")
    print(f"{'t (s)':>7}{'phase':>7}{'file':>7}{'attente (s)':>13}"
          f"{'v (km/h)':>11}{'chgts':>7}")
    print("-" * 52)

    done, last_print = False, 0.0
    while not done:
        action = agent.act(state, env.action_mask(), greedy=True)  # epsilon = 0
        state, _, done, _ = env.step(action)

        if env.sim_time - last_print >= args.report_every:
            last_print = env.sim_time
            m = env.metrics
            print(f"{env.sim_time:7.0f}{env.signal.cur:7d}"
                  f"{m['queue'][-1]:7.0f}{m['wait'][-1]:13.0f}"
                  f"{m['speed'][-1]:11.1f}{m['switches']:7d}")

    summary = env.episode_summary()
    env.close()
    return summary


def run_baseline(args):
    """Le feu reste géré par SUMO (programme fixe ou actionné)."""
    import sumolib

    cfg = C.CONFIG_ACTUATED if args.controller == "actue" else C.CONFIG_PATH
    if args.controller == "actue" and not os.path.exists(cfg):
        raise FileNotFoundError(f"{cfg} manquant — générer osm.net.actuated.xml.gz.")

    # La démo doit voir exactement la même demande que le DQN.
    env = SumoEnv(episode_len=args.episode_len, label="demo",
                  demand_scale=args.scale)
    env._write_demand(args.seed)

    cmd = [
        sumolib.checkBinary("sumo-gui"), "-c", cfg,
        "--step-length", str(C.STEP_LENGTH), "--seed", str(args.seed),
        "--no-warnings", "true", "--no-step-log", "true",
        "--time-to-teleport", "-1", "--waiting-time-memory", "10000",
        "--start", "--quit-on-end",
    ]
    traci.start(cmd, label="demo")
    print(f"Contrôleur « {args.controller} » — le feu est géré par SUMO.\n")

    from .traffic_signal import TrafficSignal
    tls = C.TLS_ID or traci.trafficlight.getIDList()[0]
    lanes = list(dict.fromkeys(traci.trafficlight.getControlledLanes(tls)))

    print(f"{'t (s)':>7}{'file':>7}{'attente (s)':>13}{'v (km/h)':>11}")
    print("-" * 38)

    t, last_print = 0.0, 0.0
    queues, waits, speeds = [], [], []
    while t < args.episode_len and traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        t += C.STEP_LENGTH

        if t - last_print >= args.report_every:
            last_print = t
            q = sum(traci.lane.getLastStepHaltingNumber(l) for l in lanes)
            w = sum(
                traci.vehicle.getAccumulatedWaitingTime(v)
                for l in lanes for v in traci.lane.getLastStepVehicleIDs(l)
            )
            v = sum(traci.lane.getLastStepMeanSpeed(l) for l in lanes) / len(lanes) * 3.6
            queues.append(q); waits.append(w); speeds.append(v)
            print(f"{t:7.0f}{q:7.0f}{w:13.0f}{v:11.1f}")

    traci.close()
    n = max(1, len(queues))
    return {
        "mean_queue": sum(queues) / n, "mean_wait": sum(waits) / n,
        "mean_speed": sum(speeds) / n, "switches": 0, "decisions": n,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--controller", choices=["dqn", "fixe", "actue"], default="dqn")
    ap.add_argument("--model", type=str,
                    default=os.path.join(C.OUTPUT_DIR, "dqn_best.pt"))
    ap.add_argument("--seed", type=int, default=7,
                    help="graine d'évaluation (7, 13, 21, 42, 77 = jamais vues)")
    ap.add_argument("--episode-len", type=int, default=1800,
                    help="secondes simulées (1800 = 30 min, assez pour une démo)")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="multiplicateur de demande (>1 = plus congestionné)")
    ap.add_argument("--report-every", type=int, default=60,
                    help="intervalle d'affichage de la télémétrie, en s simulées")
    args = ap.parse_args()

    if args.controller == "dqn" and not os.path.exists(args.model):
        raise SystemExit(f"Modèle introuvable : {args.model}\n"
                         "Lancer d'abord : py -3.14 -m rl.train")

    t0 = time.time()
    s = (run_dqn(args) if args.controller == "dqn" else run_baseline(args))

    print("\n" + "=" * 52)
    print(f"Contrôleur      : {args.controller}")
    print(f"File moyenne    : {s['mean_queue']:.2f} véhicules")
    print(f"Attente moyenne : {s['mean_wait']:.1f} s")
    print(f"Vitesse moyenne : {s['mean_speed']:.1f} km/h")
    if s["switches"]:
        print(f"Changements     : {s['switches']}")
    print(f"Temps réel      : {time.time() - t0:.0f} s")
    print("=" * 52)


if __name__ == "__main__":
    main()
