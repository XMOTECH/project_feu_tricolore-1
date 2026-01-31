import turtle

class Vehicle:
    def __init__(self, id_veh, spawn_x, spawn_y):
        self.id = id_veh
        self.x = spawn_x
        self.y = spawn_y
        self.max_speed = 3  # Vitesse de croisière
        self.current_speed = self.max_speed
        
        # Création graphique
        self.shape = turtle.Turtle()
        self.shape.shape("square")
        self.shape.shapesize(stretch_wid=1, stretch_len=2)
        self.shape.color("blue")
        self.shape.penup()
        self.shape.goto(self.x, self.y)
    
    def move(self):
        """Avance selon la vitesse actuelle."""
        self.x += self.current_speed
        self.shape.setx(self.x)
        
        # Reset position pour tester en boucle (téléportation au début)
        if self.x > 400:
            self.x = -400
            self.current_speed = self.max_speed # Réinitialise la vitesse

    def check_traffic_light(self, light_state, light_x):
        """Décision : Doit-on s'arrêter ?"""
        # Distance de sécurité (avant le feu)
        dist_to_light = light_x - self.x
        
        # Conditions d'arrêt :
        # 1. Le feu est Rouge ou Orange
        # 2. La voiture est DEVANT le feu (dist > 0)
        # 3. La voiture est PROCHE du feu (dist < 100 pixels)
        should_stop = (light_state in ["ROUGE", "ORANGE"]) and (0 < dist_to_light < 100)
        
        if should_stop:
            self.current_speed = 0 # Arrêt
        elif light_state == "VERT":
            self.current_speed = self.max_speed # Redémarrage

class VehicleManager:
    def __init__(self):
        self.vehicles = []

    def spawn_vehicle(self):
        pass

    def update_vehicles(self, traffic_light):
        """Met à jour toutes les voitures en leur donnant l'état du feu."""
        for v in self.vehicles:
            # On passe l'état du feu et sa position X (ici 0 pour le centre)
            v.check_traffic_light(traffic_light.state, traffic_light.x)
            v.move()