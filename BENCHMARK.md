# 📊 Benchmark Expérimental et État de l'Art — Régulation de Trafic

**Projet :** Régulation Intelligente de Trafic Routier par Deep Q-Network (DQN) sous Eclipse SUMO  
**Auteur :** Mamadou Ahmadou Ka (Licence 1 Informatique — Université Iba Der Thiam de Thiès, Sénégal)  
**Date :** Septembre 2026  
**Environnement :** Carrefour réel de Thiès (Données OpenStreetMap, 8 voies d'approche, 4 phases vertes)

---

## 1. Introduction & Objectifs du Benchmark

L'objectif de ce document est de dresser une **comparaison scientifique et empirique rigoureuse** entre notre agent d'Apprentissage par Renforcement Profond (**Double DQN**) et les principales approches de référence issues de la littérature des transports et de l'état de l'art mondial :

1. **Contrôleur Statique (`fixe`)** : Plan à temps fixe pré-programmé (référence minimale).
2. **Contrôleur Actionné (`actue`)** : Régulation réactive par détection de passage / *gap-out*.
3. **Max-Pressure (`mp`)** : Algorithme théorique de référence (Varaiya, 2013) optimisant la pression instantanée des files d'attente.
4. **Double DQN (`dqn`)** : Notre agent de Deep Reinforcement Learning entraîné sur Processus de Décision Markovien (MDP à 13 dimensions).

---

## 2. Protocole Expérimental

Afin de garantir une **parfaite équité scientifique** (*ceteris paribus*), tous les contrôleurs sont évalués selon les règles strictes suivantes :

* **Moteur de simulation :** Eclipse SUMO (v1.27.0) sans téléportation (`--time-to-teleport -1`).
* **Jeu de graines (*Seeds*) :** $5$ graines pseudo-aléatoires distinctes ($\text{SEED\_EVAL} = [7, 13, 21, 42, 77]$).
* **Durée des simulations :** $3600\text{ secondes}$ (1 heure de trafic continu par test, soit 20 heures simulées au total).
* **Contraintes de sécurité :** Mêmes durées minimales de vert ($\text{MIN\_GREEN} = 10\text{ s}$), maximales ($\text{MAX\_GREEN} = 60\text{ s}$), temps de décision ($\text{DELTA\_TIME} = 5\text{ s}$) et temps jaune de transition ($\text{YELLOW\_TIME} = 3\text{ s}$).
* **Source des métriques :** Fichiers standards `tripinfo.xml` générés nativement par SUMO.

---

## 3. Résultats Expérimentaux Globaux (Campagne 5 graines $\times$ 3600 s)

Les métriques sont moyennées sur les 5 graines (moyenne $\pm$ écart-type inter-graines) :

| Contrôleur | `timeLoss` (s) | `waitingTime` (s) | Durée trajet (s) | Vitesse ($m/s$) | Véhicules servis ($n$) | Écart / Fixe |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`fixe`** | $31{,}5 \pm 0{,}5$ | $23{,}8 \pm 0{,}4$ | $48{,}5$ | $6{,}37$ | $\sim 872$ | Référence ($0\,\%$) |
| **`actue`** | $34{,}2 \pm 1{,}1$ | $25{,}8 \pm 0{,}8$ | $51{,}2$ | $5{,}72$ | $\sim 874$ | $+8{,}7\,\%$ |
| **`mp` (somme brute)** | $71{,}7 \pm 15{,}2$ | $57{,}3 \pm 12{,}6$ | $86{,}6$ | $4{,}12$ | $\sim 580$ | $+127{,}7\,\%$ |
| **`mp` (mode `max`)** | $45{,}7 \pm 3{,}2$ | $37{,}7 \pm 2{,}9$ | $63{,}2$ | $6{,}65$ | $\sim 798$ | $+41{,}5\,\%$ |
| **`dqn` (Notre IA)** | **$15{,}5 \pm 0{,}6$** | **$9{,}0 \pm 0{,}5$** | **$32{,}7$** | **$8{,}16$** | **$\sim 889$** | 🚀 **$-50{,}7\,\%$** |

---

## 4. Diagnostic Approfondi de l'Algorithme Max-Pressure (Varaiya, 2013)

### A. Constat Initial
L'implémentation naïve de Max-Pressure ($\arg\max$ sur la somme des files) présentait une dégradation anormale ($+128\,\%$ de `timeLoss`) et une chute de $34\,\%$ du débit de véhicules. Un diagnostic approfondi a été mené sur la graine 7 :

| Contrôleur | Commutations (`switches`) | Ph0 (Axe 1) | Ph1 (Tourne-G 1) | Ph2 (Axe 2) | Ph3 (Tourne-G 2) | Débit ($n$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`fixe`** | 159 | $1080\text{ s}$ ($41\%$) | $240\text{ s}$ ($9\%$) | $1080\text{ s}$ ($41\%$) | $240\text{ s}$ ($9\%$) | $843$ |
| **`dqn`** | **210** | **$1495\text{ s}$ ($41{,}5\%$)** | **$0\text{ s}$ ($0\%$)** | **$1445\text{ s}$ ($40{,}1\%$)** | **$660\text{ s}$ ($18{,}3\%$)** | **$849$ (100 %)** |
| **`mp` (naïf)** | **91** (très bas) | $690\text{ s}$ ($19{,}2\%$) | $0\text{ s}$ ($0\%$) | **$2910\text{ s}$ ($80{,}8\%$)** | **$0\text{ s}$ ($0\%$)** | $559$ ($-34\%$) |

### B. Conclusions du Diagnostic
1. **Élimination de l'hypothèse de *Thrashing* :** Avec seulement 91 changements de feux, MP n'oscille pas trop vite.
2. **Identification du mécanisme de *Starvation* (Famine) :**  
   * Comme la Phase 2 comporte davantage de liens ouverts, sa somme de files domine mathématiquement.
   * La **Phase 3 reçoit $0{,}0\text{ seconde}$ de vert**, provoquant un blocage complet de la voie de tourne-à-gauche qui refoule en amont (*spillback*) et empêche $207$ véhicules d'entrer dans la simulation.
3. **Correctif apporté (Mode `max`) :**  
   * L'agrégation par file maximale ($\text{pression} = \max_{v \in S} x_v$) réduit la distorsion entre phases et fait remonter le débit à $798$ véhicules.

---

## 5. Pourquoi le Double DQN Surclasse les Baselines ?

1. **Anticipation vs Gloutonnerie :**  
   Contrairement à Max-Pressure qui réagit à l'instant présent, le DQN maximise l'espérance des récompenses futures (Équation de Bellman). Il apprend à accorder des fenêtres courtes mais régulières à la Phase 3 ($18{,}3\,\%$ du temps) pour vider les files secondaires avant qu'elles ne bloquent les artères majeures.
2. **Vision Continue (Files + Densités) :**  
   Le vecteur d'état à 13 dimensions intègre la densité de véhicules en mouvement, permettant d'anticiper les pelotons à pleine vitesse ($50\text{ km/h}$) avant qu'ils ne soient à l'arrêt.
3. **Pénalisation Naturelle des Pertes :**  
   La récompense différentielle $r = \frac{\Delta W}{100}$ intègre implicitement le coût des transitions jaunes de 3s, empêchant les commutations stériles.

---

## 6. Références Bibliographiques Fondamentales

1. **Day, C. M., Li, H., et al. (2016).** *Detector-Free Optimization of Traffic Signal Offsets with Connected Vehicle Data.* Transportation Research Record, 2620, 52–60.
2. **Varaiya, P. (2013).** *Max pressure control of a network of signalized intersections.* Transportation Research Part C: Emerging Technologies, 36, 177–195.
3. **Genders, W., & Razavi, S. (2016).** *Using deep reinforcement learning for traffic light control.* Transportation Research Record, 2620(1), 52–60.
4. **Wei, H., Zheng, G., Yao, H., & Li, Z. (2018).** *IntelliLight: A Reinforcement Learning Approach for Intelligent Traffic Light Control.* ACM SIGKDD 2018, 2496–2505.
5. **Wei, H., Chen, C., et al. (2019).** *PressLight: Learning Max-Pressure Traffic Signal Control for Urban Networks.* ACM SIGKDD 2019, 2653–2661.
