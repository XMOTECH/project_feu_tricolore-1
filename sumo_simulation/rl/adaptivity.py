"""Mesure le caractère adaptatif de la politique apprise.

Le nombre de changements de phase par épisode est très régulier (~215), ce qui
laisse soupçonner que l'agent aurait simplement ré-appris un cycle fixe. Le
tableau comparatif réfute cette hypothèse par l'absurde (un cycle fixe ne peut
pas battre un cycle fixe de moitié) ; ce script la réfute *positivement*.

AVERTISSEMENT MÉTHODOLOGIQUE — la corrélation agrégée « file -> durée de vert »
ne prouve RIEN. Mesurée sur le contrôleur fixe, elle vaut r = +0,54 : les phases
de l'axe majeur ont à la fois plus de vert (33 s contre 12 s) et plus de file. La
corrélation capte donc la topologie du cycle, pas une réaction au trafic. Elle
est conservée ici uniquement pour documenter ce piège.

Trois tests valides :

1. VARIANCE INTRA-PHASE de la durée de vert. Un cycle fixe a un écart-type
   rigoureusement nul par construction ; c'est sa signature. Une politique
   adaptative doit moduler la durée d'une même phase d'un passage à l'autre.

2. ARBITRAGE : quand plusieurs actions sont permises, l'agent sélectionne-t-il la
   phase dont la file est la plus longue ? Référence du hasard sur 4 phases : 25 %.
   Mesuré au seul instant où le choix existe (hors verrou de min_green).

3. RÉACTION À LA PRESSION CONCURRENTE : corrélation entre la durée d'un vert et la
   file maximale sur les branches NON desservies. Attendu négatif : plus une autre
   branche sature, plus l'agent doit écourter le vert courant. Ce test est
   insensible au confondant du test écarté, la pression concurrente n'étant pas
   liée à la durée programmée de la phase.

Note : le DQN maintient les files quasi nulles, donc la file à l'ouverture du vert
a très peu de variance. C'est un succès du contrôleur, mais cela rend tout test
fondé sur cette variable peu informatif — d'où le test 3, fondé sur la pression.

    py -3.14 -m rl.adaptivity
    py -3.14 -m rl.adaptivity --seeds 7 13 21 --episode-len 3600
"""

import argparse
import os

import numpy as np
import sumolib
import traci

from . import config as C
from .dqn import DQNAgent
from .env import SumoEnv

N_GROUPS = 4


# --- Cartographie phase -> branches desservies ----------------------------

