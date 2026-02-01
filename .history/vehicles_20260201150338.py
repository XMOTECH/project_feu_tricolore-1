import turtle
import random
import os
import math


# Directions possibles (Nomenclature : Direction du flux)
# spawn_x/y : point de départ
# heading : orientation initiale
# lane_offset : coordonnée constante de la voie (ex: y=-35 pour EST)
DIRECTIONS = {
    "EST": {"spawn_x": -600, "spawn_y": -35, "heading": 0, "lane_offset": -35, "oncoming": "OUEST"},
    "OUEST": {"spawn_x": 600, "spawn_y": 35, "heading": 180, "lane_offset": 35, "oncoming": "EST"},
    "NORD": {"spawn_x": 35, "spawn_y": -600, "heading": 90, "lane_offset": 35, "oncoming": "SUD"},
    "SUD": {"spawn_x": -35, "spawn_y": 600, "heading": 270, "lane_offset": -35, "oncoming": "NORD"}
}

def register_vehicle_shapes(screen):
    """Enregistre toutes les formes de véhicules (Jour/Nuit, Normal/Freinage)."""

    def add_car_base(shape, color_roof="#b3e5fc", color_body="gray"):
        shape.addcomponent(((-12,-14), (-10,-14), (-10,-4), (-12,-4)), "black", "black") # Pneus AR
        shape.addcomponent(((10,-14), (12,-14), (12,-4), (10,-4)), "black", "black")
        shape.addcomponent(((-12,6), (-10,6), (-10,16), (-12,16)), "black", "black") # Pneus AV
        shape.addcomponent(((10,6), (12,6), (12,16), (10,16)), "black", "black")
        shape.addcomponent(((-10,-18), (10,-18), (10,14), (6,22), (-6,22), (-10,14)), color_body, "black") # Corps
        shape.addcomponent(((-7,-10), (7,-10), (7,8), (4,12), (-4,12), (-7,8)), color_roof, "black") # Toit

    def add_car_lights(shape, color="white"):
        shape.addcomponent(((-9,18), (-5,18), (-5,22), (-9,22)), color, "black" if color=="white" else color)
        shape.addcomponent(((5,18), (9,18), (9,22), (5,22)), color, "black" if color=="white" else color)

    def add_brakes(shape, y_pos=-18):
        shape.addcomponent(((-9,y_pos), (-5,y_pos), (-5,y_pos+3), (-9,y_pos+3)), "red", "red")
        shape.addcomponent(((5,y_pos), (9,y_pos), (9,y_pos+3), (5,y_pos+3)), "red", "red")

    def add_blinkers(shape, side, y_front=18, y_rear=-18, height=3, width=4):
        """Ajoute des clignotants rouges (AV/AR)."""
        x_left, x_right = -9, 5
        if side == "LEFT":
            # AR G
            shape.addcomponent(((x_left, y_rear), (x_left+width, y_rear), (x_left+width, y_rear+height), (x_left, y_rear+height)), "red", "red")
            # AV G
            shape.addcomponent(((x_left, y_front), (x_left+width, y_front), (x_left+width, y_front+height), (x_left, y_front+height)), "red", "red")
        elif side == "RIGHT":
            # AR D
            shape.addcomponent(((x_right, y_rear), (x_right+width, y_rear), (x_right+width, y_rear+height), (x_right, y_rear+height)), "red", "red")
            # AV D
            shape.addcomponent(((x_right, y_front), (x_right+width, y_front), (x_right+width, y_front+height), (x_right, y_front+height)), "red", "red")

    # --- 1. VOITURES & 2. TAXIS ---
    for v_type in ["car", "taxi"]:
        for night in [False, True]:
            for braking in [False, True]:
                for blink in ["", "_left", "_right"]:
                    name = f"shape_{v_type}{'_night' if night else ''}{'_braking' if braking else ''}{blink}"
                    s = turtle.Shape("compound")
                    if v_type == "car":
                        add_car_base(s, color_roof="#1a237e" if night else "#b3e5fc")
                    else:
                        add_car_base(s, color_roof="black", color_body="#fbc02d")
                        s.addcomponent(((-4,-2), (4,-2), (4,2), (-4,2)), "white" if not night else "#ffeb3b", "black")
                    
                    if night: add_car_lights(s, color="white")
                    if braking: add_brakes(s)
                    
                    if blink == "_left": add_blinkers(s, "LEFT")
                    elif blink == "_right": add_blinkers(s, "RIGHT")
                    
                    screen.register_shape(name, s)

    # --- 3. MINIBUS ---
    def add_minibus_base(shape, color_body="gray"):
        shape.addcomponent(((-14,-22), (-12,-22), (-12,-12), (-14,-12)), "black", "black")
        shape.addcomponent(((12,-22), (14,-22), (14,-12), (12,-12)), "black", "black")
        shape.addcomponent(((-14,12), (-12,12), (-12,22), (-14,22)), "black", "black")
        shape.addcomponent(((12,12), (14,12), (14,22), (12,22)), "black", "black")
        shape.addcomponent(((-12,-28), (12,-28), (12,22), (9,30), (-9,30), (-12,22)), color_body, "black")
        shape.addcomponent(((-10,-20), (10,-20), (10,15), (7,22), (-7,22), (-10,15)), "#e0f7fa" if color_body=="gray" else "#546e7a", "black")

    for night in [False, True]:
        for braking in [False, True]:
            for blink in ["", "_left", "_right"]:
                name = f"shape_minibus{'_night' if night else ''}{'_braking' if braking else ''}{blink}"
                s = turtle.Shape("compound")
                add_minibus_base(s, color_body="#263238" if night else "gray")
                if night:
                    s.addcomponent(((-10,25), (-6,25), (-6,30), (-10,30)), "white", "white") # Phares AV
                    s.addcomponent(((6,25), (10,25), (10,30), (6,30)), "white", "white")
                if braking: 
                    s.addcomponent(((-11,-28), (-7,-28), (-7,-25), (-11,-25)), "red", "red")
                    s.addcomponent(((7,-28), (11,-28), (11,-25), (7,-25)), "red", "red")
                
                if blink == "_left":
                    # AR G
                    s.addcomponent(((-11,-28), (-7,-28), (-7,-25), (-11,-25)), "red", "red")
                    # AV G
                    s.addcomponent(((-10,25), (-6,25), (-6,30), (-10,30)), "red", "red")
                elif blink == "_right":
                    # AR D
                    s.addcomponent(((7,-28), (11,-28), (11,-25), (7,-25)), "red", "red")
                    # AV D
                    s.addcomponent(((6,25), (10,25), (10,30), (6,30)), "red", "red")
                
                screen.register_shape(name, s)

