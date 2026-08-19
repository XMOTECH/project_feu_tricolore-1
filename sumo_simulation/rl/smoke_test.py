"""Vérifie que l'agent contrôle RÉELLEMENT le feu.

C'est le test que l'implémentation précédente ne passait pas : avec setPhase(),
SUMO ré-enchaînait les phases du programme statique et l'état interne de l'agent
divergeait de l'état réel du feu dès la première décision.

    py -3.14 -m rl.smoke_test
"""

from . import config as C
from .env import SumoEnv

import traci


def main():
    env = SumoEnv(episode_len=600, label="smoke")
    env.reset(seed=1)
    sig = env.signal

    print(f"feu           : {sig.id}")
    print(f"phases vertes : {sig.num_green}")
    for i, s in enumerate(sig.green_states):
        print(f"   [{i}] {s}")
    print(f"voies         : {len(sig.lanes)}")
    print(f"état          : {env.state_dim}D\n")

    # 1. Le feu tient-il sans ordre ? Un programme statique aurait changé
    #    d'état après 27 s de vert.
    start = traci.trafficlight.getRedYellowGreenState(sig.id)
    env._sim_step(60)
    held = traci.trafficlight.getRedYellowGreenState(sig.id)
    assert held == start, (
        f"ÉCHEC : le feu a changé tout seul en 60 s ({start!r} -> {held!r}). "
        "Le programme statique tourne encore."
    )
    print(f"[OK] feu maintenu 60 s sans ordre de l'agent : {held}")

    # 2. Le feu obéit-il à chaque changement demandé, avec passage au jaune ?
    sig.time_since_green = C.MIN_GREEN
    for target in range(1, sig.num_green):
        seen_yellow = {"v": False}

        def watch(d):
            for _ in range(int(round(d / C.STEP_LENGTH))):
                traci.simulationStep()
                env.sim_time += C.STEP_LENGTH
                if "y" in traci.trafficlight.getRedYellowGreenState(sig.id):
                    seen_yellow["v"] = True

        sig.apply(target, watch)
        sig.assert_in_sync()
        assert seen_yellow["v"], f"ÉCHEC : pas de jaune avant la phase {target}"
        print(f"[OK] passage -> phase {target} (jaune observé, feu synchronisé)")
        sig.time_since_green = C.MIN_GREEN

    # 3. Masquage des actions.
    sig.time_since_green = 0
    assert sig.valid_actions() == [sig.cur], "ÉCHEC : min_green non respecté"
    print(f"[OK] min_green : seule l'action {sig.cur} est autorisée")

    sig.time_since_green = C.MAX_GREEN
    assert sig.cur not in sig.valid_actions(), "ÉCHEC : max_green non respecté"
    print(f"[OK] max_green : rester est interdit ({sig.valid_actions()})")

    # 4. Récompense et observation.
    sig.time_since_green = C.MIN_GREEN
    obs, r, done, info = env.step(0)
    print(f"[OK] step -> obs={obs.shape} reward={r:.3f} file={info['queue']}")

    env.close()
    print("\nTOUS LES TESTS PASSENT — l'agent contrôle bien le feu.")


if __name__ == "__main__":
    main()
