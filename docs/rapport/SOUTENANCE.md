# Fiche de soutenance — régulation de feux par DQN

Une page à avoir sous les yeux. Tous les chiffres ont été revérifiés le 10 août par
réexécution de `rl.evaluate` et `rl.adaptivity`.

## 1. Ce que fait le projet, en trois phrases

Un agent de Deep Q-Learning régule un carrefour réel de Thiès sous SUMO. Il
observe un vecteur de 13 réels (4 files, 4 densités, phase courante en one-hot,
indicateur min_green) et choisit **l'indice de la prochaine phase verte** parmi 4,
les actions non conformes aux contraintes de sécurité étant masquées. Il est
récompensé par la réduction du temps d'attente cumulé : `r = (W_avant − W_après)/100`.

## 2. Le résultat central

Face au feu fixe en place, sur **5 graines de trafic jamais vues à l'entraînement** :

| | fixe (feu actuel) | actué | **DQN** |
|---|---|---|---|
| temps perdu / véh. | 31,5 ± 0,5 s | 34,2 ± 1,1 s | **15,5 ± 0,6 s (−50,7 %)** |
| attente / véh. | 23,8 ± 0,4 s | 25,8 ± 0,8 s | **9,0 ± 0,5 s (−62,2 %)** |
| durée de trajet | 48,5 s | 51,2 s | **32,7 s** |
| vitesse effective | 6,37 m/s | 5,72 m/s | **8,16 m/s** |

`tripinfo.xml`, épisodes de 3600 s, ~850–900 véhicules écoulés, **moins de 1 %
d'écart de débit** entre contrôleurs — les trois évacuent la même demande, donc la
comparaison porte sur la qualité de régulation, pas sur un débit différent.

### Et le gain ne sacrifie personne

Objection classique : « une moyenne s'améliore en pénalisant une minorité ». Vérifié
sur la distribution complète (4 386 véhicules) :

| | moyenne | médiane | p90 | p99 | **max** |
|---|---|---|---|---|---|
| fixe | 23,8 s | 20 s | 55 s | 89 s | 127 s |
| actué | 25,8 s | 24 s | 53 s | 76 s | 136 s |
| **DQN** | **9,0 s** | **5 s** | **25 s** | **45 s** | **89 s** |

Le DQN domine à **tous** les quantiles. Le véhicule le plus pénalisé attend 89 s contre
127 s sous le feu fixe : le pire cas s'améliore de 30 % **en même temps** que la
moyenne. Aucun report sur une minorité.

## 3. La preuve que l'agent est bien adaptatif

C'est la question qui vient forcément : « 215 changements par épisode, c'est très
régulier — vous n'avez pas juste ré-appris un cycle fixe ? »

Mesuré par `rl/adaptivity.py` sur 5 graines (1083 verts pour le DQN, 795 pour le fixe) :

| test | fixe | actué | **DQN** |
|---|---|---|---|
| écart-type intra-phase de la durée de vert | **0,00 s** | 1,38 s | **3,53 s** |
| plage des durées | 12–33 s | 14–44 s | **15–55 s** |
| choix de la phase la plus chargée quand permis | n/a | n/a | **79,2 %** (hasard : 25 %) |

**L'écart-type intra-phase est l'argument décisif.** Un cycle fixe donne
rigoureusement 0,00 s — c'est sa signature mathématique. Le DQN module la durée
d'une même phase de 15 à 55 s selon l'état observé. L'hypothèse du cycle fixe est
donc réfutée par la mesure, pas seulement par l'absurde.

### Le piège à désamorcer avant qu'il soit tendu

La corrélation « file à l'ouverture → durée de vert » vaut **+0,54 sur le contrôleur
fixe**. Un feu strictement statique semble donc « réagir » au trafic ! Explication :
les phases de l'axe majeur ont à la fois plus de vert (33 s contre 12 s) et plus de
file. La corrélation capte la topologie du cycle, pas une réaction. **Cette
corrélation est donc écartée comme non valide**, et c'est un point à présenter
soi-même — un jury qui le trouve après toi coûte plus cher que le fait de l'avouer.

## 4. La découverte : l'agent abandonne une phase

Le DQN n'ouvre **jamais** la phase 1 (0 vert sur 1083 observés ; 410 / 451 / 222 sur
les phases 0, 2, 3). Ce n'est pas un bug, et l'analyse du réseau l'explique :

| phase | liens verts | ce qu'elle sert |
|---|---|---|
| 0 | 10 liens | axe majeur, tout droit `G` **+ tourne-à-gauche permissif `g`** |
| **1** | **4 liens** | **uniquement les tourne-à-gauche, en protégé `G`** |
| 2 | 6 liens | axe secondaire, tout droit |
| 3 | 4 liens | tourne-à-gauche de l'axe secondaire, protégé |

La phase 1 est un **sous-ensemble strict de la phase 0** : tous ses mouvements y sont
déjà autorisés, en permissif au lieu de protégé. L'agent a donc découvert qu'elle est
redondante en capacité, et il récupère ses ~12 s de vert au profit des mouvements qui
en ont besoin. C'est un vrai résultat d'optimisation, pas un artefact.