def phase_topology(tls):
    """Associe à chaque phase verte l'ensemble des groupes d'approche qu'elle ouvre.

    `getControlledLanes()` renvoie une entrée par lien (avec doublons), et c'est
    cet ordre qui indexe la chaîne d'état du feu. Le regroupement en 4 branches
    reprend exactement la formule de `SumoEnv._grouped`, afin que les files
    mesurées ici soient celles que l'agent observe.
    """
    logic = traci.trafficlight.getAllProgramLogics(tls)[0]
    green_states = [
        p.state for p in logic.phases
        if "y" not in p.state.lower() and "g" in p.state.lower()
    ]
    links = traci.trafficlight.getControlledLanes(tls)
    lanes = list(dict.fromkeys(links))
    group_of = {l: (i * N_GROUPS) // len(lanes) for i, l in enumerate(lanes)}

    served = []
    for st in green_states:
        groups = {group_of[links[i]] for i, ch in enumerate(st)
                  if ch in "Gg" and i < len(links)}
        served.append(sorted(groups))
    return green_states, lanes, group_of, served


def grouped_queues(lanes, group_of):
    g = [0.0] * N_GROUPS
    for l in lanes:
        g[group_of[l]] += traci.lane.getLastStepHaltingNumber(l)
    return g


def queue_per_phase(q, served):
    """File en attente derrière chaque phase, vue comme somme de ses branches."""
    return [sum(q[g] for g in s) for s in served]


# --- Statistiques --------------------------------------------------------

def pearson(xs, ys):
    x, y = np.asarray(xs, float), np.asarray(ys, float)
    if len(x) < 3 or x.std() < 1e-9 or y.std() < 1e-9:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def spearman(xs, ys):
    """Corrélation de rang : insensible à la forme de la relation."""
    def rank(v):
        order = np.argsort(np.asarray(v, float), kind="mergesort")
        r = np.empty(len(v), float)
        r[order] = np.arange(len(v), dtype=float)
        return r
    return pearson(rank(xs), rank(ys))


def quartile_table(queues, durations):
    """Durée de vert moyenne par quartile de file à l'ouverture du vert."""
    q = np.asarray(queues, float)
    d = np.asarray(durations, float)
    edges = np.quantile(q, [0.25, 0.5, 0.75])
    bins = np.digitize(q, edges)
    rows = []
    for b in range(4):
        sel = bins == b
        if sel.sum():
            rows.append((b, int(sel.sum()), q[sel].mean(), d[sel].mean()))
    return rows


# --- Collecte : agent DQN ------------------------------------------------

def collect_dqn(seed, episode_len, model):
    env = SumoEnv(episode_len=episode_len, label="adapt")
    state = env.reset(seed=seed)
    agent = DQNAgent(env.state_dim, env.num_actions)
    agent.load(model)

    _, lanes, group_of, served = phase_topology(env.signal.id)

    intervals = []       # (phase, durée, file à l'ouverture, pression concurrente max)
    served_is_max = []   # la phase au vert est-elle celle de file maximale ?
    picked_is_max = []   # quand un changement est permis, l'agent choisit-il le max ?

    cur, onset_t = env.signal.cur, 0.0
    onset_q = queue_per_phase(grouped_queues(lanes, group_of), served)[cur]
    rival_peak = 0.0     # file max vue sur les autres phases pendant ce vert
    done = False

    while not done:
        per_phase = queue_per_phase(grouped_queues(lanes, group_of), served)
        mask = env.action_mask()
        action = agent.act(state, mask, greedy=True)

        # Pression concurrente : la file la plus longue hors phase courante.
        rival_peak = max(rival_peak,
                         max((v for p, v in enumerate(per_phase) if p != cur),
                             default=0.0))

        # Ne compter que les instants où l'arbitrage a un sens : au moins une
        # branche non vide, sinon « servir la file max » est indéterminé.
        if max(per_phase) > 0:
            served_is_max.append(per_phase[cur] >= max(per_phase) - 1e-9)
            if mask.sum() > 1:
                valid = [p for p in range(env.num_actions) if mask[p]]
                best = max(per_phase[p] for p in valid)
                picked_is_max.append(per_phase[action] >= best - 1e-9)

        state, _, done, _ = env.step(action)

        if env.signal.cur != cur:
            intervals.append((cur, env.sim_time - onset_t, onset_q, rival_peak))
            cur, onset_t = env.signal.cur, env.sim_time
            onset_q = queue_per_phase(grouped_queues(lanes, group_of), served)[cur]
            rival_peak = 0.0

    env.close()
    return intervals, served_is_max, picked_is_max


# --- Collecte : baselines gérées par SUMO --------------------------------

def collect_baseline(seed, episode_len, controller):
    cfg = C.CONFIG_ACTUATED if controller == "actue" else C.CONFIG_PATH
    if not os.path.exists(cfg):
        raise FileNotFoundError(f"{cfg} manquant.")

    env = SumoEnv(episode_len=episode_len, label="adapt")
    env._write_demand(seed)          # même demande que l'agent

    traci.start([
        sumolib.checkBinary("sumo"), "-c", cfg,
        "--step-length", str(C.STEP_LENGTH), "--seed", str(seed),
        "--no-warnings", "true", "--no-step-log", "true",
        "--time-to-teleport", "-1", "--waiting-time-memory", "10000",
    ], label="adapt")

    tls = C.TLS_ID or traci.trafficlight.getIDList()[0]
    green_states, lanes, group_of, served = phase_topology(tls)
    index_of = {st: i for i, st in enumerate(green_states)}

    intervals, served_is_max = [], []
    cur, onset_t, onset_q = None, 0.0, 0.0
    rival_peak = 0.0
    t = 0.0

    while t < episode_len and traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        t += C.STEP_LENGTH

        state = traci.trafficlight.getRedYellowGreenState(tls)
        idx = index_of.get(state)

        if idx is not None and idx != cur:
            per_phase = queue_per_phase(grouped_queues(lanes, group_of), served)
            if cur is not None:
                intervals.append((cur, t - onset_t, onset_q, rival_peak))
            cur, onset_t, onset_q = idx, t, per_phase[idx]
            rival_peak = 0.0

        # Échantillonné au pas de décision de l'agent, pour comparabilité.
        if cur is not None and abs(t % C.DELTA_TIME) < 1e-9:
            per_phase = queue_per_phase(grouped_queues(lanes, group_of), served)
            rival_peak = max(rival_peak,
                             max((v for p, v in enumerate(per_phase) if p != cur),
                                 default=0.0))
            if max(per_phase) > 0:
                served_is_max.append(per_phase[cur] >= max(per_phase) - 1e-9)

    traci.close()
    return intervals, served_is_max, []


# --- Rapport -------------------------------------------------------------

def report(name, intervals, served_is_max, picked_is_max):
    phases = [p for p, _, _, _ in intervals]
    durs = [d for _, d, _, _ in intervals]
    qs = [q for _, _, q, _ in intervals]
    rivals = [r for _, _, _, r in intervals]

    print(f"\n{'=' * 70}")
    print(f"  {name}   ({len(intervals)} verts observés)")
    print("=" * 70)
    print(f"  Durée de vert : moy {np.mean(durs):.1f} s   "
          f"écart-type {np.std(durs):.1f} s   "
          f"[{min(durs):.0f}, {max(durs):.0f}]")

    # --- Test 1 : variance intra-phase (signature du cycle fixe) ---
    print("\n  [1] VARIANCE INTRA-PHASE — un cycle fixe donne un écart-type nul")
    print(f"      {'phase':>7}{'n':>6}{'durée moy':>12}{'écart-type':>12}"
          f"{'min':>7}{'max':>7}")
    intra = []
    for p in sorted(set(phases)):
        d = [durs[i] for i, ph in enumerate(phases) if ph == p]
        if len(d) < 3:
            continue
        intra.append(np.std(d))
        print(f"      {p:7d}{len(d):6d}{np.mean(d):11.1f} s{np.std(d):11.1f} s"
              f"{min(d):7.0f}{max(d):7.0f}")
    if intra:
        print(f"      -> écart-type intra-phase moyen : {np.mean(intra):.2f} s")

    # --- Test 2 : arbitrage ---
    print("\n  [2] ARBITRAGE — la phase servie est-elle la plus chargée ?")
    if served_is_max:
        print(f"      phase au vert = file max : {100 * np.mean(served_is_max):5.1f} %"
              f"   ({len(served_is_max)} instants)")
    if picked_is_max:
        print(f"      choix = file max quand le changement est permis : "
              f"{100 * np.mean(picked_is_max):5.1f} %   ({len(picked_is_max)} décisions)")
    else:
        print("      (non applicable : le contrôleur ne choisit pas sa phase)")
    print("      référence du hasard sur 4 phases : 25 %")

    # --- Test 3 : réaction à la pression concurrente ---
    print("\n  [3] PRESSION CONCURRENTE -> durée du vert (attendu : négatif)")
    r_riv, rho_riv = pearson(rivals, durs), spearman(rivals, durs)
    print(f"      Pearson r = {r_riv:+.3f}   Spearman = {rho_riv:+.3f}")
    print(f"      {'quartile':>10}{'n':>6}{'pression':>11}{'durée moy':>12}")
    for b, n, mr, md in quartile_table(rivals, durs):
        print(f"      {'Q' + str(b + 1):>10}{n:6d}{mr:11.2f}{md:11.1f} s")

    # --- Test écarté, conservé pour documenter le piège ---
    print("\n  [x] ÉCARTÉ — file à l'ouverture -> durée "
          f"(r = {pearson(qs, durs):+.3f}) : confondu par la topologie du cycle,")
    print(f"      file moyenne à l'ouverture = {np.mean(qs):.2f} véh. "
          "(trop peu de variance pour conclure)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--controllers", nargs="+", default=["dqn", "fixe"],
                    choices=["dqn", "fixe", "actue"])
    ap.add_argument("--seeds", type=int, nargs="+", default=[7, 13, 21])
    ap.add_argument("--episode-len", type=int, default=C.EPISODE_LEN)
    ap.add_argument("--model", type=str,
                    default=os.path.join(C.OUTPUT_DIR, "dqn_best.pt"))
    args = ap.parse_args()

    if "dqn" in args.controllers and not os.path.exists(args.model):
        raise SystemExit(f"Modèle introuvable : {args.model}")

    for ctrl in args.controllers:
        intervals, served_max, picked_max = [], [], []
        for seed in args.seeds:
            print(f"  {ctrl} / graine {seed} ...", flush=True)
            if ctrl == "dqn":
                i, s, p = collect_dqn(seed, args.episode_len, args.model)
            else:
                i, s, p = collect_baseline(seed, args.episode_len, ctrl)
            intervals += i
            served_max += s
            picked_max += p
        report(f"Contrôleur « {ctrl} »  —  graines {args.seeds}",
               intervals, served_max, picked_max)

    print()


if __name__ == "__main__":
    main()
