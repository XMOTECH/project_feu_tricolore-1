"""Environnement SUMO pour la régulation de feux par apprentissage par renforcement.

MDP
---
État      : 13 réels — 4 files normalisées, 4 densités, one-hot de la phase
            verte courante (4), indicateur "min_green écoulé" (1).
Action    : indice de la prochaine phase verte, dans [0, num_green).
            Les actions invalides sont masquées (voir TrafficSignal.valid_actions).
Récompense: variation du temps d'attente cumulé entre deux décisions,
            r = (W_avant - W_après) / 100. Positive quand l'agent résorbe
            l'attente. Le coût d'un changement de phase est capturé
            naturellement par le jaune — aucune pénalité arbitraire n'est
            nécessaire.
"""

import os
import sys

import numpy as np

if "SUMO_HOME" not in os.environ:
    sys.exit("Variable d'environnement 'SUMO_HOME' non définie.")
sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

import sumolib  # noqa: E402
import traci  # noqa: E402

from . import config as C  # noqa: E402
from .traffic_signal import TrafficSignal  # noqa: E402


class SumoEnv:
    def __init__(self, config_path=C.CONFIG_PATH, tls_id=C.TLS_ID, use_gui=False,
                 episode_len=C.EPISODE_LEN, tripinfo_path=None, label="default",
                 regenerate_demand=True, demand_scale=1.0):
        self.config_path = config_path
        self.tls_id = tls_id
        self.use_gui = use_gui
        self.episode_len = episode_len
        self.tripinfo_path = tripinfo_path
        self.label = label
        # Régénérer la demande à chaque épisode force l'agent à généraliser
        # au lieu de mémoriser un flux unique.
        self.regenerate_demand = regenerate_demand
        self.demand_scale = demand_scale
        self.binary = sumolib.checkBinary("sumo-gui" if use_gui else "sumo")

        self.signal = None
        self.sim_time = 0.0
        self.last_wait = 0.0
        self.metrics = {}

        # Dimensions connues avant le premier reset (num_green fixé par le réseau).
        self._num_green = None

    # --- Cycle de vie ----------------------------------------------------

    def _sumo_cmd(self, seed):
        cmd = [
            self.binary,
            "-c", self.config_path,
            "--step-length", str(C.STEP_LENGTH),
            "--no-warnings", "true",
            "--no-step-log", "true",
            "--time-to-teleport", "-1",     # pas de téléportation : les blocages
                                            # doivent être visibles dans la récompense
            "--waiting-time-memory", "10000",
            "--seed", str(seed),
        ]
        if self.tripinfo_path:
            cmd += ["--tripinfo-output", self.tripinfo_path]
        if self.use_gui:
            cmd += ["--start", "--quit-on-end"]
        return cmd

    def reset(self, seed=0):
        self.close()
        if self.regenerate_demand:
            self._write_demand(seed)
        traci.start(self._sumo_cmd(seed), label=self.label)
        self.conn = traci.getConnection(self.label)

        tls_id = self.tls_id
        if not tls_id:
            ids = traci.trafficlight.getIDList()
            if not ids:
                raise RuntimeError("Aucun feu tricolore dans le réseau SUMO.")
            tls_id = ids[0]

        self.signal = TrafficSignal(
            tls_id, C.DELTA_TIME, C.YELLOW_TIME, C.MIN_GREEN, C.MAX_GREEN,
            C.STEP_LENGTH,
        )
        self._num_green = self.signal.num_green
        self.sim_time = 0.0
        self.last_wait = self.signal.accumulated_waiting_time()
        self.metrics = {"queue": [], "speed": [], "wait": [], "switches": 0}
        return self._observe()

    def _write_demand(self, seed):
        """Régénère le fichier de flux pour la graine courante."""
        import subprocess
        subprocess.run(
            [sys.executable, "-m", "rl.make_demand",
             "--seed", str(seed),
             "--out", C.DEMAND_FILE,
             "--duration", str(self.episode_len),
             "--scale", str(self.demand_scale)],
            cwd=C.SIM_DIR, check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

    def close(self):
        try:
            traci.close()
        except Exception:
            pass

    # --- Dimensions ------------------------------------------------------

    @property
    def num_actions(self):
        if self._num_green is None:
            raise RuntimeError("Appeler reset() avant de lire num_actions.")
        return self._num_green

    @property
    def state_dim(self):
        return 4 + 4 + self.num_actions + 1

    # --- Boucle ----------------------------------------------------------

    def _sim_step(self, duration_s):
        """Avance la simulation de `duration_s` secondes simulées."""
        n = int(round(duration_s / C.STEP_LENGTH))
        for _ in range(n):
            traci.simulationStep()
            self.sim_time += C.STEP_LENGTH

    def _grouped(self, per_lane):
        """Agrège une mesure par voie en 4 groupes d'approche.

        Le carrefour de Thiès a 8 voies entrantes (4 branches x 2 voies) ;
        on somme deux à deux dans l'ordre des voies contrôlées.
        """
        lanes = self.signal.lanes
        groups = [0.0] * 4
        for i, v in enumerate(per_lane):
            groups[(i * 4) // max(1, len(lanes))] += v
        return groups

    def _observe(self):
        q = self._grouped(self.signal.queues())
        d = self._grouped(self.signal.densities())
        phase = [0.0] * self.num_actions
        phase[self.signal.cur] = 1.0
        ready = [1.0 if self.signal.can_switch() else 0.0]
        obs = [min(1.0, x / C.MAX_QUEUE) for x in q] + \
              [min(1.0, x / 2.0) for x in d] + phase + ready
        return np.asarray(obs, dtype=np.float32)

    def action_mask(self):
        mask = np.zeros(self.num_actions, dtype=bool)
        for a in self.signal.valid_actions():
            mask[a] = True
        return mask

    def step(self, action):
        prev = self.signal.cur
        self.signal.apply(action, self._sim_step)
        if self.signal.cur != prev:
            self.metrics["switches"] += 1

        wait = self.signal.accumulated_waiting_time()
        reward = (self.last_wait - wait) / 100.0
        self.last_wait = wait

        q = self.signal.queues()
        self.metrics["queue"].append(sum(q))
        self.metrics["speed"].append(self.signal.mean_speed() * 3.6)
        self.metrics["wait"].append(wait)

        done = (
            self.sim_time >= self.episode_len
            or traci.simulation.getMinExpectedNumber() == 0
        )
        return self._observe(), reward, done, {"queue": sum(q)}

    def episode_summary(self):
        m = self.metrics
        n = max(1, len(m["queue"]))
        return {
            "mean_queue": sum(m["queue"]) / n,
            "mean_speed": sum(m["speed"]) / n,
            "mean_wait": sum(m["wait"]) / n,
            "switches": m["switches"],
            "decisions": n,
        }
