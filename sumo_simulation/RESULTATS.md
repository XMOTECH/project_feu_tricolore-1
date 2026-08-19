# Résultats — régulation de feux par DQN (carrefour de Thiès)

Carrefour : `cluster_6021368912_6083287698_6083287699_6083287700` (4 phases vertes, 8 voies).

## Entraînement

150 épisodes de 3600 s simulées (720 décisions/épisode), demande régénérée à
chaque épisode avec une graine différente (`SEED_TRAIN_BASE + ep`) pour forcer
la généralisation. Double DQN, perte de Huber, cible en soft update.

| épisodes | attente moy. (s) | file moy. | vitesse (km/h) |
|---|---|---|---|
| 1–25 | 413.3 | 8.35 | 33.6 |
| 26–50 | 91.0 | 4.31 | 40.7 |
| 51–75 | 50.5 | 3.13 | 45.5 |
| 76–100 | 43.2 | 2.85 | 47.6 |
| 101–125 | 38.9 | 2.65 | 48.6 |
| 126–150 | **34.1** | **2.48** | **49.4** |

Plateau atteint vers l'épisode 70 ; les 80 derniers épisodes affinent.

## Évaluation

5 graines réservées (7, 13, 21, 42, 77), jamais vues à l'entraînement.
Épisodes de 3600 s, même demande pour les trois contrôleurs. Politique en
exploitation pure (epsilon = 0). Métriques issues de `tripinfo.xml`.

| Contrôleur | timeLoss (s) | attente (s) | durée (s) | v (m/s) | Δ timeLoss |
|---|---|---|---|---|---|
| fixe (statique 27/6/6/6…) | 31.5 ± 0.5 | 23.8 ± 0.4 | 48.5 | 6.37 | référence |
| actué (gap-out, minDur 8 / maxDur 50) | 34.2 ± 1.1 | 25.8 ± 0.8 | 51.2 | 5.72 | **+8.7 %** |
| **DQN** | **15.5 ± 0.6** | **9.0 ± 0.5** | **32.7** | **8.16** | **−50.7 %** |

Écart-type inter-graines. ~850–900 véhicules terminés par épisode et par
contrôleur, écarts de comptage < 1 % : les trois contrôleurs écoulent la même
demande, la comparaison porte bien sur la qualité de la régulation.

Le DQN divise le temps perdu par deux et l'attente par 2,6 face au feu fixe.

**La baseline actionnée est plus mauvaise que le feu fixe (+8.7 %).** Ce n'est
pas une anomalie : la détection par gap prolonge le vert d'une branche tant que
des véhicules arrivent, ce qui pénalise l'axe secondaire sur un carrefour à
demande asymétrique et soutenue (l'axe majeur est chargé 2×). Le contrôleur
fixe, lui, garantit un tour de rôle. C'est justement la faiblesse que le DQN
exploite : il arbitre selon les files observées au lieu d'un critère local.

## Note sur la sélection du meilleur modèle

`dqn_best.pt` était initialement sélectionné sur le retour cumulé de l'épisode.
Ce critère est vide de sens ici : la récompense étant `(W_avant − W_après)/100`,
sa somme sur un épisode se télescope en `(W_initial − W_final)/100`, soit du
bruit autour de 0. Le modèle ainsi retenu (≈ épisode 50) mesuré à −32.3 %
seulement, contre −50.7 % pour le checkpoint final. Corrigé dans `train.py` :
sélection sur l'attente moyenne, et uniquement une fois epsilon au plancher.
Le fichier `dqn_best.pt` a été remplacé par le checkpoint de l'épisode 150.

## Reproduire

```
py -3.14 -m rl.smoke_test                          # vérifie que l'agent pilote le feu
py -3.14 -m rl.train --episodes 150
py -3.14 -m rl.evaluate --model outputs/dqn_best.pt
```
