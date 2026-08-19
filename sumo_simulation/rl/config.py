"""Hyperparamètres centralisés du régulateur DQN.

Toutes les durées sont exprimées en SECONDES DE SIMULATION.
Le pas de simulation est fixé à STEP_LENGTH (voir env.py, option --step-length),
de sorte que 1 seconde simulée == 1 / STEP_LENGTH pas SUMO.
"""

import os

# --- Chemins ---
SIM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Configuration dédiée au RL : demande concentrée sur le carrefour étudié.
# map.sumocfg (demande OSM d'origine) laisse l'intersection en écoulement libre.
CONFIG_PATH = os.path.join(SIM_DIR, "rl.sumocfg")
# Même réseau, feu reconstruit en mode actionné (baseline forte).
CONFIG_ACTUATED = os.path.join(SIM_DIR, "rl_actuated.sumocfg")
DEMAND_FILE = os.path.join(SIM_DIR, "net_demand.rou.xml")
OUTPUT_DIR = os.path.join(SIM_DIR, "outputs")

# Carrefour ciblé (Thiès). None => auto-détection du premier feu du réseau.
TLS_ID = "cluster_6021368912_6083287698_6083287699_6083287700"

BACKEND_URL = "http://localhost:8000"

# --- Temporalité de la simulation ---
STEP_LENGTH = 1.0      # s par pas SUMO
DELTA_TIME = 5         # s entre deux décisions de l'agent
YELLOW_TIME = 3        # s de jaune, INCLUS dans DELTA_TIME
MIN_GREEN = 10         # s de vert avant qu'un changement soit autorisé
MAX_GREEN = 60         # s de vert au-delà desquelles rester est interdit
EPISODE_LEN = 3600     # s simulées par épisode -> 720 décisions

# --- MDP ---
# Normalisation des files d'attente dans le vecteur d'état.
MAX_QUEUE = 10.0

# --- Agent DQN ---
GAMMA = 0.99
LR = 5e-4
BUFFER_SIZE = 50_000
BATCH_SIZE = 64
LEARNING_STARTS = 1_000    # transitions avant le premier apprentissage
TRAIN_FREQ = 1             # une mise à jour par décision
TAU = 0.005                # soft update du réseau cible, par mise à jour
HIDDEN = (64, 64)

EPS_START = 1.0
EPS_END = 0.05
EPS_DECAY_STEPS = 30_000   # décroissance linéaire, PAR PAS (pas par épisode)

# --- Entraînement ---
N_EPISODES = 150
SEED_TRAIN_BASE = 1000     # graines d'entraînement : BASE + numéro d'épisode
SEED_EVAL = [7, 13, 21, 42, 77]   # graines réservées à l'évaluation
CHECKPOINT_EVERY = 10
