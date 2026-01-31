from abc import ABC, abstractmethod

class ScenarioStrategy(ABC):
    """Interface commune pour tous les scénarios."""
    def __init__(self):
        self.name = "Inconnu"

    @abstractmethod
    def update_intersection(self, intersection):
        """Définit comment l'intersection évolue à chaque frame."""
        pass
    
    # Compatibilité avec l'ancien système (un seul feu)
    def update_light(self, traffic_light):
        """Fallback pour compatibilité."""
        pass

class NormalScenario(ScenarioStrategy):
    def __init__(self):
        self.name = "Normal"

    def update_intersection(self, intersection):
        """Cycle standard automatique."""
        intersection.standard_update()

    def update_light(self, light):
        """Compatibilité ancien système."""
        light.timer += 1
        limit = light.durations.get(light.state, 100)
        
        if light.timer >= limit:
            light.change_state()

class RushHourScenario(ScenarioStrategy):
    def __init__(self):
        self.name = "Heure de Pointe"
        # Phases plus longues pour fluidifier le trafic
        self.phase_durations = {
            "A": 200, "A_ORANGE": 30, "B": 200, "B_ORANGE": 30
        }

    def update_intersection(self, intersection):
        """Cycle optimisé pour trafic dense."""
        intersection.timer += 1
        limit = self.phase_durations.get(intersection.current_phase, 100)
        
        if intersection.timer >= limit:
            intersection.timer = 0
            intersection.phase_index = (intersection.phase_index + 1) % len(intersection.phase_sequence)
            intersection.current_phase = intersection.phase_sequence[intersection.phase_index]
            intersection._apply_phase()

    def update_light(self, light):
        light.timer += 1
        durations = {"VERT": 200, "ORANGE": 30, "ROUGE": 50}
        limit = durations.get(light.state, 100)
        
        if light.timer >= limit:
            light.change_state()

class NightScenario(ScenarioStrategy):
    def __init__(self):
        self.name = "Mode Nuit"

    def update_intersection(self, intersection):
        """Tous les feux clignotent orange."""
        intersection.night_mode_update()

    def update_light(self, light):
        light.timer += 1
        
        if light.state not in ["ORANGE", "ETEINT"]:
            light.set_state("ORANGE")
            light.timer = 0
        
        if light.timer >= 30:
            light.timer = 0
            new_state = "ETEINT" if light.state == "ORANGE" else "ORANGE"
            light.set_state(new_state)

class ManualScenario(ScenarioStrategy):
    def __init__(self):
        self.name = "Manuel"

    def update_intersection(self, intersection):
        """Pas de changement automatique. Attend action utilisateur."""
        pass

    def update_light(self, light):
        """Le feu ne change JAMAIS seul."""
        pass