**Mais il faut en énoncer le coût** : passer un tourne-à-gauche de protégé à permissif
reporte la résolution du conflit sur le conducteur, qui doit chercher un créneau. En
simulation SUMO cela fonctionne (2 freinages d'urgence sur 5 épisodes) ; sur le
terrain, c'est un choix qui relève de l'ingénieur sécurité, pas de l'agent. Une
contrainte d'équité par mouvement (garantir un vert protégé périodique) serait la
correction à apporter avant tout déploiement.

## 5. Les limites — à énoncer avant qu'on les demande

1. **Un seul entraînement.** L'écart-type reporté mesure la variabilité du *trafic*,
   pas celle de l'*apprentissage*. Il faudrait 3 à 5 runs avec des graines
   d'initialisation différentes.
2. **Carrefour isolé.** Fluidifier un carrefour peut déplacer la congestion vers le
   suivant. Rien n'est démontré en réseau.
3. **La métrique de vitesse par voie est trompeuse.** `getLastStepMeanSpeed` renvoie
   la vitesse *autorisée* sur une voie vide : les 51 km/h du journal d'entraînement
   mesurent en partie l'absence de trafic. D'où l'usage de `tripinfo.xml` (vitesse
   par véhicule) pour toute conclusion.
4. **Équité par mouvement non contrôlée** (voir §4).
5. **Écart au terrain.** SUMO modélise un trafic homogène de voitures ; Thiès a des
   deux-roues, des charrettes et des piétons hors passage.

## 6. Le défaut qu'on a trouvé et corrigé

C'est le meilleur moment de la soutenance, à raconter volontairement.

Le critère de sélection du « meilleur modèle » était le retour cumulé de l'épisode.
Or la récompense est une différence, donc sa somme se télescope :

```
Σ (W_{t-1} − W_t)/100  =  (W_0 − W_T)/100
```

soit une quantité qui ne dépend que des états initial et final — du bruit autour de
zéro. Le critère ne sélectionnait rien. Le modèle qu'il retenait (vers l'épisode 50)
atteignait **−32,3 %** au lieu du **−50,7 %** du modèle final. Remplacé par l'attente
moyenne de l'épisode, évaluée seulement une fois `ε` au plancher.

Leçon transférable : une métrique de sélection non vérifiée peut faire publier un
modèle nettement inférieur à celui dont on dispose, **sans aucun signal d'erreur**.

## 7. Pourquoi le feu actionné perd contre le feu fixe

Contre-intuitif, donc on va te le demander. La logique actionnée prolonge le vert sur
un critère **local** : « des véhicules arrivent-ils encore sur cette branche ? ». L'axe
majeur étant chargé 2× plus, son vert va systématiquement jusqu'à `maxDur` et l'axe
secondaire est affamé. Le feu fixe est moins réactif mais garantit un tour de rôle.

Confirmé par la mesure : chez `actué`, la durée du vert **augmente** avec la pression
sur les autres branches (r = +0,36) — l'inverse du comportement souhaitable. Chez
`fixe`, r = −0,24 par simple effet du cycle.

Le DQN échappe à ce piège parce que son état contient les **quatre** files
simultanément : il arbitre au lieu de réagir localement.

## 8. Si tu peux montrer quelque chose

```bash
cd sumo_simulation
py -3.14 -m rl.demo --controller fixe --seed 7 --episode-len 600 --scale 1.4
py -3.14 -m rl.demo --controller dqn  --seed 7 --episode-len 600 --scale 1.4
```

Même graine, même trafic, seul le contrôleur change. **Mettre « Delay » à 150 ms**
dans la barre d'outils, sinon ça défile trop vite pour être commenté.

À l'écran : avec le feu fixe, une file s'accumule sur l'axe chargé pendant que la
transversale reste vide au vert. Le DQN écourte les verts inutiles.

## 9. Reproduire

```bash
py -3.14 -m rl.smoke_test                             # l'agent tient-il le feu ?
py -3.14 -m rl.train --episodes 150                   # ~45 min
py -3.14 -m rl.evaluate --model outputs/dqn_best.pt   # tableau comparatif, ~10 min
py -3.14 -m rl.adaptivity --seeds 7 13 21 42 77       # preuve d'adaptativité
```

`smoke_test` vérifie le point technique le plus facile à rater : l'agent commande
par `setRedYellowGreenState()` et non `setPhase()`, ce dernier réarmant la durée
programmée — SUMO reprendrait alors son cycle tout seul pendant que l'agent croit
piloter. Test : le feu est laissé 60 s sans ordre et ne bouge pas, là où le programme
statique aurait basculé à 27 s.

## Piège de reproductibilité (à connaître si on te demande de relancer)

`outputs/` est écrasé à chaque exécution : `rl.train` réécrit `training_log.csv` depuis
zéro et `rl.evaluate` remplace les `tripinfo_*.xml`. Un fichier présent sur le disque
ne correspond donc **pas nécessairement** au modèle courant.

C'est arrivé pendant la préparation : des `tripinfo` antérieurs au remplacement de
`dqn_best.pt` donnaient −32,3 % au lieu de −50,7 %. Vérifié par réexécution complète le
10 août — le rapport est juste, les fichiers étaient périmés. **Toujours relancer
`rl.evaluate` plutôt que relire les fichiers existants.**

Si le professeur demande de reproduire devant lui : prévoir ~10 min pour `rl.evaluate`
(15 simulations de 3600 s), ou restreindre avec `--seeds 7`.
