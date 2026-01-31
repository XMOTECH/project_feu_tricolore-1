from traffic_light import TrafficLight

class IntersectionController:
    """Contrôleur d'intersection avec 4 feux synchronisés."""
    
    def __init__(self):
        # Feux de circulation (Nomenclature : Direction du FLUX)
        self.lights = {
            "EST": TrafficLight(-100, -100, "EST", 0.7),   # Flux vers l'Est
            "OUEST": TrafficLight(100, 100, "OUEST", 0.7), # Flux vers l'Ouest
            "NORD": TrafficLight(100, -100, "NORD", 0.7),  # Flux vers le Nord
            "SUD": TrafficLight(-100, 100, "SUD", 0.7)     # Flux vers le Sud
        }
        
        # Positions d'arrêt (Flux Est s'arrête en -135, Flux Ouest en 135, etc.)
        self.stop_positions = {
            "EST": -135,   # X min
            "OUEST": 135,  # X max
            "NORD": -135,  # Y min
            "SUD": 135     # Y max
        }
        
        # Phase actuelle (A = Flux N-S actif, B = Flux E-W actif)
        self.current_phase = "A"
        self.timer = 0
        
        # Configuration des phases
        self.phases = {
            "A": {"NORD": "VERT", "SUD": "VERT", "EST": "ROUGE", "OUEST": "ROUGE"},
            "A_ORANGE": {"NORD": "ORANGE", "SUD": "ORANGE", "EST": "ROUGE", "OUEST": "ROUGE"},
            "B": {"NORD": "ROUGE", "SUD": "ROUGE", "EST": "VERT", "OUEST": "VERT"},
            "B_ORANGE": {"NORD": "ROUGE", "SUD": "ROUGE", "EST": "ORANGE", "OUEST": "ORANGE"}
        }
        
        # Durées des phases
        self.phase_durations = {
            "A": 100, "A_ORANGE": 40, "B": 100, "B_ORANGE": 40
        }
        
        # Séquence des phases
        self.phase_sequence = ["A", "A_ORANGE", "B", "B_ORANGE"]
        self.phase_index = 0
        
        # Appliquer la phase initiale
        self._apply_phase()
    
    def _apply_phase(self):
        """Applique l'état des feux selon la phase actuelle."""
        phase_states = self.phases[self.current_phase]
        for direction, state in phase_states.items():
            self.lights[direction].set_state(state)
            
    def redraw(self):
        """Force le redessin de tous les feux d'intersection."""
        for light in self.lights.values():
            light.redraw()
    
    def update(self, scenario):
        """Met à jour l'intersection selon le scénario."""
        scenario.update_intersection(self)
    
    def standard_update(self):
        """Mise à jour standard avec cycle automatique."""
        self.timer += 1
        
        limit = self.phase_durations.get(self.current_phase, 100)
        
        if self.timer >= limit:
            self.timer = 0
            self.phase_index = (self.phase_index + 1) % len(self.phase_sequence)
            self.current_phase = self.phase_sequence[self.phase_index]
            self._apply_phase()
    
    def night_mode_update(self):
        """Mode nuit : tous les feux clignotent orange."""
        self.timer += 1
        
        if self.timer >= 30:
            self.timer = 0
            for light in self.lights.values():
                if light.state == "ORANGE":
                    light.set_state("ETEINT")
                else:
                    light.set_state("ORANGE")
    
    def manual_change(self):
        """Changement manuel de phase."""
        self.timer = 0
        self.phase_index = (self.phase_index + 1) % len(self.phase_sequence)
        self.current_phase = self.phase_sequence[self.phase_index]
        self._apply_phase()
    
    def get_light_state(self, vehicle_direction):
        """Retourne l'état du feu pour une direction de véhicule."""
        return self.lights[vehicle_direction].state
    
    def get_stop_position(self, vehicle_direction):
        """Retourne la position d'arrêt pour une direction."""
        return self.stop_positions[vehicle_direction]
    
    def get_phase_info(self):
        """Retourne les infos de phase pour l'affichage."""
        return f"PHASE {self.current_phase}"
    
    @property
    def state(self):
        """Compatibilité avec l'ancien système de logging."""
        return self.get_phase_info().replace(" ", "_")
    
    @property
    def x(self):
        """Compatibilité avec l'ancien système."""
        return 0
