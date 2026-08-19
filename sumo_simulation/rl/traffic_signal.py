"""Contrôle bas niveau du carrefour à feux.

Point clé : on n'utilise JAMAIS traci.trafficlight.setPhase(). Cette commande
positionne la phase mais réarme sa durée programmée, si bien que SUMO enchaîne
ensuite tout seul sur la phase suivante — l'agent croit tenir le feu alors que
le programme statique continue de tourner.

On passe donc par setRedYellowGreenState(), qui bascule le feu dans un
programme "online" d'une phase à durée infinie : l'état ne change que si on le
change explicitement.
"""

import traci


class TrafficSignal:
    """Expose les phases vertes d'un feu et applique les transitions."""

    def __init__(self, tls_id, delta_time, yellow_time, min_green, max_green,
                 step_length):
        self.id = tls_id
        self.delta_time = delta_time
        self.yellow_time = yellow_time
        self.min_green = min_green
        self.max_green = max_green
        self.step_length = step_length

        logic = traci.trafficlight.getAllProgramLogics(self.id)[0]
        # Une phase est "verte" si elle allume au moins un feu vert et aucun jaune.
        self.green_states = [
            p.state for p in logic.phases
            if "y" not in p.state.lower() and "g" in p.state.lower()
        ]
        if not self.green_states:
            raise RuntimeError(f"Aucune phase verte trouvée pour le feu {self.id}")

        self.num_green = len(self.green_states)

        # Voies entrantes contrôlées, dédoublonnées en gardant l'ordre.
        self.lanes = list(dict.fromkeys(traci.trafficlight.getControlledLanes(self.id)))
        self.lane_capacity = {
            l: max(1.0, traci.lane.getLength(l) / 7.5) for l in self.lanes
        }

        self.cur = 0
        self.time_since_green = 0.0
        self._apply_green(self.cur)

    # --- Transitions -----------------------------------------------------

    def _apply_green(self, idx):
        traci.trafficlight.setRedYellowGreenState(self.id, self.green_states[idx])

    def _yellow_between(self, old, new):
        """Construit l'état jaune de transition entre deux phases vertes.

        Un feu qui passe de vert à rouge doit d'abord passer au jaune ; les
        autres gardent leur état cible. Le calcul est fait à la volée car le
        jaune codé dans le réseau n'est valide que pour la phase suivante,
        alors que l'agent peut sauter de n'importe quelle phase à n'importe
        quelle autre.
        """
        o, n = self.green_states[old], self.green_states[new]
        return "".join(
            "y" if (a in "Gg" and b not in "Gg") else b
            for a, b in zip(o, n)
        )

    def can_switch(self):
        return self.time_since_green >= self.min_green

    def must_switch(self):
        return self.time_since_green >= self.max_green

    def valid_actions(self):
        """Actions autorisées, en tenant compte des contraintes min/max green."""
        if not self.can_switch():
            return [self.cur]                       # trop tôt : on doit rester
        actions = list(range(self.num_green))
        if self.must_switch():
            actions.remove(self.cur)                # trop tard : on doit changer
        return actions

    def apply(self, action, sim_step):
        """Applique une action et avance la simulation de delta_time secondes.

        `sim_step(duree_en_secondes)` est fourni par l'environnement afin que
        celui-ci garde la main sur le comptage du temps et la télémétrie.
        Les deux branches consomment exactement delta_time : c'est ce qui rend
        les récompenses de STAY et de SWITCH comparables.
        """
        if action != self.cur and self.can_switch():
            traci.trafficlight.setRedYellowGreenState(
                self.id, self._yellow_between(self.cur, action)
            )
            sim_step(self.yellow_time)
            self._apply_green(action)
            sim_step(self.delta_time - self.yellow_time)
            self.cur = action
            self.time_since_green = self.delta_time - self.yellow_time
        else:
            sim_step(self.delta_time)
            self.time_since_green += self.delta_time

    # --- Observation -----------------------------------------------------

    def queues(self):
        """Nombre de véhicules à l'arrêt par voie contrôlée."""
        return [traci.lane.getLastStepHaltingNumber(l) for l in self.lanes]

    def densities(self):
        """Occupation de chaque voie, rapportée à sa capacité."""
        return [
            min(1.0, traci.lane.getLastStepVehicleNumber(l) / self.lane_capacity[l])
            for l in self.lanes
        ]

    def accumulated_waiting_time(self):
        """Temps d'attente cumulé de tous les véhicules sur les voies contrôlées."""
        total = 0.0
        for l in self.lanes:
            for v in traci.lane.getLastStepVehicleIDs(l):
                total += traci.vehicle.getAccumulatedWaitingTime(v)
        return total

    def mean_speed(self):
        speeds = [traci.lane.getLastStepMeanSpeed(l) for l in self.lanes]
        return sum(speeds) / len(speeds) if speeds else 0.0

    def assert_in_sync(self):
        """Garde-fou : l'état réel du feu doit correspondre à l'état interne.

        C'est le test qui échouait silencieusement avec setPhase().
        """
        actual = traci.trafficlight.getRedYellowGreenState(self.id)
        expected = self.green_states[self.cur]
        if actual != expected:
            raise AssertionError(
                f"Feu désynchronisé — SUMO={actual!r} agent={expected!r}"
            )