class Vehicle:
    def __init__(self, id_veh, origin_direction="EST", screen=None):
        self.id = id_veh
        self.origin = origin_direction
        self.current_direction = origin_direction
        
        # Choix aléatoire du TYPE
        # 70% Car, 10% Taxi, 20% Minibus
        type_roll = random.random()
        if type_roll < 0.7: 
            self.v_type = "CAR"
        elif type_roll < 0.8:
            self.v_type = "TAXI"
        else: 
            self.v_type = "MINIBUS"

        # Dimensions pour collision (offset capteur)
        self.length_offset = 22
        self.back_offset = 18 
        
        if self.v_type == "MINIBUS":
            self.length_offset = 30
            self.back_offset = 28

        self.front_offset = self.length_offset

        # Intention de virage
        r = random.random()
        if r < 0.6: self.turn_intention = "STRAIGHT"
        elif r < 0.8: self.turn_intention = "RIGHT"
        else: self.turn_intention = "LEFT"

        # Couleur persistante
        if self.v_type == "CAR":
            self.color = random.choice([
                "#e74c3c", "#3498db", "#2ecc71", "#ffffff", "#2c3e50", 
                "#95a5a6", "#9b59b6", "#e67e22", "#1abc9c", "#f1c40f",
                "#d35400", "#c0392b", "#2980b9", "#27ae60", "#7f8c8d"
            ])
        elif self.v_type == "MINIBUS":
            self.color = random.choice([
                "#f57c00", "#7b1fa2", "#00796b", "#455a64", "#5d4037", 
                "#d32f2f", "#1976d2", "#388e3c", "#fbc02d", "#8e24aa",
                "#00acc1", "#c0ca33", "#fb8c00", "#546e7a"
            ])
        else: # TAXI
            self.color = "#fbc02d"
        
        config = DIRECTIONS[origin_direction]
        self.x = config["spawn_x"]
        self.y = config["spawn_y"]
        self.heading = config["heading"]
        
        self.max_speed = 4
        if self.v_type == "MINIBUS": self.max_speed = 3.5
        
        self.current_speed = self.max_speed
        self.is_active = True
        self.has_turned = False
        self.is_turning = False
        self.target_heading = self.heading
        self.night_mode = False 
        
        self.is_braking = False
        self.blink_timer = 0
        self.blink_state = False 
        self.blink_interval = 12 
        
        self.shape = turtle.Turtle()
        self.shape.speed(0)
        self.shape.penup()
        
        if screen:
            pass 
            
        self._apply_visuals()
        
        self.shape.goto(self.x, self.y)
        self.shape.setheading(self.heading)

    def toggle_night_mode(self, is_night):
        """Active/Désactive les phares."""
        self.night_mode = is_night
        self._apply_visuals()

    def _apply_visuals(self):
        """Applique la forme et la couleur selon le type, le mode nuit, le freinage et les clignotants."""
        suffix = "_night" if self.night_mode else ""
        if self.is_braking:
            suffix += "_braking"
        
        # Ajout du clignotant si actif
        if self.blink_state:
            if self.turn_intention == "LEFT": suffix += "_left"
            elif self.turn_intention == "RIGHT": suffix += "_right"
        
        if self.v_type == "CAR":
            self.shape.shape("shape_car" + suffix)
            self.shape.color(self.color if not self.night_mode else "#546e7a")
        elif self.v_type == "TAXI":
            self.shape.shape("shape_taxi" + suffix)
            self.shape.color("#fbc02d" if not self.night_mode else "#f9a825")
        elif self.v_type == "MINIBUS":
            self.shape.shape("shape_minibus" + suffix)
            self.shape.color(self.color if not self.night_mode else "#37474f")
        
        self.shape.goto(self.x, self.y)
        self.shape.setheading(self.heading)
    
    def move(self):
        """Déplace le véhicule et gère les virages arrondis et les clignotants."""
        if not self.is_active:
            return

        # Mise à jour des feux de freinage
        currently_stopping = (self.current_speed == 0)
        if currently_stopping != self.is_braking:
            self.is_braking = currently_stopping
            self._apply_visuals()

        # Logique des clignotants
        if not self.has_turned and self.turn_intention != "STRAIGHT":
            self.blink_timer += 1
            if self.blink_timer >= self.blink_interval:
                self.blink_timer = 0
                self.blink_state = not self.blink_state
                self._apply_visuals()
        elif self.blink_state: 
            self.blink_state = False
            self.blink_timer = 0
            self._apply_visuals()
            
        # Si vitesse nulle, pas de mouvement
        if self.current_speed == 0:
            return

        # Logique de virage progressif
        if not self.has_turned and self.turn_intention != "STRAIGHT":
            if not self.is_turning:
                self._check_turn_trigger()
            
            if self.is_turning:
                
                turn_step = 6 * (self.current_speed / self.max_speed) if self.max_speed > 0 else 6
                
                diff = (self.target_heading - self.heading + 180) % 360 - 180
                if abs(diff) <= turn_step:
                    self.heading = self.target_heading
                    self.is_turning = False
                    self.has_turned = True
                    self._align_to_lane()
                else:
                    self.heading += turn_step if diff > 0 else -turn_step
            
        # Mouvement selon le heading actuel
        rad = math.radians(self.heading)
        dx = math.cos(rad) * self.current_speed
        dy = math.sin(rad) * self.current_speed
        
        self.x += dx
        self.y += dy
        
        self.shape.goto(self.x, self.y)
        self.shape.setheading(self.heading)
        
        # Désactivation si hors limites
        if abs(self.x) > 650 or abs(self.y) > 650:
            self.deactivate()

    def _check_turn_trigger(self):
        """Déclenche le virage au bon moment pour une trajectoire courbe et éviter l'îlot central."""
        # Pour v=4, le rayon de braquage R est d'environ 38 pixels.
        # Pour v=3.5 (minibus), R est d'environ 33 pixels.
        # On ajuste les seuils pour atterrir dans la voie (abs=35) tout en contournant l'îlot (r=22).
        
        start_turn = False
        
        if self.origin == "EST": 
            if self.turn_intention == "LEFT": 
                if self.x >= -3: start_turn = True; self.target_heading = 90; self.current_direction = "NORD"
            elif self.turn_intention == "RIGHT": 
                if self.x >= -73: start_turn = True; self.target_heading = 270; self.current_direction = "SUD"

        elif self.origin == "OUEST": 
            if self.turn_intention == "LEFT": 
                if self.x <= 3: start_turn = True; self.target_heading = 270; self.current_direction = "SUD"
            elif self.turn_intention == "RIGHT": 
                if self.x <= 73: start_turn = True; self.target_heading = 90; self.current_direction = "NORD"

        elif self.origin == "NORD": 
            if self.turn_intention == "LEFT": 
                if self.y >= -3: start_turn = True; self.target_heading = 180; self.current_direction = "OUEST"
            elif self.turn_intention == "RIGHT": 
                if self.y >= -73: start_turn = True; self.target_heading = 0; self.current_direction = "EST"

        elif self.origin == "SUD": 
            if self.turn_intention == "LEFT":
                if self.y <= 3: start_turn = True; self.target_heading = 0; self.current_direction = "EST"
            elif self.turn_intention == "RIGHT":
                if self.y <= 73: start_turn = True; self.target_heading = 180; self.current_direction = "OUEST"
        
        if start_turn:
            self.is_turning = True

    def _align_to_lane(self):
        """Recale le véhicule sur le centre de sa nouvelle voie."""
        offset = DIRECTIONS[self.current_direction]["lane_offset"]
        if self.current_direction in ["EST", "OUEST"]:
            self.y = offset
        else:
            self.x = offset

    def deactivate(self):
        self.is_active = False
        self.shape.hideturtle()

    def check_traffic_light(self, light_state, light_pos):
        if not self.is_active or self.has_turned:
            return
            
        should_stop = False
        stop_margin = 15
        front_offset = self.front_offset
        
        # Calcul de la distance au feu
        dist = 9999
        if self.origin == "EST":
            front_x = self.x + front_offset
            dist = light_pos - front_x
        elif self.origin == "OUEST":
            front_x = self.x - front_offset
            dist = front_x - light_pos
        elif self.origin == "NORD":
            front_y = self.y + front_offset
            dist = light_pos - front_y
        elif self.origin == "SUD":
            front_y = self.y - front_offset
            dist = front_y - light_pos
            
        # Si on a passé le feu, on ne s'arrête plus
        if dist < -15: 
            return

        if (light_state in ["ROUGE", "ORANGE"]) and (0 < dist < stop_margin):
            self.current_speed = 0

    def check_priority(self, vehicles):
        """Gère la priorité pour le virage à gauche."""
        if not self.is_active or self.has_turned:
            return

        if self.turn_intention == "LEFT":
            oncoming_dir = DIRECTIONS[self.origin]["oncoming"]
            
            for v in vehicles:
                if not v.is_active or v.id == self.id:
                    continue
                
                if v.origin == oncoming_dir:
                    if v.turn_intention == "LEFT":
                        continue
                        
                    # On ignore ceux qui se sont déjà éloignés
                    passed = False
                    if v.origin == "EST" and v.x > 30: passed = True
                    elif v.origin == "OUEST" and v.x < -30: passed = True
                    elif v.origin == "NORD" and v.y > 30: passed = True
                    elif v.origin == "SUD" and v.y < -30: passed = True
                    if passed: continue

                    dist_sq = v.x**2 + v.y**2
                    my_dist_sq = self.x**2 + self.y**2
                    
                    # Si on est déjà très au centre, on dégage (Anti-blocage)
                    if my_dist_sq < 70**2:
                        return

                    # Sinon on attend s'il y a du monde en face
                    if dist_sq < 250**2 and my_dist_sq < 160**2:
                        self.current_speed = 0
                        return

    def check_vehicle_ahead(self, vehicles):
        """Détection de collision géométrique avec filtrage de trajectoire."""
        if not self.is_active:
            return
            
        rad_heading = math.radians(self.heading)
        # On réduit la portée du capteur pour éviter les faux positifs en virage
        sensor_x = self.x + math.cos(rad_heading) * 30 
        sensor_y = self.y + math.sin(rad_heading) * 30 
        
        # Rayon très serré pour les collisions latérales
        safety_radius = 22 
        
        for v in vehicles:
            if v.id == self.id or not v.is_active:
                continue
                
            dx = v.x - self.x
            dy = v.y - self.y
            dist_sq = dx**2 + dy**2
            
            # Si le véhicule est derrière nous, on ignore totalement
            dot = dx * math.cos(rad_heading) + dy * math.sin(rad_heading)
            if dot < 0: continue
            
            # Vérification de proximité immédiate (sensor)
            sensor_dist_sq = (v.x - sensor_x)**2 + (v.y - sensor_y)**2
            if sensor_dist_sq < safety_radius**2:
                # Si on est en "Clear the Box" (au centre), on est plus agressif
                if self.x**2 + self.y**2 < 80**2:
                    # On ne s'arrête que si c'est VRAIMENT une collision même trajectoire
                    if abs(-dx * math.sin(rad_heading) + dy * math.cos(rad_heading)) < 15:
                        self.current_speed = 0
                        return
                else:
                    self.current_speed = 0
                    return
            
            # File d'attente sur la même voie
            # Calcul de la distance d'arrêt souhaitée : mon avant + son arrière + marge
            min_gap = 10
            stop_dist = self.front_offset + v.back_offset + min_gap
            slow_dist = stop_dist + 30

            if v.current_direction == self.current_direction and dot < slow_dist:
                lat_dist = abs(-dx * math.sin(rad_heading) + dy * math.cos(rad_heading))
                if lat_dist < 20:
                     self.current_speed = min(self.current_speed, v.current_speed)
                     if dot < stop_dist: 
                         self.current_speed = 0
                     return

    def check_intersection_speed(self):
        """Réduit la vitesse si le véhicule est dans le carrefour."""
        # Zone de l'intersection (approx -140 à 140 sur les deux axes)
        if abs(self.x) < 140 and abs(self.y) < 140:
            # Réduit à 60% de la vitesse max
            self.current_speed = self.max_speed * 0.6

