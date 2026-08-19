"""Boucle d'entraînement du régulateur DQN.

Usage (Python Windows, SUMO natif) :
    py -3.14 -m rl.train --episodes 150
    py -3.14 -m rl.train --episodes 2 --episode-len 600   # test rapide
"""

import argparse
import csv
import os
import time

from . import config as C
from .dqn import DQNAgent
from .env import SumoEnv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=C.N_EPISODES)
    ap.add_argument("--episode-len", type=int, default=C.EPISODE_LEN)
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--resume", type=str, default=None)
    ap.add_argument("--out", type=str, default=C.OUTPUT_DIR)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    log_path = os.path.join(args.out, "training_log.csv")
    ckpt_path = os.path.join(args.out, "dqn_checkpoint.pt")
    best_path = os.path.join(args.out, "dqn_best.pt")

    env = SumoEnv(use_gui=args.gui, episode_len=args.episode_len, label="train")
    state = env.reset(seed=C.SEED_TRAIN_BASE)
    agent = DQNAgent(env.state_dim, env.num_actions)
    if args.resume:
        agent.load(args.resume)
        print(f"Reprise depuis {args.resume} (pas={agent.steps})")

    print(f"état={env.state_dim}D  actions={env.num_actions}  "
          f"voies={len(env.signal.lanes)}  feu={env.signal.id}")

    with open(log_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["episode", "reward", "epsilon", "loss", "mean_queue",
                         "mean_speed_kmh", "mean_wait", "switches", "decisions",
                         "wall_s"])

        # Le retour cumulé ne peut PAS servir de critère de sélection : la
        # récompense étant une différence (W_avant - W_après), sa somme sur un
        # épisode se télescope en (W_initial - W_final) / 100, soit du bruit
        # autour de 0. On sélectionne sur l'attente moyenne, et seulement une
        # fois l'exploration éteinte (sinon epsilon fausse la comparaison).
        best_wait = float("inf")
        for ep in range(1, args.episodes + 1):
            t0 = time.time()
            # Graine différente à chaque épisode : l'agent doit généraliser,
            # pas mémoriser un flux unique.
            if ep > 1:
                state = env.reset(seed=C.SEED_TRAIN_BASE + ep)

            total_reward, done = 0.0, False
            while not done:
                mask = env.action_mask()
                action = agent.act(state, mask)
                next_state, reward, done, _ = env.step(action)
                agent.memory.push(state, action, reward, next_state, done,
                                  env.action_mask())
                state = next_state
                total_reward += reward
                agent.steps += 1
                if agent.steps % C.TRAIN_FREQ == 0:
                    agent.update()

            s = env.episode_summary()
            dt = time.time() - t0
            writer.writerow([ep, round(total_reward, 2), round(agent.epsilon(), 4),
                             round(agent.last_loss, 5), round(s["mean_queue"], 2),
                             round(s["mean_speed"], 2), round(s["mean_wait"], 1),
                             s["switches"], s["decisions"], round(dt, 1)])
            fh.flush()

            print(f"ep {ep:3d}/{args.episodes}  R={total_reward:8.2f}  "
                  f"eps={agent.epsilon():.3f}  file={s['mean_queue']:5.1f}  "
                  f"v={s['mean_speed']:4.1f}km/h  chg={s['switches']:3d}  "
                  f"{dt:.0f}s")

            if ep % C.CHECKPOINT_EVERY == 0:
                agent.save(ckpt_path)
            if agent.epsilon() <= C.EPS_END + 1e-6 and s["mean_wait"] < best_wait:
                best_wait = s["mean_wait"]
                agent.save(best_path)

    agent.save(ckpt_path)
    env.close()
    print(f"\nTerminé. Poids : {ckpt_path}\n         Meilleur : {best_path}"
          f" (attente moyenne {best_wait:.1f} s)"
          f"\n         Journal : {log_path}")


if __name__ == "__main__":
    main()
