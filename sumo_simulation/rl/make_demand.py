"""Génère une demande de trafic dédiée au carrefour étudié.

Sans cela, la demande OSM par défaut (469 véh/h dispersés sur toute la ville,
dont 12 seulement empruntent notre carrefour) laisse l'intersection en
écoulement libre : file moyenne ~2 véhicules, vitesse ~59 km/h. Aucun
contrôleur ne peut se distinguer d'un autre dans ces conditions.

On construit donc des flux :
  - concentrés sur les 4 branches du carrefour ;
  - asymétriques (l'axe Nord-Sud est deux fois plus chargé que l'Est-Ouest),
    afin qu'une répartition égale du temps de vert soit sous-optimale et que
    l'agent ait un gain réel à trouver ;
  - variables dans le temps (montée en charge puis reflux), pour qu'un cycle
    fixe unique ne puisse pas convenir à tout l'épisode.

    py -3.14 -m rl.make_demand --seed 1 --out demand_s1.rou.xml
"""

import argparse
import os
import random

from . import config as C

# Branches entrantes -> sorties possibles (relevées dans osm.net.xml.gz).
BRANCHES = {
    "638957274":   ["638957273", "638957276#1", "534681995#1", "638957270"],
    "168308879#2": ["534681995#1", "638957270", "638957273", "638957276#1"],
    "638957277#0": ["638957276#1", "638957273", "534681995#1", "638957270"],
    "638957269":   ["638957270", "534681995#1", "638957273", "638957276#1"],
}

# Axe majeur (chargé) et axe mineur : crée l'asymétrie à exploiter.
MAJOR = ["638957274", "638957277#0"]

# Profil temporel : (début, fin, facteur de charge)
PROFILE = [(0, 900, 0.6), (900, 2400, 1.0), (2400, 3600, 0.5)]

# Débit de base par branche, en véhicules/heure.
BASE_FLOW = 400


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=str, required=True)
    ap.add_argument("--duration", type=int, default=C.EPISODE_LEN)
    ap.add_argument("--scale", type=float, default=1.0,
                    help="multiplicateur global de la demande")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    path = args.out if os.path.isabs(args.out) else os.path.join(C.SIM_DIR, args.out)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">',
        '    <vType id="car" accel="2.6" decel="4.5" sigma="0.5" length="5"'
        ' minGap="2.5" maxSpeed="16.7" speedDev="0.1"/>',
    ]

    fid = 0
    for begin, end, factor in PROFILE:
        if begin >= args.duration:
            break
        end = min(end, args.duration)
        for src, dests in BRANCHES.items():
            weight = 1.0 if src in MAJOR else 0.5
            # +/-15 % de variation par graine, pour que les épisodes diffèrent.
            jitter = rng.uniform(0.85, 1.15)
            total = BASE_FLOW * weight * factor * jitter * args.scale
            # Répartition des mouvements : tout droit majoritaire.
            for dest, share in zip(dests, (0.55, 0.25, 0.15, 0.05)):
                veh_h = total * share
                if veh_h < 1:
                    continue
                lines.append(
                    f'    <flow id="f{fid}" type="car" from="{src}" to="{dest}"'
                    f' begin="{begin}" end="{end}" vehsPerHour="{veh_h:.0f}"'
                    f' departLane="best" departSpeed="max"/>'
                )
                fid += 1

    lines.append("</routes>")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"{fid} flux écrits dans {path}")


if __name__ == "__main__":
    main()
