"""Agent Double DQN (PyTorch, CPU).

Corrige les défauts de l'implémentation précédente :
  - le réseau cible est initialisé par copie du réseau principal (sinon les
    cibles de Bellman sont du bruit pur au démarrage) ;
  - epsilon décroît PAR PAS et non par épisode ;
  - Double DQN : l'action est choisie par le réseau principal, évaluée par le
    réseau cible — réduit la surestimation des Q-valeurs ;
  - perte de Huber, plus robuste aux récompenses aberrantes ;
  - masquage des actions invalides avant l'argmax, au lieu d'un court-circuit
    qui retire la décision à l'agent ;
  - sauvegarde/chargement des poids.
"""

import random
from collections import deque

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import config as C


class QNetwork(nn.Module):
    def __init__(self, state_dim, num_actions, hidden=C.HIDDEN):
        super().__init__()
        layers, prev = [], state_dim
        for h in hidden:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            prev = h
        layers.append(nn.Linear(prev, num_actions))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


class ReplayBuffer:
    def __init__(self, capacity=C.BUFFER_SIZE):
        self.buf = deque(maxlen=capacity)

    def push(self, s, a, r, s2, done, mask2):
        self.buf.append((s, a, r, s2, done, mask2))

    def sample(self, batch_size):
        batch = random.sample(self.buf, batch_size)
        s, a, r, s2, d, m2 = zip(*batch)
        return (
            torch.as_tensor(np.array(s), dtype=torch.float32),
            torch.as_tensor(a, dtype=torch.int64).unsqueeze(1),
            torch.as_tensor(r, dtype=torch.float32).unsqueeze(1),
            torch.as_tensor(np.array(s2), dtype=torch.float32),
            torch.as_tensor(d, dtype=torch.float32).unsqueeze(1),
            torch.as_tensor(np.array(m2), dtype=torch.bool),
        )

    def __len__(self):
        return len(self.buf)


class DQNAgent:
    def __init__(self, state_dim, num_actions, seed=0):
        torch.manual_seed(seed)
        self.num_actions = num_actions
        self.policy = QNetwork(state_dim, num_actions)
        self.target = QNetwork(state_dim, num_actions)
        # Le réseau cible DOIT partir des mêmes poids que le réseau principal.
        self.target.load_state_dict(self.policy.state_dict())
        self.target.eval()

        self.opt = torch.optim.Adam(self.policy.parameters(), lr=C.LR)
        self.memory = ReplayBuffer()
        self.steps = 0
        self.last_loss = 0.0

    # --- Politique -------------------------------------------------------

    def epsilon(self):
        frac = min(1.0, self.steps / C.EPS_DECAY_STEPS)
        return C.EPS_START + frac * (C.EPS_END - C.EPS_START)

    def act(self, state, mask, greedy=False):
        """Choisit une action parmi celles autorisées par `mask`."""
        valid = np.flatnonzero(mask)
        if len(valid) == 1:
            return int(valid[0])
        if not greedy and random.random() < self.epsilon():
            return int(random.choice(valid))
        with torch.no_grad():
            q = self.policy(torch.as_tensor(state, dtype=torch.float32).unsqueeze(0))
        q = q.squeeze(0).numpy()
        q[~mask] = -np.inf          # masquage des actions invalides
        return int(np.argmax(q))

    # --- Apprentissage ---------------------------------------------------

    def update(self):
        if len(self.memory) < max(C.LEARNING_STARTS, C.BATCH_SIZE):
            return
        s, a, r, s2, d, m2 = self.memory.sample(C.BATCH_SIZE)

        q = self.policy(s).gather(1, a)

        with torch.no_grad():
            # Double DQN : argmax par le réseau principal, valeur par le cible.
            q_next_policy = self.policy(s2)
            q_next_policy[~m2] = -float("inf")
            best = q_next_policy.argmax(dim=1, keepdim=True)
            q_next = self.target(s2).gather(1, best)
            target = r + C.GAMMA * q_next * (1.0 - d)

        loss = F.smooth_l1_loss(q, target)     # Huber
        self.opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.policy.parameters(), 10.0)
        self.opt.step()
        self.last_loss = float(loss.item())

        # Soft update du réseau cible.
        with torch.no_grad():
            for tp, pp in zip(self.target.parameters(), self.policy.parameters()):
                tp.mul_(1.0 - C.TAU).add_(C.TAU * pp)

    # --- Persistance -----------------------------------------------------

    def save(self, path):
        torch.save({
            "policy": self.policy.state_dict(),
            "target": self.target.state_dict(),
            "opt": self.opt.state_dict(),
            "steps": self.steps,
        }, path)

    def load(self, path):
        ck = torch.load(path, map_location="cpu")
        self.policy.load_state_dict(ck["policy"])
        self.target.load_state_dict(ck["target"])
        self.opt.load_state_dict(ck["opt"])
        self.steps = ck.get("steps", 0)
