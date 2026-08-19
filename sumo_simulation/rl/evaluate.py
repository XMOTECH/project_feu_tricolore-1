"""Compare le régulateur DQN à ses baselines.

C'est la partie qui transforme une démonstration en résultat : sans point de
comparaison, aucune affirmation d'efficacité n'est soutenable.

Trois contrôleurs, mêmes graines, même demande :
  fixe      — programme statique d'origine du réseau (27/6/6/6/27/6/6/6)
  actue     — feu actionné par détection de gap (baseline forte)
  dqn       — politique apprise, epsilon = 0

Métriques extraites de tripinfo.xml, agrégées sur SEED_EVAL :
timeLoss, waitingTime, duration, vitesse moyenne, débit.

    py -3.14 -m rl.evaluate --model outputs/dqn_best.pt
"""

import argparse
import os
import statistics
import xml.etree.ElementTree as ET

import traci
import traci.constants as tc

from . import config as C
from .dqn import DQNAgent
from .env import SumoEnv


def parse_tripinfo(path):
    """Agrège les métriques par véhicule d'un fichier tripinfo."""
    if not os.path.exists(path):
        return None
    trips = ET.parse(path).getroot().findall("tripinfo")
    if not trips:
        return None
    f = lambda k: [float(t.get(k)) for t in trips]  # noqa: E731
    return {
        "n": len(trips),
        "timeLoss": statistics.mean(f("timeLoss")),
        "waitingTime": statistics.mean(f("waitingTime")),
        "duration": statistics.mean(f("duration")),
        "speed": statistics.mean(
            float(t.get("routeLength")) / float(t.get("duration"))
            for t in trips if float(t.get("duration")) > 0
        ),
    }


def run_baseline(kind, seed, episode_len, out_dir):
    """Exécute un contrôleur non appris (feu géré par SUMO)."""
    tri = os.path.join(out_dir, f"tripinfo_{kind}_{seed}.xml")
    env = SumoEnv(episode_len=episode_len, tripinfo_path=tri, label=f"{kind}{seed}")
    env._write_demand(seed)

    import sumolib
    # Le réseau d'origine ne contient qu'un programme statique ; la baseline
    # actionnée utilise un réseau reconstruit par
    #   netconvert --tls.default-type actuated --tls.rebuild
    cfg = C.CONFIG_ACTUATED if kind == "actue" else C.CONFIG_PATH
    if kind == "actue" and not os.path.exists(cfg):
        raise FileNotFoundError(
            f"{cfg} manquant — générer d'abord osm.net.actuated.xml.gz."
        )
    cmd = [
        sumolib.checkBinary("sumo"), "-c", cfg,
        "--step-length", str(C.STEP_LENGTH), "--seed", str(seed),
        "--no-warnings", "true", "--no-step-log", "true",
        "--time-to-teleport", "-1", "--tripinfo-output", tri,
    ]

    traci.start(cmd, label=f"{kind}{seed}")
    if kind == "actue":
        # Garde-fou : si le feu n'est pas réellement actionné, la "baseline
        # forte" serait en fait le contrôleur fixe — un faux résultat.
        tls = C.TLS_ID or traci.trafficlight.getIDList()[0]
        types = {lg.type for lg in traci.trafficlight.getAllProgramLogics(tls)}
        if tc.TRAFFICLIGHT_TYPE_ACTUATED not in types:
            traci.close()
            raise RuntimeError(
                f"Le feu {tls} n'a aucun programme actionné (types={types})."
            )

    t = 0.0
    while t < episode_len and traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        t += C.STEP_LENGTH
    traci.close()
    return parse_tripinfo(tri)


def run_dqn(model_path, seed, episode_len, out_dir):
    tri = os.path.join(out_dir, f"tripinfo_dqn_{seed}.xml")
    env = SumoEnv(episode_len=episode_len, tripinfo_path=tri, label=f"dqn{seed}")
    state = env.reset(seed=seed)
    agent = DQNAgent(env.state_dim, env.num_actions)
    agent.load(model_path)

    done = False
    while not done:
        action = agent.act(state, env.action_mask(), greedy=True)  # epsilon = 0
        state, _, done, _ = env.step(action)
    env.close()
    return parse_tripinfo(tri)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=str,
                    default=os.path.join(C.OUTPUT_DIR, "dqn_best.pt"))
    ap.add_argument("--episode-len", type=int, default=C.EPISODE_LEN)
    ap.add_argument("--seeds", type=int, nargs="*", default=C.SEED_EVAL)
    ap.add_argument("--out", type=str, default=C.OUTPUT_DIR)
    ap.add_argument("--skip-dqn", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    controllers = ["fixe", "actue"]
    if not args.skip_dqn and os.path.exists(args.model):
        controllers.append("dqn")
    elif not args.skip_dqn:
        print(f"[!] Modèle introuvable ({args.model}) — baselines seules.")

    results = {c: [] for c in controllers}
    for seed in args.seeds:
        for c in controllers:
            m = (run_dqn(args.model, seed, args.episode_len, args.out)
                 if c == "dqn"
                 else run_baseline(c, seed, args.episode_len, args.out))
            if m:
                results[c].append(m)
                print(f"  {c:<6} seed={seed:<3} timeLoss={m['timeLoss']:6.1f}s "
                      f"wait={m['waitingTime']:6.1f}s n={m['n']}")

    def agg(rows, k):
        vals = [r[k] for r in rows]
        sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
        return statistics.mean(vals), sd

    print("\n" + "=" * 78)
    print(f"{'Contrôleur':<12}{'timeLoss (s)':>18}{'waiting (s)':>18}"
          f"{'durée (s)':>15}{'v (m/s)':>12}")
    print("-" * 78)
    base = None
    for c in controllers:
        if not results[c]:
            continue
        tl, tl_sd = agg(results[c], "timeLoss")
        wt, wt_sd = agg(results[c], "waitingTime")
        du, _ = agg(results[c], "duration")
        sp, _ = agg(results[c], "speed")
        if base is None:
            base = tl
        delta = f"  ({(tl - base) / base * 100:+.1f}%)" if base else ""
        print(f"{c:<12}{tl:9.1f} ± {tl_sd:<5.1f}{wt:9.1f} ± {wt_sd:<5.1f}"
              f"{du:15.1f}{sp:12.2f}{delta}")
    print("=" * 78)
    print(f"({len(args.seeds)} graines, épisodes de {args.episode_len} s, "
          "écart-type inter-graines ; % relatif au contrôleur fixe)")


if __name__ == "__main__":
    main()