class VehicleManager:
    def __init__(self, screen=None, logger=None):
        self.vehicles = []
        self.next_id = 1
        self.spawn_timer = 0
        self.spawn_interval = 80
        self.screen = screen
        self.logger = logger
        self.night_mode = False
        if screen: register_vehicle_shapes(screen)
        
    def toggle_night_mode(self, is_night):
        """Bascule le mode de tous les véhicules."""
        self.night_mode = is_night
        for v in self.vehicles:
            v.toggle_night_mode(is_night)

    def spawn_vehicle(self, direction=None):
        if direction is None:
            direction = random.choice(list(DIRECTIONS.keys()))
        new_vehicle = Vehicle(self.next_id, direction, self.screen)
        new_vehicle.toggle_night_mode(self.night_mode)
        self.vehicles.append(new_vehicle)
        
        if self.logger:
            self.logger.log_event("VEHICLE", f"Entrée véhicule {new_vehicle.id}", 
                                   None, "Simulation", vehicle=new_vehicle)
            
        self.next_id += 1
        return new_vehicle

    def auto_spawn(self):
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self.spawn_vehicle()

    def cleanup_inactive(self):
        self.vehicles = [v for v in self.vehicles if v.is_active]

    def update_vehicles(self, intersection_controller):
        self.auto_spawn()
        
        for v in self.vehicles:
            if not v.is_active:
                continue
            
            # Sauvegarde de l'état précédent pour le log
            was_stopped = (v.current_speed == 0)
            
            # RESET SYSTÉMATIQUE: On part du principe qu'on veut avancer
            v.current_speed = v.max_speed
            
            # Réduction de vitesse en intersection
            v.check_intersection_speed()
            
            # Application des freins (dans l'ordre d'importance)
            if not v.has_turned:
                light_state = intersection_controller.get_light_state(v.origin)
                light_pos = intersection_controller.get_stop_position(v.origin)
                v.check_traffic_light(light_state, light_pos)
            
            v.check_priority(self.vehicles)
            v.check_vehicle_ahead(self.vehicles)
            
            is_stopped = (v.current_speed == 0)
            
            # Logique de log sur changement d'état (arrêt/départ)
            if self.logger:
                if is_stopped and not was_stopped:
                    # On cherche la cause de l'arrêt pour le log
                    cause = "Obstacle/Priority"
                    if not v.has_turned:
                        ls = intersection_controller.get_light_state(v.origin)
                        if ls in ["ROUGE", "ORANGE"]: cause = f"Feu {ls}"
                    
                    self.logger.log_event("VEHICLE", f"Véhicule {v.id} Arrivé/Arrêté ({cause})", 
                                           None, "Simulation", vehicle=v)
                elif was_stopped and not is_stopped:
                    self.logger.log_event("VEHICLE", f"Véhicule {v.id} Redémarrage", 
                                           None, "Simulation", vehicle=v)

            v.move()
            
            # Log de sortie
            if not v.is_active and self.logger:
                self.logger.log_event("VEHICLE", f"Sortie véhicule {v.id}", 
                                       None, "Simulation", vehicle=v)
        
        self.cleanup_inactive()

    def get_vehicle_count(self):
        return len([v for v in self.vehicles if v.is_active])