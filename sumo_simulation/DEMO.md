# Lancer la démo

## Prérequis (une seule fois)

SUMO 1.27 natif Windows, avec `SUMO_HOME` défini :

```
C:\Program Files (x86)\Eclipse\Sumo\
```

Vérifier que tout répond :

```
py -3.14 -c "import traci, torch, numpy; print('ok')"
py -3.14 -m rl.smoke_test
```

`smoke_test` prouve que l'agent tient réellement le feu (le feu reste figé 60 s
sans ordre, alors qu'un programme statique aurait basculé à 27 s). S'il échoue,
inutile d'aller plus loin.

Toutes les commandes se lancent **depuis `sumo_simulation/`**.

## La démo

```
py -3.14 -m rl.demo
```

SUMO-GUI s'ouvre, l'agent entraîné commande le carrefour, et la télémétrie
défile en console. Par défaut : graine 7 (jamais vue à l'entraînement),
30 minutes simulées, modèle `outputs/dqn_best.pt`.

### La démo qui convainc : la même demande, deux contrôleurs

Le seul argument qui porte, c'est la comparaison. Même graine, même trafic,
seul le contrôleur change :

```
py -3.14 -m rl.demo --controller fixe --seed 7      # le feu actuel
py -3.14 -m rl.demo --controller dqn  --seed 7      # le régulateur appris
```

Sur 5 minutes simulées (graine 7), l'écart est visible à l'œil nu :

| | file moyenne | attente moyenne | vitesse |
|---|---|---|---|
| fixe | 5.40 véh. | 165.2 s | 34.6 km/h |
| **DQN** | **1.70 véh.** | **18.5 s** | **54.0 km/h** |

À l'écran : avec le feu fixe, une file s'accumule sur l'axe chargé pendant que
la voie transversale reste vide au vert. Le DQN écourte les verts inutiles et
rend la main à la branche qui sature.

### Options

| Option | Effet |
|---|---|
| `--controller {dqn,fixe,actue}` | contrôleur à démontrer |
| `--seed N` | graine (7, 13, 21, 42, 77 = réservées à l'évaluation) |
| `--episode-len N` | durée simulée en s (défaut 1800 = 30 min) |
| `--scale F` | multiplicateur de demande — `--scale 1.5` pour saturer |
| `--report-every N` | intervalle de télémétrie en s simulées |
| `--model CHEMIN` | autre jeu de poids |

Pour une démo courte et dense :

```
py -3.14 -m rl.demo --episode-len 600 --scale 1.4 --report-every 30
```

### Dans la fenêtre SUMO

- **Delay (ms)** dans la barre d'outils : à 0 la simulation défile trop vite
  pour être lisible — monter à 100–200 ms pour commenter.
- Molette pour zoomer sur le carrefour ; clic droit sur le feu >
  *Show Phase Index* pour suivre les phases.
- La simulation se ferme seule à la fin (`--quit-on-end`).

## Reproduire les chiffres du rapport

```
py -3.14 -m rl.evaluate --model outputs/dqn_best.pt
```

Headless, 5 graines, les trois contrôleurs, ~10 min. Produit le tableau de
`RESULTATS.md` (DQN à −50.7 % de temps perdu face au feu fixe).

## Réentraîner de zéro

```
py -3.14 -m rl.train --episodes 150      # ~45 min
```

Journal dans `outputs/training_log.csv`, poids dans `outputs/dqn_checkpoint.pt`
et `outputs/dqn_best.pt`.

## Si ça coince

| Symptôme | Cause |
|---|---|
| `SUMO_HOME non définie` | variable d'environnement absente — la définir puis rouvrir le terminal |
| `Modèle introuvable` | lancer `rl.train` d'abord, ou pointer `--model` sur un checkpoint |
| `osm.net.actuated.xml.gz manquant` | requis par `--controller actue` uniquement : `netconvert --sumo-net-file osm.net.xml.gz --tls.default-type actuated --tls.rebuild -o osm.net.actuated.xml.gz` |
| `Feu désynchronisé` | garde-fou de `traffic_signal.py` : quelque chose a repris la main sur le feu |
| Fenêtre vide, aucun véhicule | `net_demand.rou.xml` non régénéré — la démo le fait, sinon `py -3.14 -m rl.make_demand --seed 7` |
