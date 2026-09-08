"""Contrôleur Max-Pressure (Varaiya, 2013) avec options d'agrégation et d'hystérésis.

Trois modes de calcul de la pression par phase :
  - 'sum'  : somme des files des groupes desservis (MP naïf, sujet à famine de Ph3)
  - 'mean' : moyenne des files (normalisé par le nombre de groupes ouverts)
  - 'max'  : file maximale parmi les groupes desservis (recommandé pour carrefour asymétrique)

Hystérésis :
  Ne changer de phase que si pression[best] >= pression[courante] + hysteresis.
"""

import os
import traci

from . import config as C
from .adaptivity import phase_topology, grouped_queues
from .env import SumoEnv


def queue_per_phase(q, served, mode="max"):
    """Calcule la pression pour chaque phase verte selon le mode spécifié."""
    pressures = []
    for s in served:
        if not s:
            pressures.append(0.0)
            continue
        vals = [q[g] for g in s]
        if mode == "sum":
            pressures.append(sum(vals))
        elif mode == "mean":
            pressures.append(sum(vals) / len(vals))
        elif mode == "max":
            pressures.append(max(vals))
        else:
            pressures.append(max(vals))
    return pressures


def select_action(lanes, group_of, served, valid_actions, mode="max", current=None, hysteresis=0.0):
    """Sélectionne l'action optimale Max-Pressure."""
    q = grouped_queues(lanes, group_of)
    per_phase = queue_per_phase(q, served, mode=mode)
    
    cur = current
    cur_p = per_phase[cur] if (cur is not None and cur < len(per_phase)) else 0.0
    
    best_action = cur if (cur is not None and cur in valid_actions) else valid_actions[0]
    best_val = per_phase[best_action]
    
    for a in valid_actions:
        val = per_phase[a]
        if a == cur:
            if val >= best_val:
                best_val = val
                best_action = cur
        else:
            if val >= cur_p + hysteresis and val > best_val:
                best_val = val
                best_action = a
                
    return best_action


def run_mp(seed, episode_len, out_dir, mode="max", hysteresis=0.0):
    """Exécute un épisode complet Max-Pressure et extrait le tripinfo."""
    from .evaluate import parse_tripinfo
    
    tri = os.path.join(out_dir, f"tripinfo_mp_{seed}.xml")
    env = SumoEnv(episode_len=episode_len, tripinfo_path=tri, label=f"mp{seed}")
    env.reset(seed=seed)
    
    _, lanes, group_of, served = phase_topology(env.signal.id)
    
    done = False
    while not done:
        action = select_action(
            lanes, group_of, served, env.signal.valid_actions(),
            mode=mode, current=env.signal.cur, hysteresis=hysteresis,
        )
        _, _, done, _ = env.step(action)
        
    env.close()
    return parse_tripinfo(tri)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, nargs="+", default=[7])
    ap.add_argument("--episode-len", type=int, default=600)
    ap.add_argument("--out", type=str, default=C.OUTPUT_DIR)
    ap.add_argument("--mode", choices=["sum", "mean", "max"], default="max")
    ap.add_argument("--hysteresis", type=float, default=0.0)
    args = ap.parse_args()
    
    os.makedirs(args.out, exist_ok=True)
    for s in args.seeds:
        m = run_mp(s, args.episode_len, args.out, mode=args.mode, hysteresis=args.hysteresis)
        if m:
            print(f"MP mode={args.mode} seed={s:<3} timeLoss={m['timeLoss']:6.1f}s wait={m['waitingTime']:6.1f}s n={m['n']}")
