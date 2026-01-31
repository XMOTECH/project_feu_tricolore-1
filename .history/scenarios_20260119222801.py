from abc import ABC, abstractmethod

class ScenarioStrategy(ABC):
    """Interface commune pour tous les scénarios."""
    def __init__(self):
        self.name = "Inconnu"

    @abstractmethod
    def update_light(self, traffic_light):
        """Définit comment le feu évolue à chaque frame."""
        pass

class NormalScenario(ScenarioStrategy):
    def __init__(self):
        self.name = "Normal"
        # Durées en frames (approx 2 sec vert, 1 sec orange, 2 sec rouge)
        self.durations = {"VERT": 100, "ORANGE": 40, "ROUGE": 100}

    def update_light(self, light):
        light.timer += 1
        limit = self.durations.get(light.state, 100)
        
        # Cycle standard : Vert -> Orange -> Rouge -> Vert
        if light.timer >= limit:
            light.timer = 0
            if light.state == "VERT": light.state = "ORANGE"
            elif light.state == "ORANGE": light.state = "ROUGE"
            elif light.state == "ROUGE": light.state = "VERT"
            light.update_visuals()

class RushHourScenario(ScenarioStrategy):
    def __init__(self):
        self.name = "Heure de Pointe"
        # Vert très long (4s), Rouge court (1s) pour fluidifier
        self.durations = {"VERT": 200, "ORANGE": 30, "ROUGE": 50}

    def update_light(self, light):
        # Même logique que Normal, mais avec des durées différentes
        light.timer += 1
        limit = self.durations.get(light.state, 100)
        
        if light.timer >= limit:
            light.timer = 0
            if light.state == "VERT": light.state = "ORANGE"
            elif light.state == "ORANGE": light.state = "ROUGE"
            elif light.state == "ROUGE": light.state = "VERT"
            light.update_visuals()

class NightScenario(ScenarioStrategy):
    def __init__(self):
        self.name = "Mode Nuit"

    def update_light(self, light):
        # Logique Spéciale : Clignotement Orange
        light.timer += 1
        
        # Si le feu est sur Rouge ou Vert, on force l'Orange tout de suite
        if light.state not in ["ORANGE", "ETEINT"]:
            light.state = "ORANGE"
            light.timer = 0
        
        # Clignotement tous les 30 frames
        if light.timer >= 30:
            light.timer = 0
            if light.state == "ORANGE":
                light.state = "ETEINT"
            else:
                light.state = "ORANGE"
            light.update_visuals()

class ManualScenario(ScenarioStrategy):
    def __init__(self):
        self.name = "Manuel"

    def update_light(self, light):
        # Le feu ne change JAMAIS seul.
        # Il attend une action utilisateur (gérée dans main.py)
        pass